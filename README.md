# osu! Batch Web — Batch Beatmap Downloader

**English** | [简体中文](README.zh-CN.md)

osu! Batch Web is a Tampermonkey userscript for searching, collecting and batch-downloading beatmapsets on [osu.ppy.sh](https://osu.ppy.sh/). It uses your current browser login for official downloads and lets you explicitly choose a mirror.

> [!IMPORTANT]
> **Project direction — 2026-10-24:** Future development focuses on the Web / Tampermonkey edition on `tampermonkey-web`.
> Development of the Python desktop application and its Windows executable has stopped, including new features, fixes and packaged releases. Existing source and releases remain available for reference and existing users.

## Editions

| Edition | Status | Entry point |
| --- | --- | --- |
| **Web / Tampermonkey** | **Active development**; userscript version **0.3.4** at the time of this documentation update | [Install the userscript](https://raw.githubusercontent.com/Noob-Bro/Osu-Batch/tampermonkey-web/tampermonkey/osu-batch.user.js) · [Usage details](tampermonkey/README.md) |
| Python / Windows executable | **Discontinued**; latest published desktop release is **1.1.1** | [Legacy branch and instructions](https://github.com/Noob-Bro/Osu-Batch/tree/main) · [Historical releases](https://github.com/Noob-Bro/Osu-Batch/releases) |

The Python files retained in this branch are historical desktop code. They are not required to run the userscript and are no longer a development target.

## Install and start

1. Install Tampermonkey in your browser.
2. Open the [raw userscript](https://raw.githubusercontent.com/Noob-Bro/Osu-Batch/tampermonkey-web/tampermonkey/osu-batch.user.js) and confirm installation in Tampermonkey.
3. Sign in to [osu!](https://osu.ppy.sh/home) for official search and downloads, then click the floating **osu! Batch** button.
4. Choose a download source and save method, add beatmapset links/IDs or search for maps, and click **Start / resume**.

No Python installation or Windows executable is needed. The interface starts in English and provides a Chinese switch. Keep the osu! page open while downloading.

## Search and queue

- Paste beatmapset IDs or `osu.ppy.sh/beatmapsets/...` links, or collect beatmapset links from the current webpage.
- Search all pages returned by the official beatmapset search endpoint.
- Filter by title/artist (including romanized fields), mapper, source, status, mode, genre, language, BPM, length, stars and submission/update/ranked-or-approved dates.
- Preview paginated results, select individual items or all results, then explicitly choose **Add selected**. Searching does not automatically queue downloads.
- Sort results by the supported fields in ascending or descending order.
- Keep a persistent queue in Tampermonkey storage, with **1–6 concurrent downloads** (default **3**) and configurable spacing between starts. Pause cancels active requests; starting again retries unfinished items.

### Example: Ranked + Laur + osu! standard

1. Enter `Laur` in **Artist** and enable **Exact artist**.
2. Choose `Ranked` and `osu! standard`.
3. Click **Search all pages**.
4. Review the result list, use **Select all** or select individual rows, and click **Add selected**.
5. Choose the download source and click **Start / resume**.

Exact artist matching normalizes Unicode width and case; `Laur feat. Sennzai` is not exactly `Laur`. The separate romanized artist field uses substring matching, so use **Artist** for this exact-match example. A matching set is downloaded as a whole `.osz` file, including its other difficulties/modes.

“All pages” refers to what the selected endpoint returns for that search. It is not a promise of a permanent, complete catalogue across sources; account access, search limits, synchronization delays and changing content can affect results.

## Download sources and saving

**Official** is the default download source. Official requests use the current osu! browser session; the script does not ask you to copy or save an `osu_session` Cookie. Sayobot, Nerinyan and Mino are optional download sources selected explicitly; the script does not silently switch between them. Search uses the official website regardless of the selected download mirror. No-video availability depends on the selected source.

In Edge/Chrome, **Choose folder once (recommended)** asks for a destination directory when starting. After permission is granted, the queue writes completed files there without a confirmation for each file. The folder handle lasts for the current page session; choose the folder again after a page reload. Existing same-name files in that directory can be overwritten.

**Browser downloads** is available for compatibility. Browser multiple-download permissions and Tampermonkey's download settings may still apply. If Tampermonkey reports `not_whitelisted` for `.osz`, use direct-folder mode, the native browser fallback, or allow the extension in Tampermonkey's settings.

Files use `ID Artist - Title.osz`, or `ID-novideo Artist - Title.osz`. Missing metadata is looked up before downloading; unavailable names fall back to known fields or the ID. Direct-folder downloads buffer a complete file in memory, so reduce concurrency for large beatmapsets or low-memory devices.

## Detect an existing osu!stable library

Click **Load osu!.db** and manually select your stable database, usually:

```text
%LOCALAPPDATA%\osu!\osu!.db
```

It is parsed locally in the browser and is not uploaded. BeatmapSet IDs are stored in Tampermonkey storage; matching queue entries and osu! page links are highlighted pale green. Reload `osu!.db` after installing or removing maps to refresh the index.

The script cannot silently watch `Songs`. osu!lazer's `client.realm` is not supported.

## Limits and migration from desktop

| Area | Web edition | Discontinued desktop edition |
| --- | --- | --- |
| Official session | Current browser login | Cookie supplied to the application for each run |
| Queue/settings | Tampermonkey extension storage | SQLite under `%LOCALAPPDATA%\OsuBatch` |
| Pause/resume | Resume the queue; unfinished downloads restart | Partial-file resume when the source supports it |
| Archive validation | No ZIP CRC or downloaded-content verification | CRC and `.osu` / beatmapset-ID checks |
| Local library | User-selected stable `osu!.db` | Read-only stable `Songs` scanning in desktop source |

The Web edition does not automatically import the desktop SQLite queue or settings. Add the required links/IDs again, or export desktop failed-task links and paste them into the Web queue. This documentation update does not alter existing local queues, databases or downloaded files.

Website and mirror behavior can change. This documentation update is not a new live-service compatibility test.

## Development

The maintained code is under `tampermonkey/`:

- `osu-batch.user.js` — installable userscript.
- `osu-batch.test.js` — parsing and filtering tests.
- `osu-batch.concurrent.test.js` — concurrent-queue tests.
- `README.md` — Web usage details.

Run the mock-based, offline JavaScript tests with Node.js:

```powershell
node --test tampermonkey/osu-batch.test.js tampermonkey/osu-batch.concurrent.test.js
```

Future contributions should target `tampermonkey-web` and focus on the userscript. The Python application, PyInstaller build and historical Windows releases are retained without ongoing maintenance.

## License

See [LICENSE](LICENSE). osu! Batch is independent of osu! and the mirror operators.
