import io
import json
import threading
import zipfile
from pathlib import Path

import httpx
import pytest

import engine
from engine import Downloader, DownloadError, Options, RateGate, Stopped, parse_input, clean_cookie, validate_osz
from store import Store


def archive(sid=123):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr(zipfile.ZipInfo("test.osu"), f"osu file format v14\n[Metadata]\nBeatmapSetID:{sid}\n")
        z.writestr(zipfile.ZipInfo("audio.mp3"), b"test fixture, not real audio" * 100)
    return buf.getvalue()


def downloader(handler):
    return Downloader(RateGate(0), httpx.MockTransport(handler))


def run(d, folder, mode="mirror", cookie="", stop=None):
    return d.download(123, Options(folder, mode=mode, mirror="Nerinyan", cookie=cookie), stop or threading.Event(), lambda *args: None)


@pytest.fixture(autouse=True)
def fast_retries(monkeypatch):
    monkeypatch.setattr(engine, "wait_stop", lambda stop, seconds: engine.check_stop(stop))
    monkeypatch.setattr(RateGate, "cooldown", lambda *args: None)


def test_parse_and_deduplicate():
    ids, errors = parse_input("123\nhttps://osu.ppy.sh/beatmapsets/123#osu/999，https://osu.ppy.sh/s/456 0 https://evil.com/s/55 https://osu.ppy.sh/beatmaps/123")
    assert ids == [123, 456]
    assert len(errors) == 3


def test_cookie_input():
    assert clean_cookie("abc%3D") == "osu_session=abc%3D"
    assert clean_cookie("Cookie: osu_session=secret; cf_clearance=clear") == "osu_session=secret; cf_clearance=clear"
    with pytest.raises(ValueError):
        clean_cookie("osu_session=foo\r\nInjected: secret")


def test_download_and_local_dedup(tmp_path):
    calls = []
    def handler(req):
        calls.append(req)
        return httpx.Response(200, content=archive(), headers={"ETag": '"one"'})
    d = downloader(handler)
    path, source = run(d, tmp_path)
    assert Path(path).read_bytes() == archive()
    assert source == "Nerinyan"
    assert run(d, tmp_path)[1] == "本地"
    assert len(calls) == 1
    assert not list(tmp_path.glob("*.part*"))


def test_official_cookie_not_leaked_to_redirect(tmp_path):
    seen = []
    def handler(req):
        seen.append(req)
        if req.url.host == "osu.ppy.sh":
            return httpx.Response(302, headers={"location": "https://files.example.org/signed?secret=test", "set-cookie": "extra=secret; Domain=.example.org"})
        return httpx.Response(200, content=archive())
    run(downloader(handler), tmp_path, mode="official", cookie="osu_session=secret")
    assert seen[0].headers["cookie"] == "osu_session=secret"
    assert "cookie" not in seen[1].headers
    assert "referer" not in seen[1].headers
    assert "secret" not in "".join(p.read_text(errors="ignore") for p in tmp_path.glob("*.json"))


def test_fallback_is_opt_in_and_cookie_does_not_leak(tmp_path):
    seen = []
    def handler(req):
        seen.append(req)
        if req.url.host == "osu.ppy.sh":
            return httpx.Response(403)
        assert "cookie" not in req.headers
        return httpx.Response(200, content=archive())
    with pytest.raises(DownloadError):
        run(downloader(handler), tmp_path, mode="official", cookie="osu_session=x")
    assert len(seen) == 1
    path, source = run(downloader(handler), tmp_path, mode="fallback", cookie="osu_session=x")
    assert source == "Nerinyan"


def test_html_never_saved_as_osz(tmp_path):
    with pytest.raises(DownloadError, match="网页"):
        run(downloader(lambda req: httpx.Response(200, text="<html>Login</html>", headers={"Content-Type":"text/html"})), tmp_path)
    assert not list(tmp_path.glob("*.osz"))


def test_corrupt_zip_never_finalized(tmp_path):
    with pytest.raises(DownloadError):
        run(downloader(lambda req: httpx.Response(200, content=b"not a zip")), tmp_path)
    assert not list(tmp_path.glob("*.osz"))


def test_wrong_mapset_rejected(tmp_path):
    with pytest.raises(DownloadError, match="ID"):
        run(downloader(lambda req: httpx.Response(200, content=archive(999))), tmp_path)
    assert not list(tmp_path.glob("*.osz"))


def seed_partial(folder, body, validator='"one"'):
    partial = folder / "123.nerinyan.part"
    partial.write_bytes(body)
    partial.with_suffix(".part.json").write_text(json.dumps({"id":123,"source":"Nerinyan","no_video":False,"validator":validator}))


def test_resume_206(tmp_path):
    body = archive()
    seed_partial(tmp_path, body[:30])
    def handler(req):
        assert req.headers["range"] == "bytes=30-"
        assert req.headers["if-range"] == '"one"'
        return httpx.Response(206, content=body[30:], headers={"Content-Range":f"bytes 30-{len(body)-1}/{len(body)}", "ETag":'"one"'})
    path, _ = run(downloader(handler), tmp_path)
    assert Path(path).read_bytes() == body


def test_server_ignores_range_restart(tmp_path):
    seed_partial(tmp_path, b"old version")
    path, _ = run(downloader(lambda req: httpx.Response(200, content=archive(), headers={"ETag":'"two"'})), tmp_path)
    assert Path(path).read_bytes() == archive()


def test_bad_range_then_fresh_request(tmp_path):
    body = archive()
    seed_partial(tmp_path, body[:30])
    seen = []
    def handler(req):
        seen.append(req)
        if len(seen) == 1:
            return httpx.Response(206, content=body[31:], headers={"Content-Range":f"bytes 31-{len(body)-1}/{len(body)}"})
        assert "range" not in req.headers
        return httpx.Response(200, content=body)
    path, _ = run(downloader(handler), tmp_path)
    assert Path(path).read_bytes() == body
    assert len(seen) == 2


def test_416_restarts(tmp_path):
    seed_partial(tmp_path, archive()[:30])
    calls = []
    def handler(req):
        calls.append(req)
        return httpx.Response(416) if len(calls) == 1 else httpx.Response(200, content=archive())
    run(downloader(handler), tmp_path)
    assert "range" not in calls[1].headers


def test_partial_missing_validator_restarts(tmp_path):
    seed_partial(tmp_path, b"old", validator="")
    def handler(req):
        assert "range" not in req.headers
        return httpx.Response(200, content=archive())
    run(downloader(handler), tmp_path)


def test_429_retries_and_does_not_switch_source(tmp_path):
    calls = []
    def handler(req):
        calls.append(req)
        assert req.url.host == "osu.ppy.sh"
        return httpx.Response(429, headers={"Retry-After":"0"})
    with pytest.raises(DownloadError, match="限流"):
        run(downloader(handler), tmp_path, mode="fallback", cookie="osu_session=x")
    assert len(calls) == 3


def test_cancel_preserves_partial(tmp_path):
    stop = threading.Event()
    class InterruptStream(httpx.SyncByteStream):
        def __iter__(self):
            yield b"x" * (128 * 1024)
            stop.set()
            yield b"y" * (128 * 1024)
    d = downloader(lambda req: httpx.Response(200, stream=InterruptStream(), headers={"etag":'"one"'}))
    with pytest.raises(Stopped):
        run(d, tmp_path, stop=stop)
    assert (tmp_path / "123.nerinyan.part").stat().st_size == 128 * 1024
    assert not list(tmp_path.glob("*.osz"))


def test_existing_invalid_file_not_overwritten(tmp_path):
    target = tmp_path / "123.osz"
    target.write_bytes(b"user data")
    with pytest.raises(DownloadError, match="未覆盖"):
        run(downloader(lambda req: pytest.fail("must not download")), tmp_path)
    assert target.read_bytes() == b"user data"


def test_insecure_redirect_rejected(tmp_path):
    with pytest.raises(DownloadError, match="不安全"):
        run(downloader(lambda req: httpx.Response(302, headers={"location":"http://files.example.org/a"})), tmp_path)


def test_queue_recovers_and_secret_cannot_be_saved(tmp_path):
    store = Store(tmp_path)
    assert store.add([123, 123, 456]) == 2
    store.update(123, status="下载中")
    store.save_settings({"mode":"official"})
    with pytest.raises(AssertionError):
        store.save_settings({"cookie":"secret"})
    store.close()
    store = Store(tmp_path)
    assert store.rows()[0]["status"] == "已暂停"
    assert store.settings() == {"mode":"official"}
    store.close()


def test_network_exception_redacted(tmp_path):
    def handler(req):
        raise httpx.ConnectError("https://secret.example?token=TOPSECRET")
    with pytest.raises(DownloadError) as exc:
        run(downloader(handler), tmp_path)
    assert "TOPSECRET" not in str(exc.value)


def test_sayobot_adapter_and_video_variant(tmp_path):
    requests = []
    def handler(req):
        requests.append(req)
        return httpx.Response(200, content=archive())
    d = downloader(handler)
    path, source = d.download(123, Options(tmp_path, mode="mirror", mirror="Sayobot 小夜", no_video=True), threading.Event(), lambda *args: None)
    assert requests[0].url.path == "/beatmaps/download/novideo/123"
    assert Path(path).name == "123-novideo.osz"
    assert source == "Sayobot 小夜"

