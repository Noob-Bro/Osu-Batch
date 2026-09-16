const test = require('node:test');
const assert = require('node:assert/strict');
const {
    parseInput, normalized, parseOsuDb, buildSearchParams, normaliseRecord, recordMatches, sortRecords, downloadUrl,
} = require('./osu-batch.user.js');

function makeOsuDb(version = 20250107, setId = 456) {
    const parts = [];
    const write = (size, method, value) => { const buffer = Buffer.alloc(size); buffer[method](value, 0); parts.push(buffer); };
    const u8 = value => write(1, 'writeUInt8', value);
    const i16 = value => write(2, 'writeInt16LE', value);
    const i32 = value => write(4, 'writeInt32LE', value);
    const i64 = value => write(8, 'writeBigInt64LE', BigInt(value));
    const f32 = value => write(4, 'writeFloatLE', value);
    const f64 = value => write(8, 'writeDoubleLE', value);
    const empty = () => u8(0);
    i32(version); i32(0); u8(1); i64(0); empty(); i32(1);
    for (let i = 0; i < 9; i += 1) empty();
    u8(4); i16(1); i16(2); i16(3); i64(0);
    for (let i = 0; i < 4; i += 1) f32(5);
    f64(1.4);
    for (let i = 0; i < 4; i += 1) i32(0);
    i32(60); i32(90); i32(30); i32(0);
    i32(123); i32(setId); i32(0);
    for (let i = 0; i < 4; i += 1) u8(0);
    i16(0); f32(0); u8(0); empty(); empty(); i16(0); empty();
    u8(0); i64(0); u8(1); empty(); i64(0);
    for (let i = 0; i < 5; i += 1) u8(0);
    i32(0); u8(0); i32(0);
    const buffer = Buffer.concat(parts);
    return buffer.buffer.slice(buffer.byteOffset, buffer.byteOffset + buffer.byteLength);
}

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
    const rankedDate = buildSearchParams({ status: 'ranked', statusChangedFrom: '2024-01-01', sortField: 'statusChanged', sortDescending: true }, null);
    assert.match(rankedDate.get('q'), /ranked>=2024-01-01/);
    assert.equal(rankedDate.get('sort'), 'ranked_desc');
});

test('normalises and locally verifies official results', () => {
    const row = normaliseRecord({
        id: 42, artist: 'Laur', artist_unicode: 'ＬＡＵＲ', title: 'Song', creator: 'Mapper', status: 'ranked',
        beatmaps: [{ mode_int: 0 }, { mode_int: 3 }],
    });
    assert.equal(recordMatches(row, { artist: 'laur', title: 'son', creator: 'map', exactArtist: true, status: 'ranked', mode: '0' }), true);
    assert.equal(recordMatches(row, { artist: 'lau', title: '', creator: '', exactArtist: true, status: 'ranked', mode: '' }), false);
});

test('parses a modern osu!stable database and extracts beatmapset IDs', async () => {
    const result = await parseOsuDb(makeOsuDb());
    assert.equal(result.version, 20250107);
    assert.equal(result.beatmapCount, 1);
    assert.deepEqual(result.setIds, [456]);
});

test('applies advanced ranges, dates and sorting', () => {
    const first = normaliseRecord({
        id: 1, artist: 'B', title: 'Second', creator: 'Mapper', source: 'Game', status: 'ranked',
        genre: { id: 2 }, language: { id: 3 }, submitted_date: '2024-01-03T00:00:00Z',
        last_updated: '2024-02-03T00:00:00Z', ranked_date: '2024-03-03T00:00:00Z',
        beatmaps: [{ mode_int: 0, bpm: 180, total_length: 120, difficulty_rating: 5.2 }],
    });
    const second = normaliseRecord({ id: 2, artist: 'A', title: 'First', status: 'ranked', beatmaps: [{ mode_int: 0, bpm: 120, total_length: 90, difficulty_rating: 3 }] });
    assert.equal(recordMatches(first, {
        artist: '', title: '', creator: '', sourceText: 'game', exactArtist: true, status: 'ranked', mode: '0',
        genre: '2', language: '3', bpmMin: '170', bpmMax: '190', lengthMin: '100', lengthMax: '130',
        difficultyMin: '5', difficultyMax: '6', submittedFrom: '2024-01-01', submittedTo: '2024-01-31',
    }), true);
    assert.deepEqual(sortRecords([first, second], 'artist', false).map(row => row.sid), [2, 1]);
    assert.throws(() => buildSearchParams({ bpmMin: '200', bpmMax: '100' }, null), /minimum/);
    assert.equal(recordMatches(second, {
        artist: '', title: '', creator: '', exactArtist: true, status: 'ranked', mode: '0',
        statusChangedFrom: '2024-01-01', statusChangedTo: '2024-12-31',
    }), true, 'missing response dates must not discard server-filtered results');
});

test('creates verified source URLs and rejects Mino no-video', () => {
    assert.equal(downloadUrl('official', 123, true), 'https://osu.ppy.sh/beatmapsets/123/download?noVideo=1');
    assert.equal(downloadUrl('sayobot', 123, false), 'https://txy1.sayobot.cn/beatmaps/download/full/123');
    assert.throws(() => downloadUrl('mino', 123, true));
});

