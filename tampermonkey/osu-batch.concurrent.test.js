const test = require('node:test');
const assert = require('node:assert/strict');
const { init, runConcurrent } = require('./osu-batch.user.js');

test('worker pool respects the concurrency limit and visits each item once', async () => {
    let active = 0;
    let peak = 0;
    const visited = [];
    await runConcurrent([1, 2, 3, 4, 5, 6], 3, async item => {
        active += 1;
        peak = Math.max(peak, active);
        visited.push(item);
        await new Promise(resolve => setTimeout(resolve, 5));
        active -= 1;
    });
    assert.equal(peak, 3);
    assert.deepEqual(visited.sort((a, b) => a - b), [1, 2, 3, 4, 5, 6]);
});

test('pause aborts every active browser download and leaves unstarted items waiting', async () => {
    const original = {};
    const names = ['document', 'window', 'MutationObserver', 'GM_addStyle', 'GM_getValue', 'GM_setValue', 'GM_download', 'GM_registerMenuCommand'];
    for (const name of names) original[name] = globalThis[name];
    let clickHandler;
    let saved;
    const downloads = [];
    const panel = {
        innerHTML: '',
        addEventListener(type, handler) { if (type === 'click') clickHandler = handler; },
        querySelectorAll() { return []; },
        contains() { return false; },
    };
    try {
        globalThis.document = {
            getElementById() { return null; },
            createElement(tag) { return tag === 'section' ? panel : { addEventListener() {} }; },
            querySelectorAll() { return []; },
            body: { appendChild() {} },
        };
        globalThis.window = {};
        globalThis.MutationObserver = class { observe() {} };
        globalThis.GM_addStyle = () => {};
        globalThis.GM_getValue = () => ({
            downloadMode: 'browser', interval: 0.5, concurrency: 3,
            queue: [1, 2, 3, 4].map(sid => ({ sid, artist: 'Artist', title: `Song ${sid}`, status: 'waiting', message: '' })),
        });
        globalThis.GM_setValue = (_key, state) => { saved = structuredClone(state); };
        globalThis.GM_download = options => {
            const request = { options, aborted: false };
            downloads.push(request);
            return { abort() { request.aborted = true; } };
        };
        globalThis.GM_registerMenuCommand = () => {};
        init();
        const click = action => clickHandler({ target: { closest: () => ({ dataset: { action } }) } });
        const queueRun = click('start');
        const deadline = Date.now() + 2500;
        while (downloads.length < 3 && Date.now() < deadline) await new Promise(resolve => setTimeout(resolve, 20));
        assert.equal(downloads.length, 3);
        assert.deepEqual(saved.queue.map(item => item.status), ['downloading', 'downloading', 'downloading', 'waiting']);
        await click('pause');
        await queueRun;
        assert.equal(downloads.every(request => request.aborted), true);
        assert.deepEqual(saved.queue.map(item => item.status), ['paused', 'paused', 'paused', 'waiting']);
        assert.equal(downloads.length, 3);
    } finally {
        for (const name of names) {
            if (original[name] === undefined) delete globalThis[name];
            else globalThis[name] = original[name];
        }
    }
});

test('direct-folder mode completes one file while cancelling the other active requests', async () => {
    const names = ['document', 'window', 'MutationObserver', 'GM_addStyle', 'GM_getValue', 'GM_setValue', 'GM_xmlhttpRequest', 'GM_registerMenuCommand'];
    const original = Object.fromEntries(names.map(name => [name, globalThis[name]]));
    let clickHandler;
    let saved;
    const requests = [];
    const written = [];
    const directory = {
        name: 'Beatmaps',
        async getFileHandle(name) {
            return {
                async createWritable() {
                    return {
                        async write(blob) { written.push({ name, size: blob.size }); },
                        async close() {},
                        async abort() {},
                    };
                },
            };
        },
    };
    try {
        globalThis.document = {
            getElementById() { return null; },
            createElement(tag) {
                return tag === 'section'
                    ? { innerHTML: '', addEventListener(type, handler) { if (type === 'click') clickHandler = handler; }, querySelectorAll() { return []; }, contains() { return false; } }
                    : { addEventListener() {} };
            },
            querySelectorAll() { return []; },
            body: { appendChild() {} },
        };
        globalThis.window = { showDirectoryPicker: async () => directory };
        globalThis.MutationObserver = class { observe() {} };
        globalThis.GM_addStyle = () => {};
        globalThis.GM_getValue = () => ({
            downloadMode: 'folder', interval: 0.5, concurrency: 3,
            queue: [1, 2, 3].map(sid => ({ sid, artist: 'Artist', title: `Song ${sid}`, status: 'waiting', message: '' })),
        });
        globalThis.GM_setValue = (_key, state) => { saved = structuredClone(state); };
        globalThis.GM_xmlhttpRequest = options => {
            const request = { options, aborted: false };
            requests.push(request);
            return { abort() { request.aborted = true; } };
        };
        globalThis.GM_registerMenuCommand = () => {};
        init();
        const click = action => clickHandler({ target: { closest: () => ({ dataset: { action } }) } });
        const queueRun = click('start');
        const deadline = Date.now() + 2500;
        while (requests.length < 3 && Date.now() < deadline) await new Promise(resolve => setTimeout(resolve, 20));
        assert.equal(requests.length, 3);
        requests[0].options.onload({ status: 200, response: new Blob(['abc']), responseHeaders: 'content-type: application/octet-stream' });
        while (saved.queue[0].status !== 'done' && Date.now() < deadline) await new Promise(resolve => setTimeout(resolve, 10));
        assert.equal(saved.queue[0].status, 'done');
        assert.deepEqual(written, [{ name: '1 Artist - Song 1.osz', size: 3 }]);
        await click('pause');
        await queueRun;
        assert.deepEqual(requests.map(request => request.aborted), [false, true, true]);
        assert.deepEqual(saved.queue.map(item => item.status), ['done', 'paused', 'paused']);
    } finally {
        for (const name of names) {
            if (original[name] === undefined) delete globalThis[name];
            else globalThis[name] = original[name];
        }
    }
});
