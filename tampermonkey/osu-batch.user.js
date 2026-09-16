// ==UserScript==
// @name         osu! Batch Web
// @name:zh-CN   osu! Batch 网页版
// @namespace    https://github.com/Noob-Bro/Osu-Batch
// @version      0.2.1
// @description  Batch-search and download osu! beatmapsets from osu.ppy.sh.
// @description:zh-CN 在 osu! 官网筛选、收集并批量下载谱面集。
// @author       Noob-Bro
// @match        https://osu.ppy.sh/*
// @icon         https://osu.ppy.sh/favicon.ico
// @grant        GM_addStyle
// @grant        GM_download
// @grant        GM_getValue
// @grant        GM_setValue
// @grant        GM_registerMenuCommand
// @connect      osu.ppy.sh
// @connect      api.nerinyan.moe
// @connect      txy1.sayobot.cn
// @connect      catboy.best
// @run-at       document-idle
// @noframes
// @updateURL    https://raw.githubusercontent.com/Noob-Bro/Osu-Batch/tampermonkey-web/tampermonkey/osu-batch.user.js
// @downloadURL  https://raw.githubusercontent.com/Noob-Bro/Osu-Batch/tampermonkey-web/tampermonkey/osu-batch.user.js
// ==/UserScript==

(function (root, factory) {
    const api = factory();
    if (typeof module === 'object' && module.exports) module.exports = api;
    else api.init();
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
    'use strict';

    const STORE_KEY = 'osuBatchWebStateV1';
    const MAX_ID = 2 ** 31;
    const SOURCES = {
        official: 'osu! official',
        sayobot: 'Sayobot',
        nerinyan: 'Nerinyan',
        mino: 'Mino',
    };
    const GENRES = [
        ['', 'Any', '不限'], ['1', 'Unspecified', '未指定'], ['2', 'Video Game', '游戏'], ['3', 'Anime', '动漫'],
        ['4', 'Rock', '摇滚'], ['5', 'Pop', '流行'], ['6', 'Other', '其他'], ['7', 'Novelty', '新奇'],
        ['9', 'Hip Hop', '嘻哈'], ['10', 'Electronic', '电子'], ['11', 'Metal', '金属'], ['12', 'Classical', '古典'],
        ['13', 'Folk', '民谣'], ['14', 'Jazz', '爵士'],
    ];
    const LANGUAGES = [
        ['', 'Any', '不限'], ['1', 'Unspecified', '未指定'], ['2', 'English', '英语'], ['3', 'Japanese', '日语'],
        ['4', 'Chinese', '中文'], ['5', 'Instrumental', '纯音乐'], ['6', 'Korean', '韩语'], ['7', 'French', '法语'],
        ['8', 'German', '德语'], ['9', 'Swedish', '瑞典语'], ['10', 'Spanish', '西班牙语'], ['11', 'Italian', '意大利语'],
        ['12', 'Russian', '俄语'], ['13', 'Polish', '波兰语'], ['14', 'Other', '其他'],
    ];
    const SORT_FIELDS = [
        ['default', 'Website default', '网站默认'], ['title', 'Title', '歌名'], ['titleRomanized', 'Title (romanized)', '歌名（罗马字）'],
        ['artist', 'Artist', '艺术家'], ['artistRomanized', 'Artist (romanized)', '艺术家（罗马字）'], ['source', 'Source', '来源'],
        ['creator', 'Mapper', '谱师'], ['status', 'Status', '状态'], ['submitted', 'Submitted', '提交日期'],
        ['updated', 'Updated', '更新日期'], ['statusChanged', 'Ranked/approved date', '上架/达标日期'], ['mode', 'Mode', '模式'],
        ['bpm', 'BPM', 'BPM'], ['length', 'Length', '时长'], ['difficulty', 'Stars', '星数'],
    ];
    const TEXT = {
        en: {
            title: 'osu! Batch Web', hide: 'Hide', input: 'Beatmapset links or IDs', add: 'Add to queue',
            collect: 'Collect this page', search: 'Search all pages', stopSearch: 'Stop search',
            artist: 'Artist', titleField: 'Title', creator: 'Mapper', exact: 'Exact artist', status: 'Status',
            mode: 'Mode', any: 'Any', source: 'Download source', noVideo: 'No video', interval: 'Interval (s)',
            artistRomanized: 'Artist (romanized)', titleRomanized: 'Title (romanized)', sourceText: 'Source',
            genre: 'Genre', language: 'Language', bpmMin: 'Min BPM', bpmMax: 'Max BPM',
            lengthMin: 'Min length (s)', lengthMax: 'Max length (s)', difficultyMin: 'Min stars', difficultyMax: 'Max stars',
            submittedFrom: 'Submitted from', submittedTo: 'Submitted to', updatedFrom: 'Updated from', updatedTo: 'Updated to',
            statusChangedFrom: 'Ranked/approved from', statusChangedTo: 'Ranked/approved to',
            sortField: 'Sort by', sortDescending: 'Descending', advanced: 'Advanced filters',
            start: 'Start / resume', pause: 'Pause', clearDone: 'Clear completed', clearAll: 'Clear all',
            id: 'ID', metadata: 'Beatmapset', state: 'State', waiting: 'Waiting', downloading: 'Downloading',
            completed: 'Completed', failed: 'Failed', paused: 'Paused', queueEmpty: 'Queue is empty.',
            added: n => `Added ${n} beatmapset(s).`, invalid: n => `${n} invalid token(s) ignored.`,
            collected: n => `Collected ${n} beatmapset(s) from this page.`, searching: (p, n) => `Reading page ${p}; ${n} unique result(s).`,
            searchDone: n => `Search complete: ${n} beatmapset(s) found. Select the ones to add to the download queue.`, login: 'Official download uses your current osu! website session.',
            searchResults: 'Search results', selectAll: 'Select all', selectNone: 'Select none', addSelected: 'Add selected',
            selectedCount: (selected, total) => `${selected}/${total} selected`, previous: 'Previous', next: 'Next',
            resultPage: (page, pages) => `Page ${page}/${pages}`, nativeFallback: 'Tampermonkey blocked .osz; started with the browser download instead.',
            browserLimit: 'Your browser may ask for permission to allow multiple downloads.',
            localLimit: 'For security, select osu!.db manually. It is parsed locally and is never uploaded. osu!lazer client.realm is not supported yet.',
            loadDb: 'Load osu!.db', clearDb: 'Clear local library', local: 'Already local',
            dbReading: (n, total, sets) => `Reading osu!.db: ${n}/${total} beatmaps; ${sets} beatmapsets found.`,
            dbLoaded: (sets, maps, version) => `Local library loaded: ${sets} beatmapsets / ${maps} beatmaps (db ${version}).`,
            dbCleared: 'Local-library index cleared.', dbError: value => `Could not read osu!.db: ${value}`,
            confirmClear: 'Clear every queue record? Downloaded files will not be deleted.',
            unsupportedNoVideo: 'The selected source has no verified no-video endpoint.',
            stopped: 'Stopped.', open: 'Open', lang: '中文', show: 'osu! Batch',
        },
        zh: {
            title: 'osu! Batch 网页版', hide: '隐藏', input: '谱面集链接或 ID', add: '加入队列',
            collect: '收集当前页面', search: '搜索全部分页', stopSearch: '停止搜索',
            artist: '艺术家', titleField: '歌名', creator: '谱师', exact: '艺术家精确匹配', status: '状态',
            mode: '模式', any: '不限', source: '下载来源', noVideo: '不含视频', interval: '间隔（秒）',
            artistRomanized: '艺术家（罗马字）', titleRomanized: '歌名（罗马字）', sourceText: '来源',
            genre: '曲风', language: '语言', bpmMin: '最低 BPM', bpmMax: '最高 BPM',
            lengthMin: '最短时长（秒）', lengthMax: '最长时长（秒）', difficultyMin: '最低星数', difficultyMax: '最高星数',
            submittedFrom: '提交日期起', submittedTo: '提交日期止', updatedFrom: '更新日期起', updatedTo: '更新日期止',
            statusChangedFrom: '上架/达标日期起', statusChangedTo: '上架/达标日期止',
            sortField: '排序字段', sortDescending: '降序', advanced: '高级筛选',
            start: '开始 / 继续', pause: '暂停', clearDone: '清除已完成', clearAll: '清除全部',
            id: 'ID', metadata: '谱面集', state: '状态', waiting: '等待', downloading: '下载中',
            completed: '已完成', failed: '失败', paused: '已暂停', queueEmpty: '队列为空。',
            added: n => `已加入 ${n} 个谱面集。`, invalid: n => `已忽略 ${n} 个无效输入。`,
            collected: n => `已从当前页面收集 ${n} 个谱面集。`, searching: (p, n) => `正在读取第 ${p} 页；已有 ${n} 个不重复结果。`,
            searchDone: n => `搜索完成：找到 ${n} 个谱面集。请勾选需要加入下载队列的歌曲。`, login: '官方下载使用当前 osu! 网页登录会话。',
            searchResults: '筛选结果', selectAll: '全选', selectNone: '全不选', addSelected: '加入已选项',
            selectedCount: (selected, total) => `已选 ${selected}/${total}`, previous: '上一页', next: '下一页',
            resultPage: (page, pages) => `第 ${page}/${pages} 页`, nativeFallback: 'Tampermonkey 拦截了 .osz，已改用浏览器原生下载。',
            browserLimit: '浏览器可能询问是否允许连续下载多个文件。',
            localLimit: '受浏览器安全限制，需手动选择 osu!.db；文件只在本地解析，不会上传。暂不支持 osu!lazer client.realm。',
            loadDb: '载入 osu!.db', clearDb: '清除本地曲库', local: '本地已有',
            dbReading: (n, total, sets) => `正在读取 osu!.db：${n}/${total} 张谱面；已找到 ${sets} 个谱面集。`,
            dbLoaded: (sets, maps, version) => `本地曲库已载入：${sets} 个谱面集 / ${maps} 张谱面（数据库 ${version}）。`,
            dbCleared: '已清除本地曲库索引。', dbError: value => `无法读取 osu!.db：${value}`,
            confirmClear: '确定清除全部队列记录吗？已下载文件不会被删除。',
            unsupportedNoVideo: '所选来源没有经过验证的无视频下载接口。',
            stopped: '已停止。', open: '打开', lang: 'English', show: 'osu! Batch',
        },
    };

    function parseInput(text) {
        const ids = [];
        const invalid = [];
        for (const raw of String(text || '').trim().split(/[\s,，;；]+/)) {
            if (!raw) continue;
            let value = null;
            if (/^\d+$/.test(raw)) value = Number(raw);
            else {
                try {
                    const url = new URL(raw.includes('://') ? raw : `https://${raw}`);
                    const match = url.pathname.match(/^\/(?:beatmapsets|s)\/(\d+)(?:\/download)?\/?$/);
                    if (url.protocol === 'https:' && url.hostname === 'osu.ppy.sh' && match) value = Number(match[1]);
                } catch (_) { /* invalid token */ }
            }
            if (Number.isInteger(value) && value > 0 && value < MAX_ID) {
                if (!ids.includes(value)) ids.push(value);
            } else invalid.push(raw);
        }
        return { ids, invalid };
    }

    function normalized(value) {
        return String(value || '').normalize('NFKC').trim().toLocaleLowerCase();
    }

    class BinaryReader {
        constructor(buffer) {
            this.view = new DataView(buffer);
            this.bytes = new Uint8Array(buffer);
            this.offset = 0;
        }
        require(size) {
            if (!Number.isInteger(size) || size < 0 || this.offset + size > this.view.byteLength) throw new Error('Unexpected end of osu!.db');
        }
        u8() { this.require(1); return this.view.getUint8(this.offset++); }
        i16() { this.require(2); const v = this.view.getInt16(this.offset, true); this.offset += 2; return v; }
        i32() { this.require(4); const v = this.view.getInt32(this.offset, true); this.offset += 4; return v; }
        i64() { this.require(8); const v = this.view.getBigInt64(this.offset, true); this.offset += 8; return v; }
        f32() { this.require(4); const v = this.view.getFloat32(this.offset, true); this.offset += 4; return v; }
        f64() { this.require(8); const v = this.view.getFloat64(this.offset, true); this.offset += 8; return v; }
        uleb128() {
            let value = 0; let shift = 0;
            for (let i = 0; i < 5; i += 1) {
                const byte = this.u8(); value |= (byte & 0x7f) << shift;
                if ((byte & 0x80) === 0) return value >>> 0;
                shift += 7;
            }
            throw new Error('Invalid ULEB128 value in osu!.db');
        }
        skipString() {
            const marker = this.u8();
            if (marker === 0) return;
            if (marker !== 0x0b) throw new Error('Invalid string marker in osu!.db');
            const length = this.uleb128(); this.require(length); this.offset += length;
        }
    }

    function skipStarRatings(reader, version) {
        const count = reader.i32();
        if (count < 0 || count > 100000) throw new Error('Invalid star-rating count in osu!.db');
        for (let i = 0; i < count; i += 1) {
            if (reader.u8() !== 0x08) throw new Error('Invalid star-rating mod marker');
            reader.i32();
            const marker = reader.u8();
            if (version >= 20250107) {
                if (marker !== 0x0c) throw new Error('Invalid float marker in osu!.db');
                reader.f32();
            } else {
                if (marker !== 0x0d) throw new Error('Invalid double marker in osu!.db');
                reader.f64();
            }
        }
    }

    async function parseOsuDb(buffer, onProgress = () => {}) {
        if (!(buffer instanceof ArrayBuffer)) throw new TypeError('osu!.db must be an ArrayBuffer');
        const reader = new BinaryReader(buffer);
        const version = reader.i32();
        if (version < 20070000 || version > 21000000) throw new Error(`Unsupported osu!.db version: ${version}`);
        reader.i32(); // folder count
        reader.u8(); // account unlocked
        reader.i64();
        reader.skipString(); // player name
        const beatmapCount = reader.i32();
        if (beatmapCount < 0 || beatmapCount > 2000000) throw new Error('Invalid beatmap count in osu!.db');
        const setIds = new Set();
        for (let index = 0; index < beatmapCount; index += 1) {
            if (version < 20191106) reader.i32();
            for (let i = 0; i < 9; i += 1) reader.skipString();
            reader.u8();
            reader.i16(); reader.i16(); reader.i16(); reader.i64();
            if (version < 20140609) { reader.u8(); reader.u8(); reader.u8(); reader.u8(); }
            else { reader.f32(); reader.f32(); reader.f32(); reader.f32(); }
            reader.f64();
            if (version >= 20140609) for (let mode = 0; mode < 4; mode += 1) skipStarRatings(reader, version);
            reader.i32(); reader.i32(); reader.i32();
            const timingCount = reader.i32();
            if (timingCount < 0 || timingCount > 1000000) throw new Error('Invalid timing-point count in osu!.db');
            for (let i = 0; i < timingCount; i += 1) { reader.f64(); reader.f64(); reader.u8(); }
            reader.i32(); // difficulty / beatmap ID
            const setId = reader.i32();
            if (setId > 0 && setId < MAX_ID) setIds.add(setId);
            reader.i32();
            reader.u8(); reader.u8(); reader.u8(); reader.u8();
            reader.i16(); reader.f32(); reader.u8();
            reader.skipString(); reader.skipString(); reader.i16(); reader.skipString();
            reader.u8(); reader.i64(); reader.u8(); reader.skipString(); reader.i64();
            reader.u8(); reader.u8(); reader.u8(); reader.u8(); reader.u8();
            if (version < 20140609) reader.i16();
            reader.i32(); reader.u8();
            if ((index + 1) % 500 === 0) {
                onProgress(index + 1, beatmapCount, setIds.size);
                await new Promise(resolve => setTimeout(resolve, 0));
            }
        }
        reader.i32(); // user permissions
        onProgress(beatmapCount, beatmapCount, setIds.size);
        return { version, beatmapCount, setIds: [...setIds] };
    }

    function cleanTerm(value, label) {
        const result = String(value || '').trim();
        if (result.length > 200 || /[\r\n"\\]/.test(result)) throw new Error(`${label}: invalid text`);
        return result;
    }

    function cleanRangeNumber(value, label) {
        if (value === '' || value == null) return null;
        const number = Number(value);
        if (!Number.isFinite(number) || number < 0) throw new Error(`${label}: invalid number`);
        return number;
    }

    function validateRange(lower, upper, label) {
        const min = cleanRangeNumber(lower, `${label} min`);
        const max = cleanRangeNumber(upper, `${label} max`);
        if (min != null && max != null && min > max) throw new Error(`${label}: minimum is greater than maximum`);
        return [min, max];
    }

    function buildSearchParams(filters, cursor) {
        const query = [];
        const title = cleanTerm(filters.title, 'title');
        const titleRomanized = cleanTerm(filters.titleRomanized, 'titleRomanized');
        const artist = cleanTerm(filters.artist, 'artist');
        const artistRomanized = cleanTerm(filters.artistRomanized, 'artistRomanized');
        const sourceText = cleanTerm(filters.sourceText, 'source');
        const creator = cleanTerm(filters.creator, 'creator');
        for (const [field, value] of [['title', title], ['artist', artist], ['source', sourceText], ['creator', creator]]) {
            if (value) query.push(`${field}="${value}"`);
        }
        if (titleRomanized && titleRomanized !== title) query.push(`title="${titleRomanized}"`);
        if (artistRomanized && artistRomanized !== artist) query.push(`artist="${artistRomanized}"`);
        for (const [name, lower, upper] of [
            ['bpm', filters.bpmMin, filters.bpmMax], ['length', filters.lengthMin, filters.lengthMax],
            ['stars', filters.difficultyMin, filters.difficultyMax],
        ]) {
            const [min, max] = validateRange(lower, upper, name);
            if (min != null) query.push(`${name}>=${min}`);
            if (max != null) query.push(`${name}<=${max}`);
        }
        for (const [name, lower, upper] of [
            ['submitted', filters.submittedFrom, filters.submittedTo],
            ['updated', filters.updatedFrom, filters.updatedTo],
            ['ranked', filters.statusChangedFrom, filters.statusChangedTo],
        ]) {
            if (lower && upper && lower > upper) throw new Error(`${name}: start is after end`);
            if (lower) query.push(`${name}>=${lower}`);
            if (upper) query.push(`${name}<=${upper}`);
        }
        let status = filters.status || 'any';
        // osu!web treats legacy Approved as a structured query term rather
        // than a value accepted by the `s` parameter.
        if (status === 'approved') { query.push('status=approved'); status = 'any'; }
        let sort = 'ranked_asc';
        if (filters.sortField === 'statusChanged') sort = `ranked_${filters.sortDescending ? 'desc' : 'asc'}`;
        else if (filters.sortField === 'updated') sort = `updated_${filters.sortDescending ? 'desc' : 'asc'}`;
        const params = new URLSearchParams({ q: query.join(' '), s: status, sort, nsfw: 'true' });
        if (filters.mode !== '' && filters.mode != null) params.set('m', String(filters.mode));
        if (filters.genre !== '' && filters.genre != null) params.set('g', String(filters.genre));
        if (filters.language !== '' && filters.language != null) params.set('l', String(filters.language));
        if (cursor) params.set('cursor_string', cursor);
        return params;
    }

    function normaliseRecord(raw) {
        const sid = Number(raw && raw.id);
        if (!Number.isInteger(sid) || sid <= 0 || sid >= MAX_ID) throw new Error('Invalid beatmapset ID');
        const beatmaps = (raw.beatmaps || []).map(item => ({
            mode: Number(item.mode_int), bpm: Number(item.bpm), length: Number(item.total_length), stars: Number(item.difficulty_rating),
        })).filter(item => Number.isInteger(item.mode));
        const metadataId = value => Number(value && typeof value === 'object' ? value.id : value);
        return {
            sid,
            artist: String(raw.artist || ''),
            artistUnicode: String(raw.artist_unicode || ''),
            title: String(raw.title || ''),
            titleUnicode: String(raw.title_unicode || ''),
            creator: String(raw.creator || ''),
            sourceText: String(raw.source || ''),
            genre: metadataId(raw.genre || raw.genre_id),
            language: metadataId(raw.language || raw.language_id),
            status: String(raw.status || ''),
            submittedDate: String(raw.submitted_date || ''),
            updatedDate: String(raw.last_updated || ''),
            statusChangedDate: String(raw.ranked_date || ''),
            beatmaps,
            modes: [...new Set(beatmaps.map(item => item.mode))],
        };
    }

    function inRange(value, lower, upper) {
        if ((lower === '' || lower == null) && (upper === '' || upper == null)) return true;
        if (!Number.isFinite(value)) return false;
        return (lower === '' || lower == null || value >= Number(lower)) && (upper === '' || upper == null || value <= Number(upper));
    }

    function dateInRange(value, lower, upper) {
        if (!lower && !upper) return true;
        const day = String(value || '').slice(0, 10);
        return /^\d{4}-\d{2}-\d{2}$/.test(day) && (!lower || day >= lower) && (!upper || day <= upper);
    }

    function recordMatches(row, filters) {
        const title = normalized(filters.title);
        const titleRomanized = normalized(filters.titleRomanized);
        const artist = normalized(filters.artist);
        const artistRomanized = normalized(filters.artistRomanized);
        const sourceText = normalized(filters.sourceText);
        const creator = normalized(filters.creator);
        if (title && ![row.title, row.titleUnicode].some(v => normalized(v).includes(title))) return false;
        if (titleRomanized && !normalized(row.title).includes(titleRomanized)) return false;
        if (artist) {
            const names = [normalized(row.artist), normalized(row.artistUnicode)];
            if (filters.exactArtist ? !names.includes(artist) : !names.some(v => v.includes(artist))) return false;
        }
        if (artistRomanized && !normalized(row.artist).includes(artistRomanized)) return false;
        if (sourceText && !normalized(row.sourceText).includes(sourceText)) return false;
        if (creator && !normalized(row.creator).includes(creator)) return false;
        if (filters.status && filters.status !== 'any' && row.status !== filters.status) return false;
        if (filters.genre !== '' && filters.genre != null && row.genre !== Number(filters.genre)) return false;
        if (filters.language !== '' && filters.language != null && row.language !== Number(filters.language)) return false;
        const matchingBeatmaps = row.beatmaps.filter(item =>
            (filters.mode === '' || filters.mode == null || item.mode === Number(filters.mode)) &&
            inRange(item.bpm, filters.bpmMin, filters.bpmMax) &&
            inRange(item.length, filters.lengthMin, filters.lengthMax) &&
            inRange(item.stars, filters.difficultyMin, filters.difficultyMax));
        if (!matchingBeatmaps.length) return false;
        // The website search endpoint already applies date query terms. Some
        // response shapes omit these dates, so only double-check a value when
        // the server actually returned it.
        if (row.submittedDate && !dateInRange(row.submittedDate, filters.submittedFrom, filters.submittedTo)) return false;
        if (row.updatedDate && !dateInRange(row.updatedDate, filters.updatedFrom, filters.updatedTo)) return false;
        if (row.statusChangedDate && !dateInRange(row.statusChangedDate, filters.statusChangedFrom, filters.statusChangedTo)) return false;
        return true;
    }

    function sortRecords(records, field, descending) {
        if (!field || field === 'default') return [...records];
        const firstNumber = (row, key) => {
            const values = row.beatmaps.map(item => item[key]).filter(Number.isFinite);
            return values.length ? Math.min(...values) : null;
        };
        const value = row => ({
            title: normalized(row.titleUnicode || row.title), titleRomanized: normalized(row.title),
            artist: normalized(row.artistUnicode || row.artist), artistRomanized: normalized(row.artist),
            source: normalized(row.sourceText), creator: normalized(row.creator), status: normalized(row.status),
            submitted: row.submittedDate, updated: row.updatedDate, statusChanged: row.statusChangedDate,
            mode: row.modes.length ? Math.min(...row.modes) : null, bpm: firstNumber(row, 'bpm'),
            length: firstNumber(row, 'length'), difficulty: firstNumber(row, 'stars'),
        })[field];
        const present = []; const missing = [];
        for (const row of records) (value(row) == null || value(row) === '' ? missing : present).push(row);
        present.sort((a, b) => {
            const av = value(a); const bv = value(b); const cmp = typeof av === 'number' ? av - bv : String(av).localeCompare(String(bv));
            return descending ? -cmp : cmp;
        });
        return present.concat(missing);
    }

    function downloadUrl(source, sid, noVideo) {
        if (source === 'official') return `https://osu.ppy.sh/beatmapsets/${sid}/download${noVideo ? '?noVideo=1' : ''}`;
        if (source === 'sayobot') return `https://txy1.sayobot.cn/beatmaps/download/${noVideo ? 'novideo' : 'full'}/${sid}`;
        if (source === 'nerinyan') return `https://api.nerinyan.moe/d/${sid}${noVideo ? '?nv=1' : ''}`;
        if (source === 'mino' && !noVideo) return `https://catboy.best/d/${sid}`;
        throw new Error('No verified no-video endpoint');
    }

    function delay(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }
    function escapeHtml(value) {
        return String(value ?? '').replace(/[&<>"']/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]));
    }

    function init() {
        if (typeof document === 'undefined' || document.getElementById('obw-launcher')) return;

        let state = loadState();
        let running = false;
        let searching = false;
        let stopRequested = false;
        let activeDownload = null;
        let notice = '';
        let localIds = new Set(state.localSetIds);
        let searchResults = [];
        let selectedResults = new Set();
        let resultPage = 0;
        const resultPageSize = 100;

        function defaults() {
            return {
                language: 'en',
                queue: [], source: 'official', noVideo: false, interval: 1.5,
                localSetIds: [],
                filters: {
                    artist: '', artistRomanized: '', title: '', titleRomanized: '', creator: '', sourceText: '',
                    exactArtist: true, status: 'ranked', mode: '0', genre: '', language: '',
                    bpmMin: '', bpmMax: '', lengthMin: '', lengthMax: '', difficultyMin: '', difficultyMax: '',
                    submittedFrom: '', submittedTo: '', updatedFrom: '', updatedTo: '',
                    statusChangedFrom: '', statusChangedTo: '', sortField: 'default', sortDescending: false,
                },
            };
        }

        function loadState() {
            const fallback = defaults();
            try {
                const saved = GM_getValue(STORE_KEY, null);
                if (!saved || typeof saved !== 'object') return fallback;
                return {
                    ...fallback, ...saved,
                    queue: Array.isArray(saved.queue) ? saved.queue.filter(x => Number.isInteger(x.sid)) : [],
                    localSetIds: Array.isArray(saved.localSetIds) ? saved.localSetIds.filter(x => Number.isInteger(x) && x > 0 && x < MAX_ID) : [],
                    filters: { ...fallback.filters, ...(saved.filters || {}) },
                };
            } catch (_) { return fallback; }
        }

        function saveState() { GM_setValue(STORE_KEY, state); }
        function tr(key, ...args) {
            const value = TEXT[state.language][key];
            return typeof value === 'function' ? value(...args) : value;
        }

        GM_addStyle(`
            #obw-launcher{position:fixed;right:18px;bottom:18px;z-index:2147483646;border:0;border-radius:22px;padding:11px 17px;background:#d65a9e;color:#fff;font-weight:700;box-shadow:0 5px 18px #0008;cursor:pointer}
            #obw-panel{position:fixed;right:18px;bottom:70px;z-index:2147483646;width:min(720px,calc(100vw - 24px));max-height:calc(100vh - 92px);overflow:auto;background:#202231;color:#f0eff5;border:1px solid #53576f;border-radius:12px;box-shadow:0 10px 35px #000b;font:13px/1.4 Arial,sans-serif}
            #obw-panel *{box-sizing:border-box}#obw-panel header{display:flex;align-items:center;gap:8px;position:sticky;top:0;background:#292c3e;padding:12px;z-index:2}#obw-panel h2{font-size:18px;margin:0;flex:1}
            #obw-panel button,#obw-panel select,#obw-panel input,#obw-panel textarea{background:#303449;color:#f5f4f8;border:1px solid #5c6079;border-radius:6px;padding:7px}#obw-panel button{cursor:pointer}#obw-panel button.primary{background:#b84f91;border-color:#d972b0}#obw-panel button:disabled{opacity:.5;cursor:not-allowed}
            .obw-body{padding:12px}.obw-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px}.obw-grid label{display:flex;flex-direction:column;gap:3px}.obw-grid .wide{grid-column:span 2}.obw-row{display:flex;gap:7px;align-items:center;flex-wrap:wrap;margin:9px 0}.obw-row textarea{min-height:64px;flex:1 1 360px;resize:vertical}.obw-note{color:#b9bdd0;margin:6px 0}.obw-warn{color:#f0c57a}.obw-state{min-height:20px;color:#8de0b5}.obw-advanced{margin:9px 0;border:1px solid #454a62;border-radius:7px;padding:7px}.obw-advanced summary{cursor:pointer;font-weight:700;margin-bottom:7px}
            .obw-table{width:100%;border-collapse:collapse;margin-top:8px}.obw-table th,.obw-table td{padding:6px;border-bottom:1px solid #3d4156;text-align:left}.obw-table tr.done{background:#315743}.obw-table tr.local:not(.done){background:#405b4a}.obw-table tr.failed{background:#572f3a}.obw-table a{color:#f0a5d0}.obw-results{border:1px solid #53576f;border-radius:8px;padding:8px;margin:10px 0}.obw-results h3{margin:0 0 5px;font-size:15px}.obw-result-check{width:17px;height:17px}.obw-check{flex-direction:row!important;align-items:center;margin-top:21px}.obw-count{margin-left:auto;color:#aeb2c5}a.obw-local-link{background:rgba(115,205,145,.2)!important;outline:2px solid rgba(115,205,145,.45);border-radius:4px}@media(max-width:650px){.obw-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
        `);

        const launcher = document.createElement('button');
        launcher.id = 'obw-launcher';
        launcher.type = 'button';
        launcher.textContent = tr('show');
        launcher.addEventListener('click', () => {
            const panel = document.getElementById('obw-panel');
            if (panel) panel.hidden = !panel.hidden;
        });
        document.body.appendChild(launcher);

        const panel = document.createElement('section');
        panel.id = 'obw-panel';
        document.body.appendChild(panel);

        function optionRows(rows, selected) {
            return rows.map(([value, en, zh]) => `<option value="${value}" ${String(selected) === value ? 'selected' : ''}>${escapeHtml(state.language === 'zh' ? zh : en)}</option>`).join('');
        }

        function applyLocalHighlights() {
            document.querySelectorAll('a[href*="/beatmapsets/"]').forEach(anchor => {
                if (panel.contains(anchor)) return;
                const match = anchor.href.match(/\/beatmapsets\/(\d+)/);
                anchor.classList.toggle('obw-local-link', Boolean(match && localIds.has(Number(match[1]))));
            });
        }

        function queueRow(item) {
            const label = item.status === 'done' ? tr('completed') : item.status === 'downloading' ? tr('downloading') : item.status === 'failed' ? tr('failed') : item.status === 'paused' ? tr('paused') : tr('waiting');
            const meta = [item.artist, item.title].filter(Boolean).join(' — ') || '—';
            const isLocal = localIds.has(item.sid);
            const classes = [item.status === 'done' ? 'done' : '', item.status === 'failed' ? 'failed' : '', isLocal ? 'local' : ''].filter(Boolean).join(' ');
            return `<tr class="${classes}"><td><a href="https://osu.ppy.sh/beatmapsets/${item.sid}" target="_blank" rel="noopener">${item.sid}</a></td><td title="${escapeHtml(item.message || '')}">${escapeHtml(meta)}</td><td>${isLocal ? `${escapeHtml(tr('local'))} · ` : ''}${escapeHtml(label)}</td></tr>`;
        }

        function resultRow(item) {
            const isLocal = localIds.has(item.sid);
            const meta = [item.artist, item.title].filter(Boolean).join(' — ') || '—';
            return `<tr class="${isLocal ? 'local' : ''}"><td><input class="obw-result-check" type="checkbox" data-result-id="${item.sid}" ${selectedResults.has(item.sid) ? 'checked' : ''}></td><td><a href="https://osu.ppy.sh/beatmapsets/${item.sid}" target="_blank" rel="noopener">${item.sid}</a></td><td>${escapeHtml(meta)}</td><td>${isLocal ? escapeHtml(tr('local')) : escapeHtml(item.status)}</td></tr>`;
        }

        function render() {
            launcher.textContent = tr('show');
            const f = state.filters;
            const shown = state.queue.slice(0, 300);
            const resultPages = Math.max(1, Math.ceil(searchResults.length / resultPageSize));
            resultPage = Math.max(0, Math.min(resultPage, resultPages - 1));
            const resultSlice = searchResults.slice(resultPage * resultPageSize, (resultPage + 1) * resultPageSize);
            const resultPanel = searchResults.length ? `<section class="obw-results"><h3>${tr('searchResults')}</h3>
                <div class="obw-row"><button data-action="selectAll">${tr('selectAll')}</button><button data-action="selectNone">${tr('selectNone')}</button><button data-action="addSelected" class="primary" ${selectedResults.size ? '' : 'disabled'}>${tr('addSelected')}</button><span id="obw-selected-count">${tr('selectedCount', selectedResults.size, searchResults.length)}</span></div>
                <table class="obw-table"><thead><tr><th></th><th>${tr('id')}</th><th>${tr('metadata')}</th><th>${tr('state')}</th></tr></thead><tbody>${resultSlice.map(resultRow).join('')}</tbody></table>
                <div class="obw-row"><button data-action="resultPrev" ${resultPage === 0 ? 'disabled' : ''}>${tr('previous')}</button><span>${tr('resultPage', resultPage + 1, resultPages)}</span><button data-action="resultNext" ${resultPage + 1 >= resultPages ? 'disabled' : ''}>${tr('next')}</button></div></section>` : '';
            panel.innerHTML = `
                <header><h2>${tr('title')}</h2><button data-action="lang">${tr('lang')}</button><button data-action="hide">${tr('hide')}</button></header>
                <div class="obw-body">
                    <div class="obw-grid">
                        <label>${tr('artist')}<input data-field="artist" value="${escapeHtml(f.artist)}"></label>
                        <label>${tr('titleField')}<input data-field="title" value="${escapeHtml(f.title)}"></label>
                        <label>${tr('creator')}<input data-field="creator" value="${escapeHtml(f.creator)}"></label>
                        <label class="obw-check"><input type="checkbox" data-field="exactArtist" ${f.exactArtist ? 'checked' : ''}> ${tr('exact')}</label>
                        <label>${tr('status')}<select data-field="status">${['any','ranked','approved','qualified','loved','pending','wip','graveyard'].map(v => `<option value="${v}" ${f.status === v ? 'selected' : ''}>${v === 'any' ? tr('any') : v}</option>`).join('')}</select></label>
                        <label>${tr('mode')}<select data-field="mode">${[['',tr('any')],['0','osu!'],['1','taiko'],['2','catch'],['3','mania']].map(([v,n]) => `<option value="${v}" ${String(f.mode) === v ? 'selected' : ''}>${n}</option>`).join('')}</select></label>
                        <label>${tr('genre')}<select data-field="genre">${optionRows(GENRES, f.genre)}</select></label>
                        <label>${tr('language')}<select data-field="language">${optionRows(LANGUAGES, f.language)}</select></label>
                    </div>
                    <details class="obw-advanced"><summary>${tr('advanced')}</summary><div class="obw-grid">
                        <label>${tr('artistRomanized')}<input data-field="artistRomanized" value="${escapeHtml(f.artistRomanized)}"></label>
                        <label>${tr('titleRomanized')}<input data-field="titleRomanized" value="${escapeHtml(f.titleRomanized)}"></label>
                        <label class="wide">${tr('sourceText')}<input data-field="sourceText" value="${escapeHtml(f.sourceText)}"></label>
                        <label>${tr('bpmMin')}<input data-field="bpmMin" type="number" min="0" step="0.01" value="${escapeHtml(f.bpmMin)}"></label>
                        <label>${tr('bpmMax')}<input data-field="bpmMax" type="number" min="0" step="0.01" value="${escapeHtml(f.bpmMax)}"></label>
                        <label>${tr('lengthMin')}<input data-field="lengthMin" type="number" min="0" step="1" value="${escapeHtml(f.lengthMin)}"></label>
                        <label>${tr('lengthMax')}<input data-field="lengthMax" type="number" min="0" step="1" value="${escapeHtml(f.lengthMax)}"></label>
                        <label>${tr('difficultyMin')}<input data-field="difficultyMin" type="number" min="0" step="0.01" value="${escapeHtml(f.difficultyMin)}"></label>
                        <label>${tr('difficultyMax')}<input data-field="difficultyMax" type="number" min="0" step="0.01" value="${escapeHtml(f.difficultyMax)}"></label>
                        <label>${tr('submittedFrom')}<input data-field="submittedFrom" type="date" value="${escapeHtml(f.submittedFrom)}"></label>
                        <label>${tr('submittedTo')}<input data-field="submittedTo" type="date" value="${escapeHtml(f.submittedTo)}"></label>
                        <label>${tr('updatedFrom')}<input data-field="updatedFrom" type="date" value="${escapeHtml(f.updatedFrom)}"></label>
                        <label>${tr('updatedTo')}<input data-field="updatedTo" type="date" value="${escapeHtml(f.updatedTo)}"></label>
                        <label>${tr('statusChangedFrom')}<input data-field="statusChangedFrom" type="date" value="${escapeHtml(f.statusChangedFrom)}"></label>
                        <label>${tr('statusChangedTo')}<input data-field="statusChangedTo" type="date" value="${escapeHtml(f.statusChangedTo)}"></label>
                        <label>${tr('sortField')}<select data-field="sortField">${optionRows(SORT_FIELDS, f.sortField)}</select></label>
                        <label class="obw-check"><input type="checkbox" data-field="sortDescending" ${f.sortDescending ? 'checked' : ''}> ${tr('sortDescending')}</label>
                    </div></details>
                    <div class="obw-grid">
                        <label>${tr('source')}<select data-setting="source">${Object.entries(SOURCES).map(([v,n]) => `<option value="${v}" ${state.source === v ? 'selected' : ''}>${n}</option>`).join('')}</select></label>
                        <label>${tr('interval')}<input data-setting="interval" type="number" min="1" max="60" step="0.5" value="${Number(state.interval)}"></label>
                    </div>
                    <div class="obw-row"><label><input type="checkbox" data-setting="noVideo" ${state.noVideo ? 'checked' : ''}> ${tr('noVideo')}</label><button data-action="search" class="primary" ${searching || running ? 'disabled' : ''}>${tr('search')}</button><button data-action="stopSearch" ${!searching ? 'disabled' : ''}>${tr('stopSearch')}</button></div>
                    <div class="obw-row"><textarea id="obw-input" placeholder="${tr('input')}"></textarea><button data-action="add">${tr('add')}</button><button data-action="collect">${tr('collect')}</button></div>
                    <div class="obw-row"><button data-action="start" class="primary" ${running || searching ? 'disabled' : ''}>${tr('start')}</button><button data-action="pause" ${!running ? 'disabled' : ''}>${tr('pause')}</button><button data-action="clearDone" ${running || searching ? 'disabled' : ''}>${tr('clearDone')}</button><button data-action="clearAll" ${running || searching ? 'disabled' : ''}>${tr('clearAll')}</button><span class="obw-count">${state.queue.length}</span></div>
                    <div class="obw-row"><button data-action="loadDb">${tr('loadDb')}</button><button data-action="clearDb" ${state.localSetIds.length ? '' : 'disabled'}>${tr('clearDb')}</button><span>${state.localSetIds.length ? `${state.localSetIds.length} ${tr('metadata')}` : ''}</span><input id="obw-db-file" type="file" accept=".db,application/octet-stream" hidden></div>
                    <div class="obw-note">${tr('login')} ${tr('browserLimit')}</div><div class="obw-note obw-warn">${tr('localLimit')}</div><div class="obw-state">${escapeHtml(notice)}</div>
                    ${resultPanel}
                    ${shown.length ? `<table class="obw-table"><thead><tr><th>${tr('id')}</th><th>${tr('metadata')}</th><th>${tr('state')}</th></tr></thead><tbody>${shown.map(queueRow).join('')}</tbody></table>` : `<p>${tr('queueEmpty')}</p>`}
                </div>`;
            applyLocalHighlights();
        }

        function addRecords(records) {
            const known = new Set(state.queue.map(item => item.sid));
            let count = 0;
            for (const record of records) {
                const item = typeof record === 'number' ? { sid: record } : record;
                if (known.has(item.sid)) continue;
                state.queue.push({ sid: item.sid, artist: item.artist || '', title: item.title || '', status: 'waiting', message: '' });
                known.add(item.sid); count += 1;
            }
            saveState();
            return count;
        }

        async function officialSearch() {
            if (searching) return;
            syncControls(); searching = true; stopRequested = false;
            searchResults = []; selectedResults = new Set(); resultPage = 0; render();
            const seen = new Set(); const matches = []; let cursor = null; let page = 0;
            try {
                do {
                    if (stopRequested) throw new Error(tr('stopped'));
                    page += 1; notice = tr('searching', page, matches.length); render();
                    const params = buildSearchParams(state.filters, cursor);
                    const response = await fetch(`/beatmapsets/search?${params}`, { credentials: 'include', headers: { Accept: 'application/json', 'X-Requested-With': 'XMLHttpRequest' } });
                    if (!response.ok) throw new Error(`HTTP ${response.status}`);
                    const data = await response.json();
                    if (!Array.isArray(data.beatmapsets) || !Object.prototype.hasOwnProperty.call(data, 'cursor_string')) throw new Error('Unexpected search response');
                    for (const raw of data.beatmapsets) {
                        const row = normaliseRecord(raw);
                        if (!seen.has(row.sid) && recordMatches(row, state.filters)) { seen.add(row.sid); matches.push(row); }
                    }
                    cursor = data.cursor_string;
                    if (page >= 200) throw new Error('Search stopped at the 200-page safety limit');
                    if (cursor) await delay(800);
                } while (cursor);
                searchResults = sortRecords(matches, state.filters.sortField, Boolean(state.filters.sortDescending));
                selectedResults = new Set(searchResults.map(item => item.sid));
                notice = tr('searchDone', searchResults.length);
            } catch (error) { notice = error && error.message ? error.message : String(error); }
            finally { searching = false; stopRequested = false; render(); }
        }

        function syncControls() {
            panel.querySelectorAll('[data-field]').forEach(el => {
                state.filters[el.dataset.field] = el.type === 'checkbox' ? el.checked : el.value;
            });
            panel.querySelectorAll('[data-setting]').forEach(el => {
                state[el.dataset.setting] = el.type === 'checkbox' ? el.checked : el.value;
            });
            state.interval = Math.max(1, Math.min(60, Number(state.interval) || 1.5));
            saveState();
        }

        function gmDownload(item) {
            const url = downloadUrl(state.source, item.sid, state.noVideo);
            const filename = `${item.sid}${state.noVideo ? '-novideo' : ''}.osz`;
            return new Promise((resolve, reject) => {
                const fallback = () => {
                    const frame = document.createElement('iframe');
                    frame.hidden = true; frame.src = url; document.body.appendChild(frame);
                    setTimeout(() => frame.remove(), 60000);
                    resolve(true);
                };
                const fail = error => {
                    activeDownload = null;
                    const reason = String(error && (error.details || error.error || error.message) || 'Download failed');
                    if (/not_whitelisted/i.test(reason)) fallback(); else reject(new Error(reason));
                };
                try {
                    activeDownload = GM_download({
                        url, name: filename, saveAs: false, anonymous: false,
                        headers: state.source === 'official' ? { Referer: `https://osu.ppy.sh/beatmapsets/${item.sid}` } : {},
                        onload: () => { activeDownload = null; resolve(false); },
                        onerror: fail,
                        ontimeout: () => { activeDownload = null; reject(new Error('Download timed out')); },
                    });
                } catch (error) { fail(error); }
            });
        }

        async function loadLocalDatabase(file) {
            if (!file) return;
            try {
                notice = tr('dbReading', 0, '?', 0); render();
                const parsed = await parseOsuDb(await file.arrayBuffer(), (count, total, sets) => {
                    notice = tr('dbReading', count, total, sets);
                    const output = panel.querySelector('.obw-state');
                    if (output) output.textContent = notice;
                });
                state.localSetIds = parsed.setIds.sort((a, b) => a - b);
                localIds = new Set(state.localSetIds);
                saveState();
                notice = tr('dbLoaded', parsed.setIds.length, parsed.beatmapCount, parsed.version);
            } catch (error) {
                notice = tr('dbError', error && error.message ? error.message : String(error));
            }
            render();
        }

        async function runQueue() {
            if (running) return;
            syncControls();
            if (state.noVideo && state.source === 'mino') { notice = tr('unsupportedNoVideo'); render(); return; }
            running = true; stopRequested = false;
            for (const item of state.queue) {
                if (!running || stopRequested) break;
                if (item.status === 'done') continue;
                item.status = 'downloading'; item.message = ''; saveState(); render();
                try {
                    const usedFallback = await gmDownload(item);
                    item.status = 'done';
                    if (usedFallback) item.message = tr('nativeFallback');
                }
                catch (error) { item.status = stopRequested ? 'paused' : 'failed'; item.message = error.message || String(error); }
                saveState(); render();
                if (!stopRequested) await delay(state.interval * 1000);
            }
            running = false; stopRequested = false; activeDownload = null; render();
        }

        panel.addEventListener('change', event => {
            if (event.target.matches('#obw-db-file')) loadLocalDatabase(event.target.files && event.target.files[0]);
            else if (event.target.matches('[data-result-id]')) {
                const sid = Number(event.target.dataset.resultId);
                if (event.target.checked) selectedResults.add(sid); else selectedResults.delete(sid);
                const count = panel.querySelector('#obw-selected-count');
                if (count) count.textContent = tr('selectedCount', selectedResults.size, searchResults.length);
                const addButton = panel.querySelector('button[data-action="addSelected"]');
                if (addButton) addButton.disabled = selectedResults.size === 0;
            }
            else if (event.target.matches('[data-field],[data-setting]')) syncControls();
        });
        panel.addEventListener('click', async event => {
            const button = event.target.closest('button[data-action]');
            if (!button) return;
            const action = button.dataset.action;
            if (action === 'hide') panel.hidden = true;
            else if (action === 'lang') { state.language = state.language === 'zh' ? 'en' : 'zh'; saveState(); render(); }
            else if (action === 'loadDb') panel.querySelector('#obw-db-file').click();
            else if (action === 'clearDb') {
                state.localSetIds = []; localIds = new Set(); saveState(); notice = tr('dbCleared'); render();
            }
            else if (action === 'selectAll') { selectedResults = new Set(searchResults.map(item => item.sid)); render(); }
            else if (action === 'selectNone') { selectedResults = new Set(); render(); }
            else if (action === 'addSelected') {
                const count = addRecords(searchResults.filter(item => selectedResults.has(item.sid)));
                notice = tr('added', count); render();
            }
            else if (action === 'resultPrev') { resultPage = Math.max(0, resultPage - 1); render(); }
            else if (action === 'resultNext') { resultPage += 1; render(); }
            else if (action === 'add') {
                const parsed = parseInput(panel.querySelector('#obw-input').value);
                const count = addRecords(parsed.ids);
                notice = `${tr('added', count)} ${parsed.invalid.length ? tr('invalid', parsed.invalid.length) : ''}`; render();
            } else if (action === 'collect') {
                const text = [...document.querySelectorAll('a[href*="/beatmapsets/"]')].map(a => a.href).join('\n');
                const count = addRecords(parseInput(text).ids); notice = tr('collected', count); render();
            } else if (action === 'search') await officialSearch();
            else if (action === 'stopSearch') stopRequested = true;
            else if (action === 'start') await runQueue();
            else if (action === 'pause') { stopRequested = true; running = false; if (activeDownload && typeof activeDownload.abort === 'function') activeDownload.abort(); notice = tr('stopped'); render(); }
            else if (action === 'clearDone') { state.queue = state.queue.filter(item => item.status !== 'done'); saveState(); render(); }
            else if (action === 'clearAll' && window.confirm(tr('confirmClear'))) { state.queue = []; saveState(); render(); }
        });

        GM_registerMenuCommand('osu! Batch Web', () => { panel.hidden = false; });
        render();
        let highlightTimer = null;
        new MutationObserver(() => {
            if (highlightTimer) return;
            highlightTimer = setTimeout(() => { highlightTimer = null; applyLocalHighlights(); }, 250);
        }).observe(document.body, { childList: true, subtree: true });
    }

    return { init, parseInput, normalized, parseOsuDb, buildSearchParams, normaliseRecord, recordMatches, sortRecords, downloadUrl };
});

