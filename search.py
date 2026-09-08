"""Paginated metadata search; never downloads a beatmap or silently changes source."""
from dataclasses import dataclass, field
from datetime import date
import math
import threading
import unicodedata

import httpx

from engine import USER_AGENT, DownloadError, Stopped, RateGate, check_stop, retry_delay, wait_stop

STATUSES = {
    '缺省': 'any',
    'Ranked': 'ranked',
    'Approved': 'approved',
    'Qualified': 'qualified',
    'Loved': 'loved',
    'Pending': 'pending',
    'WIP': 'wip',
    'Graveyard': 'graveyard',
}
GAME_MODES = {
    '缺省': None,
    'osu! standard (std)': 0,
    'osu!taiko': 1,
    'osu!catch': 2,
    'osu!mania': 3,
}
GENRES = {
    '缺省': None,
    '未指定': 1,
    '电子游戏': 2,
    '动漫': 3,
    '摇滚': 4,
    '流行': 5,
    '其他': 6,
    '新奇 / Novelty': 7,
    '嘻哈': 9,
    '电子': 10,
    '金属': 11,
    '古典': 12,
    '民谣': 13,
    '爵士': 14,
}
LANGUAGES = {
    '缺省': None,
    '未指定': 1,
    '英语': 2,
    '日语': 3,
    '中文': 4,
    '纯音乐': 5,
    '韩语': 6,
    '法语': 7,
    '德语': 8,
    '瑞典语': 9,
    '西班牙语': 10,
    '意大利语': 11,
    '俄语': 12,
    '波兰语': 13,
    '其他语言': 14,
}
SORT_FIELDS = {
    '缺省': 'default',
    '标题': 'title',
    '标题（罗马化）': 'title_romanized',
    '艺术家': 'artist',
    '艺术家（罗马化）': 'artist_romanized',
    '来源': 'source',
    '流派': 'genre',
    '语言': 'language',
    'BPM': 'bpm',
    '长度': 'length',
    '谱面作者': 'creator',
    '谱面模式': 'mode',
    '谱面难度': 'difficulty',
    '谱面状态': 'status',
    '提交日期': 'submitted',
    '更新日期': 'updated',
    '状态改变日期': 'status_changed',
}
SORT_DIRECTIONS = {'升序': False, '降序': True}
MODE_NAMES = {0: 'std', 1: 'taiko', 2: 'catch', 3: 'mania'}
STATUS_NUMBERS = {-2: 'graveyard', -1: 'wip', 0: 'pending', 1: 'ranked', 2: 'approved', 3: 'qualified', 4: 'loved'}
SAYO_CLASSES = {'ranked': 1, 'approved': 1, 'qualified': 2, 'loved': 4, 'pending': 8, 'wip': 8, 'graveyard': 16, 'any': 31}
GENRE_NAMES = {value: key for key, value in GENRES.items() if value is not None}
LANGUAGE_NAMES = {value: key for key, value in LANGUAGES.items() if value is not None}
STATUS_ORDER = {'ranked': 0, 'approved': 1, 'qualified': 2, 'loved': 3, 'pending': 4, 'wip': 5, 'graveyard': 6}


def normalized(value):
    return unicodedata.normalize('NFKC', str(value or '')).strip().casefold()


def _query_number(value):
    value = float(value)
    return str(int(value)) if value.is_integer() else f'{value:g}'


def _iso_date(value):
    if not value:
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _metadata_id(value):
    if isinstance(value, dict):
        value = value.get('id')
    if value in (None, ''):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _metadata_name(value, names):
    if isinstance(value, dict):
        label = value.get('name')
        if label:
            return str(label)
        value = value.get('id')
    try:
        return names.get(int(value), '') if value not in (None, '') else ''
    except (TypeError, ValueError):
        return str(value or '')


@dataclass(frozen=True)
class Filters:
    # Empty / None / 'any' means the condition is not applied.
    # `title` / `artist` match either the romanised or Unicode metadata form.
    # The *_romanized fields constrain the official romanised metadata explicitly.
    title: str = ''
    title_romanized: str = ''
    artist: str = ''
    artist_romanized: str = ''
    source_text: str = ''
    genre: int | None = None
    language: int | None = None
    bpm_min: float | None = None
    bpm_max: float | None = None
    length_min: int | None = None
    length_max: int | None = None
    creator: str = ''
    mode: int | None = None
    difficulty_min: float | None = None
    difficulty_max: float | None = None
    status: str = 'any'
    submitted_from: str | date | None = None
    submitted_to: str | date | None = None
    updated_from: str | date | None = None
    updated_to: str | date | None = None
    status_changed_from: str | date | None = None
    status_changed_to: str | date | None = None
    exact_artist: bool = True

    def validate(self, source=None):
        if self.status not in STATUSES.values() or self.mode not in (None, 0, 1, 2, 3):
            raise DownloadError('筛选参数无效。')
        if self.genre not in set(GENRES.values()) or self.language not in set(LANGUAGES.values()):
            raise DownloadError('流派或语言筛选无效。')

        for label, value in (
            ('标题', self.title), ('罗马化标题', self.title_romanized),
            ('艺术家', self.artist), ('罗马化艺术家', self.artist_romanized),
            ('来源', self.source_text), ('谱面作者', self.creator),
        ):
            if len(value) > 200 or any(c in value for c in '\r\n"\\'):
                raise DownloadError(f'{label}最长 200 字符，不能包含换行、双引号或反斜杠。')

        ranges = (
            ('BPM', self.bpm_min, self.bpm_max, 0, 1000),
            ('长度', self.length_min, self.length_max, 0, 24 * 60 * 60),
            ('谱面难度', self.difficulty_min, self.difficulty_max, 0, 100),
        )
        for label, lower, upper, minimum, maximum in ranges:
            for value in (lower, upper):
                if value is not None and (not isinstance(value, (int, float)) or not math.isfinite(value) or value < minimum or value > maximum):
                    raise DownloadError(f'{label}筛选值无效。')
            if lower is not None and upper is not None and lower > upper:
                raise DownloadError(f'{label}最小值不能大于最大值。')

        for label, lower, upper in (
            ('提交日期', self.submitted_from, self.submitted_to),
            ('更新日期', self.updated_from, self.updated_to),
            ('状态改变日期', self.status_changed_from, self.status_changed_to),
        ):
            start = _iso_date(lower)
            end = _iso_date(upper)
            if (lower and start is None) or (upper and end is None):
                raise DownloadError(f'{label}格式无效，请使用 YYYY-MM-DD。')
            if start and end and start > end:
                raise DownloadError(f'{label}的起始日期不能晚于结束日期。')

        if source == 'sayobot' and self.sayobot_unsupported_fields():
            names = '、'.join(self.sayobot_unsupported_fields())
            raise DownloadError(f'Sayobot 当前返回的元数据不足以可靠执行：{names}。请改用 osu! 官方搜索。')

    def sayobot_unsupported_fields(self):
        unsupported = []
        if self.source_text:
            unsupported.append('来源')
        if self.genre is not None:
            unsupported.append('流派')
        if self.language is not None:
            unsupported.append('语言')
        if self.bpm_min is not None or self.bpm_max is not None:
            unsupported.append('BPM')
        if self.length_min is not None or self.length_max is not None:
            unsupported.append('长度')
        if self.difficulty_min is not None or self.difficulty_max is not None:
            unsupported.append('谱面难度')
        if self.submitted_from or self.submitted_to:
            unsupported.append('提交日期')
        if self.updated_from or self.updated_to:
            unsupported.append('更新日期')
        if self.status_changed_from or self.status_changed_to:
            unsupported.append('状态改变日期')
        return unsupported

    @staticmethod
    def _append_date_query(query, name, lower, upper):
        start = _iso_date(lower)
        end = _iso_date(upper)
        if start:
            query.append(f'{name}>={start.isoformat()}')
        if end:
            query.append(f'{name}<={end.isoformat()}')

    def official_params(self):
        self.validate('official')
        query = []

        # Generic title/artist fields are intentionally broad and verified locally against
        # both romanised and Unicode metadata. Dedicated romanised fields use osu!web's
        # structured artist/title filters.
        for value in (self.title, self.artist):
            if value.strip():
                query.append(f'"{value.strip()}"')
        if self.title_romanized.strip():
            query.append(f'title="{self.title_romanized.strip()}"')
        if self.artist_romanized.strip():
            query.append(f'artist="{self.artist_romanized.strip()}"')
        for value in (self.source_text, self.creator):
            if value.strip():
                query.append(f'"{value.strip()}"')

        for name, lower, upper in (
            ('bpm', self.bpm_min, self.bpm_max),
            ('length', self.length_min, self.length_max),
            ('stars', self.difficulty_min, self.difficulty_max),
        ):
            if lower is not None:
                query.append(f'{name}>={_query_number(lower)}')
            if upper is not None:
                query.append(f'{name}<={_query_number(upper)}')

        self._append_date_query(query, 'submitted', self.submitted_from, self.submitted_to)
        self._append_date_query(query, 'updated', self.updated_from, self.updated_to)
        self._append_date_query(query, 'ranked', self.status_changed_from, self.status_changed_to)

        status = self.status
        if status == 'approved':
            query.append('status=approved')
            status = 'any'

        params = {'q': ' '.join(query), 's': status, 'sort': 'ranked_asc', 'nsfw': 'true'}
        if self.mode is not None:
            params['m'] = str(self.mode)
        if self.genre is not None:
            params['g'] = str(self.genre)
        if self.language is not None:
            params['l'] = str(self.language)
        return params

    def sayobot_params(self, offset):
        self.validate('sayobot')
        # Sayobot has one broad keyword field. Use one supported text condition to narrow
        # the result and verify all supported conditions locally afterwards.
        keyword = next((v.strip() for v in (
            self.artist_romanized, self.title_romanized, self.artist, self.title, self.creator
        ) if v.strip()), '')
        return {
            'cmd': 'beatmaplist', 'type': 'search', 'keyword': keyword,
            'subtype': 2, 'class': SAYO_CLASSES[self.status],
            'mode': 15 if self.mode is None else 1 << self.mode,
            'limit': 50, 'offset': offset,
        }

    def matching_beatmaps(self, row):
        matches = []
        for beatmap in row.get('beatmaps', []):
            if self.mode is not None and beatmap.get('mode') != self.mode:
                continue
            if not self._number_match(beatmap.get('bpm'), self.bpm_min, self.bpm_max):
                continue
            if not self._number_match(beatmap.get('length'), self.length_min, self.length_max):
                continue
            if not self._number_match(beatmap.get('stars'), self.difficulty_min, self.difficulty_max):
                continue
            matches.append(beatmap)
        return matches

    @staticmethod
    def _number_match(value, lower, upper):
        if lower is None and upper is None:
            return True
        if value is None:
            return False
        try:
            value = float(value)
        except (TypeError, ValueError):
            return False
        return (lower is None or value >= lower) and (upper is None or value <= upper)

    @staticmethod
    def _date_match(value, lower, upper):
        if not lower and not upper:
            return True
        actual = _iso_date(value)
        if actual is None:
            return False
        start = _iso_date(lower)
        end = _iso_date(upper)
        return (start is None or actual >= start) and (end is None or actual <= end)

    def matches(self, row):
        if self.title:
            needle = normalized(self.title)
            if not any(needle in normalized(value) for value in (row.get('title'), row.get('title_unicode'))):
                return False
        if self.title_romanized and normalized(self.title_romanized) not in normalized(row.get('title')):
            return False

        if self.artist:
            artist = normalized(self.artist)
            names = [normalized(row.get('artist')), normalized(row.get('artist_unicode'))]
            if self.exact_artist:
                if artist not in names:
                    return False
            elif not any(artist in name for name in names):
                return False
        if self.artist_romanized:
            artist = normalized(self.artist_romanized)
            value = normalized(row.get('artist'))
            if (self.exact_artist and artist != value) or (not self.exact_artist and artist not in value):
                return False

        if self.source_text and normalized(self.source_text) not in normalized(row.get('source')):
            return False
        if self.creator and normalized(self.creator) not in normalized(row.get('creator')):
            return False
        if self.status != 'any' and row.get('status') != self.status:
            return False

        # The website search endpoint applies genre/language via g/l. If the returned
        # record contains the metadata too, verify it; otherwise the server-side filter
        # remains authoritative instead of rejecting a valid row due to a missing field.
        if self.genre is not None and row.get('genre_id') is not None and row.get('genre_id') != self.genre:
            return False
        if self.language is not None and row.get('language_id') is not None and row.get('language_id') != self.language:
            return False

        if not self._date_match(row.get('submitted_date'), self.submitted_from, self.submitted_to):
            return False
        if not self._date_match(row.get('last_updated'), self.updated_from, self.updated_to):
            return False
        if not self._date_match(row.get('status_changed_date'), self.status_changed_from, self.status_changed_to):
            return False

        # Mode, BPM, length and star rating must be satisfied by the same difficulty.
        difficulty_filter = (
            self.mode is not None or self.bpm_min is not None or self.bpm_max is not None or
            self.length_min is not None or self.length_max is not None or
            self.difficulty_min is not None or self.difficulty_max is not None
        )
        matched = self.matching_beatmaps(row)
        return bool(matched) if difficulty_filter else True


@dataclass(frozen=True)
class SortSpec:
    field: str = 'default'
    descending: bool = False

    def validate(self, source=None):
        if self.field not in SORT_FIELDS.values():
            raise DownloadError('排序字段无效。')
        if source == 'sayobot' and self.field in {'source', 'genre', 'language', 'bpm', 'length', 'difficulty', 'submitted', 'updated', 'status_changed'}:
            raise DownloadError('Sayobot 当前元数据不足以可靠按该字段排序；请改用 osu! 官方搜索或选择缺省排序。')


@dataclass
class SearchResult:
    rows: list = field(default_factory=list)
    complete: bool = False
    message: str = ''
    pages: int = 0
    scanned: int = 0


def normalize_record(raw, source):
    if not isinstance(raw, dict):
        raise DownloadError('搜索结果记录格式异常。')
    try:
        if source == 'official':
            sid, status = int(raw['id']), str(raw['status'])
            maps = raw['beatmaps']
            beatmaps = []
            fallback_bpm = raw.get('bpm')
            for beatmap in maps:
                if beatmap.get('convert', False) or beatmap.get('deleted_at'):
                    continue
                mode = beatmap.get('mode_int', {'osu': 0, 'taiko': 1, 'fruits': 2, 'mania': 3}.get(beatmap.get('mode')))
                if mode not in MODE_NAMES:
                    continue
                bpm = beatmap.get('bpm', fallback_bpm)
                length = beatmap.get('total_length', beatmap.get('hit_length'))
                stars = beatmap.get('difficulty_rating')
                beatmaps.append({
                    'mode': mode,
                    'version': str(beatmap.get('version', '')),
                    'bpm': float(bpm) if bpm is not None else None,
                    'length': int(length) if length is not None else None,
                    'stars': float(stars) if stars is not None else None,
                })
            artist_unicode = raw.get('artist_unicode', '')
            title_unicode = raw.get('title_unicode', '')
            genre_raw = raw.get('genre', raw.get('genre_id'))
            language_raw = raw.get('language', raw.get('language_id'))
            genre_id = _metadata_id(genre_raw)
            language_id = _metadata_id(language_raw)
            genre = _metadata_name(genre_raw, GENRE_NAMES)
            language = _metadata_name(language_raw, LANGUAGE_NAMES)
            source_text = str(raw.get('source', '') or '')
            submitted_date = str(raw.get('submitted_date', '') or '')
            last_updated = str(raw.get('last_updated', '') or '')
            # osu!web exposes ranked_date for the ranked/approved status transition.
            # It is the only reliable beatmapset-level status-change timestamp returned
            # by the endpoint; statuses without it remain blank rather than being guessed.
            status_changed_date = str(raw.get('ranked_date', '') or '')
        else:
            sid = int(raw['sid'])
            status = STATUS_NUMBERS[int(raw['approved'])]
            mask = int(raw['modes'])
            modes = [mode for mode in MODE_NAMES if mask & (1 << mode)]
            beatmaps = [{'mode': mode, 'version': '', 'bpm': None, 'length': None, 'stars': None} for mode in modes]
            artist_unicode = raw.get('artistU', raw.get('artist_unicode', ''))
            title_unicode = raw.get('titleU', raw.get('title_unicode', ''))
            genre_id = language_id = None
            genre = language = source_text = submitted_date = last_updated = status_changed_date = ''

        modes = sorted({beatmap['mode'] for beatmap in beatmaps})
        if not 0 < sid < 2**31 or status not in STATUS_NUMBERS.values() or not modes:
            raise ValueError()
        return {
            'sid': sid,
            # osu!web `artist`/`title` are the romanised forms; *_unicode preserves
            # native-script metadata when present.
            'artist': str(raw['artist']),
            'artist_unicode': str(artist_unicode or ''),
            'title': str(raw.get('title', '')),
            'title_unicode': str(title_unicode or ''),
            'source': source_text,
            'genre_id': genre_id,
            'genre': genre,
            'language_id': language_id,
            'language': language,
            'creator': str(raw.get('creator', '')),
            'status': status,
            'submitted_date': submitted_date,
            'last_updated': last_updated,
            'status_changed_date': status_changed_date,
            'modes': modes,
            'beatmaps': beatmaps,
        }
    except (KeyError, TypeError, ValueError, AttributeError, OverflowError):
        raise DownloadError('搜索结果缺少可靠的谱面 ID、状态或模式信息；已停止，避免误筛选。') from None


def _difficulty_values(row, field):
    beatmaps = row.get('matched_beatmaps') or row.get('beatmaps') or []
    values = [beatmap.get(field) for beatmap in beatmaps if beatmap.get(field) is not None]
    return values


def _sort_value(row, field):
    if field == 'title':
        value = normalized(row.get('title_unicode') or row.get('title'))
        return value or None
    if field == 'title_romanized':
        value = normalized(row.get('title'))
        return value or None
    if field == 'artist':
        value = normalized(row.get('artist_unicode') or row.get('artist'))
        return value or None
    if field == 'artist_romanized':
        value = normalized(row.get('artist'))
        return value or None
    if field in {'source', 'genre', 'language', 'creator'}:
        value = normalized(row.get(field, ''))
        return value or None
    if field == 'status':
        return STATUS_ORDER.get(row.get('status'), 99)
    if field == 'submitted':
        return _iso_date(row.get('submitted_date'))
    if field == 'updated':
        return _iso_date(row.get('last_updated'))
    if field == 'status_changed':
        return _iso_date(row.get('status_changed_date'))
    if field == 'mode':
        values = _difficulty_values(row, 'mode') or row.get('modes', [])
        return min(values) if values else None
    if field == 'bpm':
        values = _difficulty_values(row, 'bpm')
        return min(values) if values else None
    if field == 'length':
        values = _difficulty_values(row, 'length')
        return min(values) if values else None
    if field == 'difficulty':
        values = _difficulty_values(row, 'stars')
        return min(values) if values else None
    return None


def sort_rows(rows, spec):
    spec = spec or SortSpec()
    spec.validate()
    rows = list(rows)
    if spec.field == 'default':
        return rows
    present, missing = [], []
    for row in rows:
        value = _sort_value(row, spec.field)
        (present if value is not None else missing).append((value, row))
    present.sort(key=lambda item: item[0], reverse=spec.descending)
    return [row for _, row in present] + [row for row in missing]


class Searcher:
    def __init__(self, transport=None, interval=1):
        self.transport = transport
        self.gate = RateGate(interval)

    def _request(self, client, source, filters, cursor, cookie, stop, progress):
        for attempt in range(3):
            self.gate.wait(source, stop)
            headers = {'User-Agent': USER_AGENT, 'Accept': 'application/json'}
            client.cookies.clear()
            try:
                if source == 'official':
                    headers.update({'Cookie': cookie, 'Referer': 'https://osu.ppy.sh/beatmapsets'})
                    params = filters.official_params()
                    if cursor:
                        params['cursor_string'] = cursor
                    response = client.get('https://osu.ppy.sh/beatmapsets/search', params=params, headers=headers)
                else:
                    response = client.post('https://api.sayobot.cn/?post', json=filters.sayobot_params(cursor), headers=headers)
                check_stop(stop)
                if response.status_code in (301, 302, 303, 307, 308, 401, 403):
                    raise DownloadError('搜索访问被拒绝或需要登录。请重新设置官网会话，或手动选择 Sayobot 搜索。')
                if response.status_code == 429:
                    delay = retry_delay(response.headers.get('Retry-After'))
                    self.gate.cooldown(source, delay)
                    raise DownloadError('搜索源限流。', retryable=True, delay=delay)
                if response.status_code != 200:
                    raise DownloadError(f'搜索源返回 HTTP {response.status_code}。', retryable=response.status_code >= 500)
                try:
                    data = response.json()
                except ValueError:
                    raise DownloadError('搜索源未返回 JSON，可能需要在浏览器完成验证。') from None
                if not isinstance(data, dict):
                    raise DownloadError('搜索响应格式异常。')
                return data
            except httpx.HTTPError:
                error = DownloadError('搜索网络超时或连接失败。', retryable=True)
            except DownloadError as exc:
                error = exc
            if not error.retryable or attempt == 2:
                raise error
            delay = error.delay if error.delay is not None else 2 ** (attempt + 1)
            progress(f'{error} 等待 {delay:.0f} 秒后重试。')
            wait_stop(stop, delay)

    def search(self, filters, source='official', cookie='', stop=None, progress=lambda msg: None, sort_spec=None):
        result = SearchResult()
        stop = stop or threading.Event()
        sort_spec = sort_spec or SortSpec()
        seen, cursors = set(), set()
        cursor = None if source == 'official' else 0
        reported_total = 0
        try:
            if source not in ('official', 'sayobot'):
                raise DownloadError('搜索源无效。')
            filters.validate(source)
            sort_spec.validate(source)
            if source == 'official' and not cookie:
                raise DownloadError('官网筛选需要有效登录会话。请先设置官网会话，或选择 Sayobot（无需登录）。')
            with httpx.Client(timeout=20, follow_redirects=False, transport=self.transport) as client:
                while True:
                    check_stop(stop)
                    progress(f'正在读取第 {result.pages + 1} 页；已匹配 {len(result.rows)} 套。')
                    data = self._request(client, source, filters, cursor, cookie, stop, progress)
                    if source == 'official':
                        if data.get('error'):
                            raise DownloadError('官网未完成搜索，请检查登录会话及筛选条件。')
                        if not isinstance(data.get('search'), dict) or data['search'].get('sort') != 'ranked_asc':
                            raise DownloadError('官网忽略了筛选条件（常见于会话失效），已停止，未采用默认列表。')
                        records = data.get('beatmapsets')
                        if 'cursor_string' not in data:
                            raise DownloadError('官网缺少分页信息，无法确认是否已读完。')
                        next_cursor = data['cursor_string']
                        if next_cursor is not None and not isinstance(next_cursor, str):
                            raise DownloadError('官网分页游标格式异常。')
                        total = data.get('total')
                        if not isinstance(total, int) or total < 0:
                            raise DownloadError('官网缺少结果总数，无法确认完整性。')
                        reported_total = max(reported_total, total)
                        terminal = not next_cursor
                    else:
                        if data.get('status') != 0:
                            raise DownloadError('Sayobot 搜索返回错误。')
                        records = data.get('data')
                        next_cursor = data.get('endid')
                        if not isinstance(next_cursor, int) or next_cursor < 0:
                            raise DownloadError('Sayobot 缺少有效分页标记，无法确认完整性。')
                        terminal = next_cursor == 0
                    if not isinstance(records, list):
                        raise DownloadError('搜索结果列表格式异常。')
                    before = len(seen)
                    for raw in records:
                        check_stop(stop)
                        row = normalize_record(raw, source)
                        if row['sid'] in seen:
                            continue
                        seen.add(row['sid'])

                        # Web search can apply genre/language even when those fields are
                        # omitted from the returned beatmapset object. Preserve the chosen
                        # value for display in that case.
                        if source == 'official':
                            if filters.genre is not None and row['genre_id'] is None:
                                row['genre_id'] = filters.genre
                                row['genre'] = GENRE_NAMES.get(filters.genre, '')
                            if filters.language is not None and row['language_id'] is None:
                                row['language_id'] = filters.language
                                row['language'] = LANGUAGE_NAMES.get(filters.language, '')

                        if filters.matches(row):
                            matched = filters.matching_beatmaps(row)
                            row['matched_beatmaps'] = matched if matched else list(row.get('beatmaps', []))
                            result.rows.append(row)
                    result.pages += 1
                    result.scanned = len(seen)
                    if terminal:
                        if source == 'official' and len(seen) < reported_total:
                            raise DownloadError('分页已结束，但数量小于官网报告总数；可能存在搜索上限或结果变化，请缩小范围。')
                        result.complete = True
                        result.message = f'搜索完成：读取 {result.pages} 页、核对 {result.scanned} 套，匹配 {len(result.rows)} 套。'
                        break
                    if next_cursor in cursors or (records and len(seen) == before):
                        raise DownloadError('搜索源重复返回同一页，已停止；当前结果不完整。')
                    cursors.add(next_cursor)
                    cursor = next_cursor
        except Stopped:
            result.message = '搜索已取消，当前仅为部分结果。'
        except DownloadError as exc:
            result.message = str(exc) + ' 当前结果未确认完整。'
        result.rows = sort_rows(result.rows, sort_spec)
        return result

