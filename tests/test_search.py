import json
import threading

import httpx
import pytest

from search import Filters, Searcher, SortSpec, sort_rows


def beatmap(mode=0, *, convert=False, bpm=180, length=120, stars=4.5, version='Insane'):
    return dict(mode_int=mode, convert=convert, bpm=bpm, total_length=length,
                difficulty_rating=stars, version=version)


def record(sid, artist='Laur', status='ranked', mode=0, convert=False, *, title='Song',
           artist_unicode='', title_unicode='', source='Game', creator='Mapper', genre_id=10,
           language_id=5, submitted='2026-07-01T12:00:00Z',
           updated='2026-08-20T12:00:00Z', ranked='2026-08-25T12:00:00Z', beatmaps=None):
    return dict(
        id=sid, artist=artist, artist_unicode=artist_unicode, title=title,
        title_unicode=title_unicode, source=source, creator=creator, status=status,
        genre={'id': genre_id, 'name': 'Electronic'},
        language={'id': language_id, 'name': 'Instrumental'},
        submitted_date=submitted, last_updated=updated, ranked_date=ranked,
        beatmaps=beatmaps if beatmaps is not None else [beatmap(mode, convert=convert)],
    )


def official(rows, cursor=None, total=None):
    return dict(beatmapsets=rows, cursor_string=cursor, total=len(rows) if total is None else total,
                search={'sort': 'ranked_asc'}, error=None)


def sayo(sid, artist='Laur', status=1, modes=1, *, title='Song', creator='Mapper'):
    return dict(sid=sid, artist=artist, artistU='', title=title, creator=creator,
                approved=status, modes=modes)


def legacy_filters(**kwargs):
    base = dict(artist='Laur', status='ranked', mode=0, exact_artist=True)
    base.update(kwargs)
    return Filters(**base)


def test_filters_default_to_no_filter():
    filters = Filters()
    assert filters.artist == '' and filters.status == 'any' and filters.mode is None
    params = filters.official_params()
    assert params['q'] == '' and params['s'] == 'any'
    assert 'm' not in params and 'g' not in params and 'l' not in params


def test_official_all_pages_and_local_filters():
    seen = []

    def handler(req):
        seen.append(req)
        assert req.url.params['m'] == '0'
        assert req.url.params['s'] == 'ranked'
        assert req.url.params['nsfw'] == 'true'
        assert '"Laur"' in req.url.params['q']
        if len(seen) == 1:
            return httpx.Response(200, json=official([record(1), record(2, 'Laura')], 'next', 5))
        assert req.url.params['cursor_string'] == 'next'
        return httpx.Response(200, json=official([
            record(3, status='approved'), record(4, mode=1), record(5, 'LAUR')
        ], None, 5))

    result = Searcher(httpx.MockTransport(handler), 0).search(legacy_filters(), 'official', 'osu_session=test')
    assert result.complete and [row['sid'] for row in result.rows] == [1, 5]
    assert result.pages == 2 and result.scanned == 5


def test_advanced_official_filters_and_same_difficulty_matching():
    filters = Filters(
        title='Song', artist='Laur', source_text='Game', genre=10, language=5,
        bpm_min=170, bpm_max=190, length_min=100, length_max=150,
        creator='Mapper', mode=0, difficulty_min=4, difficulty_max=5,
        status='ranked', submitted_from='2026-07-01', submitted_to='2026-07-31',
        updated_from='2026-08-01', updated_to='2026-08-31',
        status_changed_from='2026-08-20', status_changed_to='2026-08-31',
    )
    params = filters.official_params()
    assert params['g'] == '10' and params['l'] == '5' and params['m'] == '0'
    for token in ('bpm>=170', 'bpm<=190', 'length>=100', 'length<=150',
                  'stars>=4', 'stars<=5', 'submitted>=2026-07-01', 'submitted<=2026-07-31',
                  'updated>=2026-08-01', 'updated<=2026-08-31',
                  'ranked>=2026-08-20', 'ranked<=2026-08-31'):
        assert token in params['q']

    good = record(1, beatmaps=[beatmap(0, bpm=180, length=120, stars=4.5)])
    split = record(2, beatmaps=[
        beatmap(0, bpm=180, length=120, stars=6.2),
        beatmap(1, bpm=180, length=120, stars=4.5),
    ])
    wrong_date = record(3, updated='2026-09-01T00:00:00Z')
    assert filters.matches(__import__('search').normalize_record(good, 'official'))
    assert not filters.matches(__import__('search').normalize_record(split, 'official'))
    assert not filters.matches(__import__('search').normalize_record(wrong_date, 'official'))


def test_unicode_and_romanized_metadata_filters_are_independent():
    row = __import__('search').normalize_record(record(
        10, artist='Hatsune Miku', artist_unicode='初音ミク',
        title='Senbonzakura', title_unicode='千本桜'
    ), 'official')

    assert Filters(title='千本', artist='初音ミク').matches(row)
    assert Filters(title='Senbon', artist='Hatsune Miku').matches(row)
    assert Filters(title_romanized='Senbon', artist_romanized='Hatsune Miku', exact_artist=False).matches(row)
    assert not Filters(title_romanized='千本').matches(row)
    assert not Filters(artist_romanized='初音ミク', exact_artist=False).matches(row)

    params = Filters(title_romanized='Senbonzakura', artist_romanized='Hatsune Miku').official_params()
    assert 'title="Senbonzakura"' in params['q']
    assert 'artist="Hatsune Miku"' in params['q']


def test_submitted_updated_and_status_changed_dates_are_separate():
    row = __import__('search').normalize_record(record(
        11,
        submitted='2026-07-10T00:00:00Z',
        updated='2026-08-10T00:00:00Z',
        ranked='2026-09-01T00:00:00Z',
    ), 'official')
    assert Filters(submitted_from='2026-07-01', submitted_to='2026-07-31').matches(row)
    assert Filters(updated_from='2026-08-01', updated_to='2026-08-31').matches(row)
    assert Filters(status_changed_from='2026-09-01', status_changed_to='2026-09-02').matches(row)
    assert not Filters(status_changed_to='2026-08-31').matches(row)

    no_status_date = __import__('search').normalize_record(record(12, ranked=''), 'official')
    assert not Filters(status_changed_from='2026-01-01').matches(no_status_date)


def test_sort_supports_romanized_and_three_date_fields():
    rows = [
        __import__('search').normalize_record(record(
            1, title='Zulu', title_unicode='阿', artist='Zulu Artist', artist_unicode='乙',
            submitted='2026-03-01T00:00:00Z', updated='2026-04-01T00:00:00Z', ranked='2026-05-01T00:00:00Z'
        ), 'official'),
        __import__('search').normalize_record(record(
            2, title='Alpha', title_unicode='字', artist='Alpha Artist', artist_unicode='甲',
            submitted='2026-01-01T00:00:00Z', updated='2026-02-01T00:00:00Z', ranked='2026-03-01T00:00:00Z'
        ), 'official'),
    ]
    assert [r['sid'] for r in sort_rows(rows, SortSpec('title_romanized'))] == [2, 1]
    assert [r['sid'] for r in sort_rows(rows, SortSpec('artist_romanized'))] == [2, 1]
    assert [r['sid'] for r in sort_rows(rows, SortSpec('submitted'))] == [2, 1]
    assert [r['sid'] for r in sort_rows(rows, SortSpec('updated'))] == [2, 1]
    assert [r['sid'] for r in sort_rows(rows, SortSpec('status_changed'))] == [2, 1]


def test_local_sort_uses_matching_difficulties_and_keeps_missing_last():
    filters = Filters(mode=0, difficulty_min=3, difficulty_max=6)
    rows = []
    for sid, stars in [(1, 5.0), (2, 3.5), (3, 4.2)]:
        row = __import__('search').normalize_record(record(sid, beatmaps=[beatmap(0, stars=stars)]), 'official')
        row['matched_beatmaps'] = filters.matching_beatmaps(row)
        rows.append(row)
    assert [r['sid'] for r in sort_rows(rows, SortSpec('difficulty'))] == [2, 3, 1]
    assert [r['sid'] for r in sort_rows(rows, SortSpec('difficulty', True))] == [1, 3, 2]


def test_guest_and_ignored_filters():
    calls = []

    def handler(req):
        calls.append(req)
        return httpx.Response(200, json={'beatmapsets': [record(1)], 'search': {'sort': 'ranked_desc'}})

    searcher = Searcher(httpx.MockTransport(handler), 0)
    assert not searcher.search(Filters()).complete
    assert not calls
    result = searcher.search(Filters(), 'official', 'osu_session=expired')
    assert not result.complete and not result.rows and '忽略' in result.message


def test_sayobot_endid_pagination_not_numeric_offset():
    calls = []

    def handler(req):
        payload = json.loads(req.content)
        calls.append(payload)
        assert 'cookie' not in req.headers
        assert payload['subtype'] == 2 and payload['mode'] == 1 and payload['class'] == 1
        assert payload['keyword'] == 'Laur'
        if payload['offset'] == 0:
            return httpx.Response(200, json={
                'data': [sayo(1), sayo(2, 'Laur feat. Sennzai')],
                'endid': 789, 'results': 9000, 'status': 0,
            })
        assert payload['offset'] == 789
        return httpx.Response(200, json={
            'data': [sayo(1), sayo(3), sayo(4, status=2), sayo(5, modes=2)],
            'endid': 0, 'results': 9000, 'status': 0,
        })

    result = Searcher(httpx.MockTransport(handler), 0).search(legacy_filters(), 'sayobot', 'osu_session=private')
    assert result.complete and [row['sid'] for row in result.rows] == [1, 3] and len(calls) == 2


def test_sayobot_default_is_unfiltered_and_advanced_fields_are_rejected_before_request():
    calls = []

    def handler(req):
        calls.append(req)
        payload = json.loads(req.content)
        assert payload['keyword'] == '' and payload['mode'] == 15 and payload['class'] == 31
        return httpx.Response(200, json={'data': [sayo(1)], 'endid': 0, 'status': 0})

    searcher = Searcher(httpx.MockTransport(handler), 0)
    result = searcher.search(Filters(), 'sayobot')
    assert result.complete and [row['sid'] for row in result.rows] == [1]
    calls.clear()
    result = searcher.search(Filters(bpm_min=180), 'sayobot')
    assert not result.complete and not calls and 'BPM' in result.message and '官方' in result.message


def test_contains_and_hybrid_mode():
    rows = [sayo(1, 'Laur feat. Sennzai', modes=3), sayo(2, 'Laura', modes=1), sayo(3, 'Laur', modes=2)]
    transport = httpx.MockTransport(lambda req: httpx.Response(200, json={'data': rows, 'endid': 0, 'status': 0}))
    result = Searcher(transport, 0).search(Filters(artist='Laur', mode=0, exact_artist=False), 'sayobot')
    assert [row['sid'] for row in result.rows] == [1, 2]


def test_title_creator_status_and_sort_on_sayobot():
    rows = [
        sayo(1, title='Alpha', creator='Zed'),
        sayo(2, title='Beta', creator='Ann'),
        sayo(3, title='Alpha Extra', creator='Ann'),
    ]
    transport = httpx.MockTransport(lambda req: httpx.Response(200, json={'data': rows, 'endid': 0, 'status': 0}))
    result = Searcher(transport, 0).search(
        Filters(title='Alpha', creator='Ann'), 'sayobot', sort_spec=SortSpec('title')
    )
    assert result.complete and [row['sid'] for row in result.rows] == [3]


def test_repeated_cursor_partial_not_complete():
    n = 0

    def handler(req):
        nonlocal n
        n += 1
        return httpx.Response(200, json=official([record(n)], 'same', 9))

    result = Searcher(httpx.MockTransport(handler), 0).search(Filters(), 'official', 'osu_session=test')
    assert not result.complete and result.pages == 2 and '重复' in result.message


def test_truncated_official_total():
    result = Searcher(httpx.MockTransport(lambda req: httpx.Response(200, json=official([record(1)], None, 99))), 0).search(
        Filters(), 'official', 'osu_session=test'
    )
    assert not result.complete and '总数' in result.message


@pytest.mark.parametrize('data', [
    {'data': [], 'status': 0},
    {'data': [], 'status': 5, 'endid': 0},
    {'data': [{'sid': 1}], 'status': 0, 'endid': 0},
])
def test_bad_sayobot_data_not_complete(data):
    result = Searcher(httpx.MockTransport(lambda req: httpx.Response(200, json=data)), 0).search(Filters(), 'sayobot')
    assert not result.complete


def test_empty_search_complete():
    result = Searcher(httpx.MockTransport(lambda req: httpx.Response(200, json={'data': [], 'status': 0, 'endid': 0})), 0).search(
        Filters(), 'sayobot'
    )
    assert result.complete and not result.rows


def test_cancel_preserves_partial():
    stop = threading.Event()

    def handler(req):
        return httpx.Response(200, json={'data': [sayo(1)], 'status': 0, 'endid': 12})

    def progress(message):
        if '第 2 页' in message:
            stop.set()

    result = Searcher(httpx.MockTransport(handler), 0).search(Filters(), 'sayobot', stop=stop, progress=progress)
    assert not result.complete and len(result.rows) == 1 and '取消' in result.message


def test_error_page_and_redirect_no_cookie_forwarding():
    requests = []

    def handler(req):
        requests.append(req)
        return httpx.Response(302, headers={'Location': 'https://third.party.example/'})

    result = Searcher(httpx.MockTransport(handler), 0).search(Filters(), 'official', 'osu_session=secret')
    assert not result.complete and len(requests) == 1 and 'secret' not in result.message


def test_http_error_after_first_page_keeps_partial(monkeypatch):
    monkeypatch.setattr('search.wait_stop', lambda *args: None)
    calls = []

    def handler(req):
        calls.append(req)
        if len(calls) == 1:
            return httpx.Response(200, json={'data': [sayo(1)], 'status': 0, 'endid': 10})
        return httpx.Response(503)

    result = Searcher(httpx.MockTransport(handler), 0).search(Filters(), 'sayobot')
    assert not result.complete and len(result.rows) == 1 and len(calls) == 4


def test_ranked_is_not_approved():
    result = Searcher(httpx.MockTransport(lambda req: httpx.Response(200, json={
        'data': [sayo(1, status=1), sayo(2, status=2)], 'status': 0, 'endid': 0,
    })), 0).search(Filters(status='approved'), 'sayobot')
    assert result.complete and [row['sid'] for row in result.rows] == [2]

