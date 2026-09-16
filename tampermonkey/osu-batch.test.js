const test = require('node:test');
const assert = require('node:assert/strict');
const {
    parseInput, normalized, buildSearchParams, normaliseRecord, recordMatches, downloadUrl,
} = require('./osu-batch.user.js');

test('parses IDs and supported osu! beatmapset links only', () => {
    const result = parseInput('123, https://osu.ppy.sh/beatmapsets/456#osu/789 osu.ppy.sh/s/777 123 bad https://example.com/9');
    assert.deepEqual(result.ids, [123, 456, 777]);
    assert.equal(result.invalid.length, 2);
});

test('normalises Unicode width and case', () => {
    assert.equal(normalized('  ＬＡＵＲ  '), 'laur');
});

test('builds official search parameters and cursor', () => {
    const params = buildSearchParams({ title: 'Song', artist: 'Laur', creator: '', status: 'ranked', mode: '0' }, 'cursor');
    assert.equal(params.get('s'), 'ranked');
    assert.equal(params.get('m'), '0');
    assert.equal(params.get('cursor_string'), 'cursor');
    assert.match(params.get('q'), /Laur/);
    const approved = buildSearchParams({ title: '', artist: '', creator: '', status: 'approved', mode: '' }, null);
    assert.equal(approved.get('s'), 'any');
    assert.equal(approved.get('q'), 'status=approved');
});

test('normalises and locally verifies official results', () => {
    const row = normaliseRecord({
        id: 42, artist: 'Laur', artist_unicode: 'ＬＡＵＲ', title: 'Song', creator: 'Mapper', status: 'ranked',
        beatmaps: [{ mode_int: 0 }, { mode_int: 3 }],
    });
    assert.equal(recordMatches(row, { artist: 'laur', title: 'son', creator: 'map', exactArtist: true, status: 'ranked', mode: '0' }), true);
    assert.equal(recordMatches(row, { artist: 'lau', title: '', creator: '', exactArtist: true, status: 'ranked', mode: '' }), false);
});

test('creates verified source URLs and rejects Mino no-video', () => {
    assert.equal(downloadUrl('official', 123, true), 'https://osu.ppy.sh/beatmapsets/123/download?noVideo=1');
    assert.equal(downloadUrl('sayobot', 123, false), 'https://txy1.sayobot.cn/beatmaps/download/full/123');
    assert.throws(() => downloadUrl('mino', 123, true));
});

