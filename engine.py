"""Download engine. GUI independent; credentials and signed URLs stay in memory."""
from __future__ import annotations

import json
import re
import threading
import time
import zipfile
import zlib
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from http.cookies import SimpleCookie
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import httpx

OFFICIAL = "https://osu.ppy.sh"
MIRRORS = {"Nerinyan": "https://api.nerinyan.moe/d/{id}",
           "Mino (catboy.best)": "https://catboy.best/d/{id}",
           "Sayobot 小夜": "https://txy1.sayobot.cn/beatmaps/download/full/{id}"}
MAX_FILE = 2 * 1024**3
USER_AGENT = "OsuBatch/1.1 (personal desktop beatmap downloader)"


def parse_input(text: str) -> tuple[list[int], list[str]]:
    """Bare numbers are set IDs, never individual difficulty IDs."""
    ids, errors = [], []
    for token in re.split(r"[\s,，;；]+", text.strip()):
        if not token:
            continue
        if re.fullmatch(r"[0-9]+", token):
            value = int(token)
        else:
            try:
                url = urlsplit(token if "://" in token else "https://" + token)
            except ValueError:
                errors.append(token)
                continue
            match = re.fullmatch(r"/(?:beatmapsets|s)/(\d+)(?:/download)?/?", url.path)
            if url.scheme not in ("http", "https") or url.hostname != "osu.ppy.sh" or not match:
                errors.append(token)
                continue
            value = int(match[1])
        if 0 < value < 2**31:
            if value not in ids:
                ids.append(value)
        else:
            errors.append(token)
    return ids, errors


def clean_cookie(raw: str) -> str:
    raw = raw.strip()
    if not raw:
        return ""
    if any(c in raw for c in "\r\n"):
        raise ValueError("Cookie 必须为单行内容。")
    if raw.lower().startswith("cookie:"):
        raw = raw[7:].strip()
    if "=" not in raw or (";" not in raw and " " not in raw and not raw.startswith("osu_session=")):
        raw = "osu_session=" + raw
    jar = SimpleCookie()
    try:
        jar.load(raw)
    except Exception:
        raise ValueError("Cookie 格式无效。") from None
    if not jar or "osu_session" not in jar:
        raise ValueError("未找到 osu_session，请粘贴官网请求的 Cookie，或单独粘贴 osu_session 值。")
    return "; ".join(f"{k}={v.coded_value}" for k, v in jar.items())


class DownloadError(Exception):
    def __init__(self, message: str, retryable=False, fallback=True, delay=None):
        super().__init__(message)
        self.retryable, self.fallback, self.delay = retryable, fallback, delay


class Stopped(Exception):
    pass


def check_stop(stop):
    if stop.is_set():
        raise Stopped()


def wait_stop(stop, seconds):
    if stop.wait(max(0, seconds)):
        raise Stopped()


def retry_delay(value, default=30):
    try:
        return max(0, float(value))
    except (ValueError, TypeError):
        try:
            return max(0, (parsedate_to_datetime(value) - datetime.now(timezone.utc)).total_seconds())
        except (ValueError, TypeError, OverflowError):
            return default


class RateGate:
    """Shared per-source spacing and cooldown across all workers."""
    def __init__(self, interval=1.5):
        self.lock = threading.Lock()
        self.next = {}
        self.interval = interval

    def wait(self, source, stop):
        while True:
            check_stop(stop)
            with self.lock:
                delay = self.next.get(source, 0) - time.monotonic()
                if delay <= 0:
                    self.next[source] = time.monotonic() + self.interval
                    return
            wait_stop(stop, min(delay, .25))

    def cooldown(self, source, seconds):
        with self.lock:
            self.next[source] = max(self.next.get(source, 0), time.monotonic() + seconds)


@dataclass(frozen=True)
class Options:
    directory: Path
    mode: str = "official"
    mirror: str = "Sayobot 小夜"
    no_video: bool = False
    cookie: str = ""


def source_url(source, sid, no_video):
    if source == "官方":
        return f"{OFFICIAL}/beatmapsets/{sid}/download" + ("?noVideo=1" if no_video else "")
    url = MIRRORS[source].format(id=sid)
    if source == "Sayobot 小夜":
        return url.replace("/full/", "/novideo/") if no_video else url
    # No-video support is enabled only for verified adapters.
    if no_video:
        if source != "Nerinyan":
            raise DownloadError("此镜像尚未提供经过验证的无视频模式。", fallback=False)
        url += "?nv=1"
    return url


def validate_osz(path: Path, sid: int, stop=None):
    """Read every member to verify CRC without extracting untrusted paths."""
    try:
        with zipfile.ZipFile(path) as z:
            infos = z.infolist()
            maps = [i for i in infos if i.filename.lower().endswith(".osu") and not i.is_dir()]
            if not maps or len(infos) > 20000 or sum(i.file_size for i in infos) > 4 * 1024**3:
                raise DownloadError("文件不是有效谱面包，或超出安全大小限制。", retryable=True)
            for info in infos:
                if info.is_dir():
                    continue
                is_map = info in maps
                prefix = bytearray()
                with z.open(info) as stream:
                    while chunk := stream.read(128 * 1024):
                        if stop is not None:
                            check_stop(stop)
                        if is_map and len(prefix) < 2 * 1024**2:
                            prefix.extend(chunk[:2 * 1024**2 - len(prefix)])
                if is_map:
                    content = prefix.decode("utf-8-sig", errors="replace")
                    if not content.lstrip().startswith("osu file format v"):
                        raise DownloadError("谱面包包含无效 .osu 文件。", retryable=True)
                    found = re.search(r"(?m)^BeatmapSetID\s*:\s*(-?\d+)\s*$", content)
                    if found and int(found[1]) > 0 and int(found[1]) != sid:
                        raise DownloadError("下载内容的谱面集 ID 不匹配。", retryable=True)
    except (zipfile.BadZipFile, RuntimeError, EOFError, NotImplementedError, zlib.error):
        raise DownloadError("谱面压缩包损坏或格式不受支持。", retryable=True) from None


class Downloader:
    def __init__(self, gate=None, transport=None):
        self.gate = gate or RateGate()
        self.transport = transport
        self.blocked = {}
        self.lock = threading.Lock()

    def clear_blocks(self):
        with self.lock:
            self.blocked.clear()

    def download(self, sid, options, stop, emit):
        folder = options.directory.expanduser().resolve()
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / f"{sid}{'-novideo' if options.no_video else ''}.osz"
        if target.exists():
            try:
                validate_osz(target, sid, stop)
            except DownloadError:
                raise DownloadError("同名文件已存在但校验失败，请移走该文件后重试；未覆盖原文件。", fallback=False) from None
            emit("本地", target.stat().st_size, target.stat().st_size, 0, "已校验，跳过重复文件")
            return str(target), "本地"
        sources = ["官方"] if options.mode == "official" else [options.mirror]
        if options.mode == "fallback":
            sources = ["官方", options.mirror]
        failures = []
        for source in sources:
            check_stop(stop)
            emit(source, 0, 0, 0, "正在准备下载")
            try:
                with self.lock:
                    blocked = self.blocked.get(source)
                if blocked:
                    raise DownloadError(blocked)
                if source == "官方" and not options.cookie:
                    raise DownloadError("请先设置官网登录会话。")
                self._source(sid, source, options, target, stop, emit)
                return str(target), source
            except DownloadError as exc:
                failures.append(f"{source}：{exc}")
                if not exc.fallback:
                    raise DownloadError("；".join(failures), fallback=False) from None
        raise DownloadError("；".join(failures))

    def _source(self, sid, source, options, target, stop, emit):
        url = source_url(source, sid, options.no_video)
        key = {"官方": "official", "Nerinyan": "nerinyan", "Mino (catboy.best)": "mino", "Sayobot 小夜": "sayobot"}[source]
        partial = target.with_suffix(f".{key}.part")
        meta = partial.with_suffix(partial.suffix + ".json")
        identity = {"id": sid, "source": source, "no_video": options.no_video}
        for attempt in range(3):
            check_stop(stop)
            try:
                self.gate.wait(source, stop)
                with httpx.Client(timeout=httpx.Timeout(20, connect=15), transport=self.transport,
                                  follow_redirects=False, trust_env=True) as client:
                    self._transfer(client, url, source, options.cookie, sid, identity,
                                   partial, meta, target, stop, emit)
                return
            except httpx.HTTPError:
                # Exception URLs may contain download signatures. Never surface raw exceptions.
                exc = DownloadError("网络连接失败、超时或响应不完整。", retryable=True)
            except DownloadError as error:
                exc = error
            if not exc.retryable or attempt == 2:
                raise exc
            delay = exc.delay if exc.delay is not None else 2 ** (attempt + 1)
            self.gate.cooldown(source, delay)
            emit(source, 0, 0, 0, f"{exc} 等待 {delay:.0f} 秒后重试 ({attempt + 1}/2)")
            wait_stop(stop, delay)

    def _response(self, client, url, source, cookie, sid, headers):
        for _ in range(10):
            parsed = urlsplit(url)
            if parsed.scheme != "https" or parsed.username or parsed.password:
                raise DownloadError("下载源返回了不安全的跳转地址。", fallback=False)
            request_headers = {"User-Agent": USER_AGENT, "Accept-Encoding": "identity", **headers}
            # Use a fresh per-request Cookie header ONLY for the exact official origin.
            # Clear the client cookie jar so Set-Cookie cannot broaden its scope.
            client.cookies.clear()
            if source == "官方" and parsed.hostname == "osu.ppy.sh" and parsed.port in (None, 443):
                request_headers["Cookie"] = cookie
                request_headers["Referer"] = f"{OFFICIAL}/beatmapsets/{sid}"
            response = client.send(client.build_request("GET", url, headers=request_headers), stream=True)
            if response.status_code in (301, 302, 303, 307, 308):
                location = response.headers.get("location")
                response.close()
                if not location:
                    raise DownloadError("下载源的跳转地址为空。")
                url = urljoin(url, location)
                continue
            return response
        raise DownloadError("下载跳转次数过多，请检查登录状态。")

    def _transfer(self, client, url, source, cookie, sid, identity, partial, meta, target, stop, emit):
        saved = {}
        if meta.exists():
            try:
                saved = json.loads(meta.read_text(encoding="utf-8"))
                if not isinstance(saved, dict):
                    saved = {}
            except (ValueError, OSError):
                pass
        offset = partial.stat().st_size if partial.exists() else 0
        if any(saved.get(k) != v for k, v in identity.items()) or not saved.get("validator"):
            offset = 0
        headers = {"Range": f"bytes={offset}-", "If-Range": saved["validator"]} if offset else {}
        response = self._response(client, url, source, cookie, sid, headers)
        try:
            status = response.status_code
            if status in (401, 403):
                message = "登录失效或访问被拒绝，请重新登录官网；也可能需要在浏览器完成验证。" if source == "官方" else "镜像拒绝访问，请稍后重试或更换下载源。"
                with self.lock:
                    self.blocked[source] = message
                raise DownloadError(message)
            if status == 429:
                delay = retry_delay(response.headers.get("Retry-After"))
                self.gate.cooldown(source, delay)
                raise DownloadError("下载源限流。", retryable=True, fallback=False, delay=delay)
            if status == 404:
                raise DownloadError("谱面不存在、已被移除，或此来源不提供下载。")
            if status == 416:
                meta.unlink(missing_ok=True)
                raise DownloadError("服务器无法续传，将重新下载。", retryable=True)
            if status not in (200, 206):
                raise DownloadError(f"下载源返回 HTTP {status}。", retryable=status >= 500)
            if "text/html" in response.headers.get("content-type", "").lower() or "json" in response.headers.get("content-type", "").lower():
                raise DownloadError("下载源返回网页或错误信息，请检查登录与浏览器验证。")
            if response.headers.get("content-encoding", "identity") not in ("identity", ""):
                raise DownloadError("下载源返回不支持的压缩传输格式。")
            etag = response.headers.get("etag", "")
            validator = etag if etag and not etag.startswith("W/") else response.headers.get("last-modified", "")
            length = response.headers.get("content-length", "")
            length = int(length) if length.isdigit() else 0
            if status == 206:
                match = re.fullmatch(r"bytes (\d+)-(\d+)/(\d+)", response.headers.get("content-range", ""))
                if not offset or not match or int(match[1]) != offset or int(match[2]) != int(match[3]) - 1 or (validator and validator != saved.get("validator")):
                    meta.unlink(missing_ok=True)
                    raise DownloadError("续传响应不一致，将重新下载。", retryable=True)
                total = int(match[3])
                if length and length != total - offset:
                    meta.unlink(missing_ok=True)
                    raise DownloadError("续传长度不一致，将重新下载。", retryable=True)
            else:
                offset, total = 0, length
            if total > MAX_FILE:
                raise DownloadError("谱面包超过 2 GiB 限制。", fallback=False)
            # Truncate before saving a new validator; interruption must never pair old bytes with new metadata.
            with partial.open("ab" if offset else "wb") as out:
                meta.write_text(json.dumps({**identity, "validator": validator}, ensure_ascii=False), encoding="utf-8")
                done, started, last = offset, time.monotonic(), 0
                for chunk in response.iter_bytes(128 * 1024):
                    check_stop(stop)
                    done += len(chunk)
                    if done > MAX_FILE or (total and done > total):
                        meta.unlink(missing_ok=True)
                        raise DownloadError("下载内容超出预期大小。", retryable=True)
                    out.write(chunk)
                    now = time.monotonic()
                    if now - last > .2:
                        emit(source, done, total, (done - offset) / max(.001, now - started), "下载中")
                        last = now
            check_stop(stop)
            if total and done != total:
                raise DownloadError("文件未下载完整。", retryable=True)
        finally:
            response.close()
        emit(source, done, done, 0, "校验压缩包与谱面 ID")
        try:
            validate_osz(partial, sid, stop)
        except DownloadError:
            meta.unlink(missing_ok=True)
            raise
        check_stop(stop)
        if target.exists():
            raise DownloadError("目标文件在下载期间已被创建，未覆盖；请重试。", fallback=False)
        partial.rename(target)
        meta.unlink(missing_ok=True)
        emit(source, done, done, 0, "下载完成")

