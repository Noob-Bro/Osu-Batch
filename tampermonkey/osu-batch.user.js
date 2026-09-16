// ==UserScript==
// @name         osu! Batch Web
// @name:zh-CN   osu! Batch 网页版
// @namespace    https://github.com/Noob-Bro/Osu-Batch
// @version      0.1.0
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
    const TEXT = {
        en: {
            title: 'osu! Batch Web', hide: 'Hide', input: 'Beatmapset links or IDs', add: 'Add to queue',
            collect: 'Collect this page', search: 'Search all pages', stopSearch: 'Stop search',
            artist: 'Artist', titleField: 'Title', creator: 'Mapper', exact: 'Exact artist', status: 'Status',
            mode: 'Mode', any: 'Any', source: 'Download source', noVideo: 'No video', interval: 'Interval (s)',
            start: 'Start / resume', pause: 'Pause', clearDone: 'Clear completed', clearAll: 'Clear all',
            id: 'ID', metadata: 'Beatmapset', state: 'State', waiting: 'Waiting', downloading: 'Downloading',
            completed: 'Completed', failed: 'Failed', paused: 'Paused', queueEmpty: 'Queue is empty.',
            added: n => `Added ${n} beatmapset(s).`, invalid: n => `${n} invalid token(s) ignored.`,
            collected: n => `Collected ${n} beatmapset(s) from this page.`, searching: (p, n) => `Reading page ${p}; ${n} unique result(s).`,
            searchDone: n => `Search complete: ${n} beatmapset(s) added.`, login: 'Official download uses your current osu! website session.',
            browserLimit: 'Your browser may ask for permission to allow multiple downloads.',
            localLimit: 'Browser scripts cannot read osu!stable Songs or osu!lazer client.realm. Green local-library detection is unavailable in this web build.',
            confirmClear: 'Clear every queue record? Downloaded files will not be deleted.',
            unsupportedNoVideo: 'The selected source has no verified no-video endpoint.',
            stopped: 'Stopped.', open: 'Open', lang: '中文', show: 'osu! Batch',
        },
        zh: {
            title: 'osu! Batch 网页版', hide: '隐藏', input: '谱面集链接或 ID', add: '加入队列',
            collect: '收集当前页面', search: '搜索全部分页', stopSearch: '停止搜索',
            artist: '艺术家', titleField: '歌名', creator: '谱师', exact: '艺术家精确匹配', status: '状态',
            mode: '模式', any: '不限', source: '下载来源', noVideo: '不含视频', interval: '间隔（秒）',
            start: '开始 / 继续', pause: '暂停', clearDone: '清除已完成', clearAll: '清除全部',
            id: 'ID', metadata: '谱面集', state: '状态', waiting: '等待', downloading: '下载中',
            completed: '已完成', failed: '失败', paused: '已暂停', queueEmpty: '队列为空。',
            added: n => `已加入 ${n} 个谱面集。`, invalid: n => `已忽略 ${n} 个无效输入。`,
            collected: n => `已从当前页面收集 ${n} 个谱面集。`, searching: (p, n) => `正在读取第 ${p} 页；已有 ${n} 个不重复结果。`,
            searchDone: n => `搜索完成：加入 ${n} 个谱面集。`, login: '官方下载使用当前 osu! 网页登录会话。',
            browserLimit: '浏览器可能询问是否允许连续下载多个文件。',
            localLimit: '网页脚本无法读取 osu!stable Songs 或 osu!lazer client.realm，因此网页版不提供绿色本地曲库检测。',
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

    function cleanTerm(value, label) {
        const result = String(value || '').trim();
        if (result.length > 200 || /[\r\n"\\]/.test(result)) throw new Error(`${label}: invalid text`);
        return result;
    }

    function buildSearchParams(filters, cursor) {
        const query = [];
        const title = cleanTerm(filters.title, 'title');
        const artist = cleanTerm(filters.artist, 'artist');
        const creator = cleanTerm(filters.creator, 'creator');
        for (const value of [title, artist, creator]) if (value) query.push(`"${value}"`);
        let status = filters.status || 'any';
        // osu!web treats legacy Approved as a structured query term rather
        // than a value accepted by the `s` parameter.
        if (status === 'approved') { query.push('status=approved'); status = 'any'; }
        const params = new URLSearchParams({ q: query.join(' '), s: status, sort: 'ranked_asc', nsfw: 'true' });
        if (filters.mode !== '' && filters.mode != null) params.set('m', String(filters.mode));
        if (cursor) params.set('cursor_string', cursor);
        return params;
    }

    function normaliseRecord(raw) {
        const sid = Number(raw && raw.id);
        if (!Number.isInteger(sid) || sid <= 0 || sid >= MAX_ID) throw new Error('Invalid beatmapset ID');
        return {
            sid,
            artist: String(raw.artist || ''),
            artistUnicode: String(raw.artist_unicode || ''),
            title: String(raw.title || ''),
            titleUnicode: String(raw.title_unicode || ''),
            creator: String(raw.creator || ''),
            status: String(raw.status || ''),
            modes: [...new Set((raw.beatmaps || []).map(item => Number(item.mode_int)).filter(Number.isInteger))],
        };
    }

    function recordMatches(row, filters) {
        const title = normalized(filters.title);
        const artist = normalized(filters.artist);
        const creator = normalized(filters.creator);
        if (title && ![row.title, row.titleUnicode].some(v => normalized(v).includes(title))) return false;
        if (artist) {
            const names = [normalized(row.artist), normalized(row.artistUnicode)];
            if (filters.exactArtist ? !names.includes(artist) : !names.some(v => v.includes(artist))) return false;
        }
        if (creator && !normalized(row.creator).includes(creator)) return false;
        if (filters.status && filters.status !== 'any' && row.status !== filters.status) return false;
        if (filters.mode !== '' && filters.mode != null && !row.modes.includes(Number(filters.mode))) return false;
        return true;
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

        function defaults() {
            return {
                language: navigator.language.toLowerCase().startsWith('zh') ? 'zh' : 'en',
                queue: [], source: 'official', noVideo: false, interval: 1.5,
                filters: { artist: '', title: '', creator: '', exactArtist: true, status: 'ranked', mode: '0' },
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
            .obw-body{padding:12px}.obw-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px}.obw-grid label{display:flex;flex-direction:column;gap:3px}.obw-grid .wide{grid-column:span 2}.obw-row{display:flex;gap:7px;align-items:center;flex-wrap:wrap;margin:9px 0}.obw-row textarea{min-height:64px;flex:1 1 360px;resize:vertical}.obw-note{color:#b9bdd0;margin:6px 0}.obw-warn{color:#f0c57a}.obw-state{min-height:20px;color:#8de0b5}
            .obw-table{width:100%;border-collapse:collapse;margin-top:8px}.obw-table th,.obw-table td{padding:6px;border-bottom:1px solid #3d4156;text-align:left}.obw-table tr.done{background:#315743}.obw-table tr.failed{background:#572f3a}.obw-table a{color:#f0a5d0}.obw-check{flex-direction:row!important;align-items:center;margin-top:21px}.obw-count{margin-left:auto;color:#aeb2c5}@media(max-width:650px){.obw-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
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

        function queueRow(item) {
            const label = item.status === 'done' ? tr('completed') : item.status === 'downloading' ? tr('downloading') : item.status === 'failed' ? tr('failed') : item.status === 'paused' ? tr('paused') : tr('waiting');
            const meta = [item.artist, item.title].filter(Boolean).join(' — ') || '—';
            return `<tr class="${item.status === 'done' ? 'done' : item.status === 'failed' ? 'failed' : ''}"><td><a href="https://osu.ppy.sh/beatmapsets/${item.sid}" target="_blank" rel="noopener">${item.sid}</a></td><td title="${escapeHtml(item.message || '')}">${escapeHtml(meta)}</td><td>${escapeHtml(label)}</td></tr>`;
        }

        function render() {
            launcher.textContent = tr('show');
            const f = state.filters;
            const shown = state.queue.slice(0, 300);
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
                        <label>${tr('source')}<select data-setting="source">${Object.entries(SOURCES).map(([v,n]) => `<option value="${v}" ${state.source === v ? 'selected' : ''}>${n}</option>`).join('')}</select></label>
                        <label>${tr('interval')}<input data-setting="interval" type="number" min="1" max="60" step="0.5" value="${Number(state.interval)}"></label>
                    </div>
                    <div class="obw-row"><label><input type="checkbox" data-setting="noVideo" ${state.noVideo ? 'checked' : ''}> ${tr('noVideo')}</label><button data-action="search" class="primary" ${searching || running ? 'disabled' : ''}>${tr('search')}</button><button data-action="stopSearch" ${!searching ? 'disabled' : ''}>${tr('stopSearch')}</button></div>
                    <div class="obw-row"><textarea id="obw-input" placeholder="${tr('input')}"></textarea><button data-action="add">${tr('add')}</button><button data-action="collect">${tr('collect')}</button></div>
                    <div class="obw-row"><button data-action="start" class="primary" ${running || searching ? 'disabled' : ''}>${tr('start')}</button><button data-action="pause" ${!running ? 'disabled' : ''}>${tr('pause')}</button><button data-action="clearDone" ${running || searching ? 'disabled' : ''}>${tr('clearDone')}</button><button data-action="clearAll" ${running || searching ? 'disabled' : ''}>${tr('clearAll')}</button><span class="obw-count">${state.queue.length}</span></div>
                    <div class="obw-note">${tr('login')} ${tr('browserLimit')}</div><div class="obw-note obw-warn">${tr('localLimit')}</div><div class="obw-state">${escapeHtml(notice)}</div>
                    ${shown.length ? `<table class="obw-table"><thead><tr><th>${tr('id')}</th><th>${tr('metadata')}</th><th>${tr('state')}</th></tr></thead><tbody>${shown.map(queueRow).join('')}</tbody></table>` : `<p>${tr('queueEmpty')}</p>`}
                </div>`;
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
            syncControls(); searching = true; stopRequested = false; render();
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
                const added = addRecords(matches);
                notice = tr('searchDone', added);
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
                activeDownload = GM_download({
                    url, name: filename, saveAs: false, anonymous: false,
                    headers: state.source === 'official' ? { Referer: `https://osu.ppy.sh/beatmapsets/${item.sid}` } : {},
                    onload: () => { activeDownload = null; resolve(); },
                    onerror: error => { activeDownload = null; reject(new Error(error && (error.details || error.error) || 'Download failed')); },
                    ontimeout: () => { activeDownload = null; reject(new Error('Download timed out')); },
                });
            });
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
                try { await gmDownload(item); item.status = 'done'; }
                catch (error) { item.status = stopRequested ? 'paused' : 'failed'; item.message = error.message || String(error); }
                saveState(); render();
                if (!stopRequested) await delay(state.interval * 1000);
            }
            running = false; stopRequested = false; activeDownload = null; render();
        }

        panel.addEventListener('change', event => {
            if (event.target.matches('[data-field],[data-setting]')) syncControls();
        });
        panel.addEventListener('click', async event => {
            const button = event.target.closest('button[data-action]');
            if (!button) return;
            const action = button.dataset.action;
            if (action === 'hide') panel.hidden = true;
            else if (action === 'lang') { state.language = state.language === 'zh' ? 'en' : 'zh'; saveState(); render(); }
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
    }

    return { init, parseInput, normalized, buildSearchParams, normaliseRecord, recordMatches, downloadUrl };
});

