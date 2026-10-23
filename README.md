# osu! Batch — Batch Beatmap Downloader for the Web
<img width="2172" height="724" alt="image" src="https://github.com/user-attachments/assets/a0e433f9-bb12-4c1a-a87d-6c3a28d9f125" />


**English** | [简体中文](README.zh-CN.md)

> [!WARNING]
> **Security Notice**
>
> Install the userscript from this repository and review Tampermonkey's permissions. Official downloads use your current osu! browser login; the script does not ask you to copy or store your session Cookie.
>
> **Keep your browser and security software protections enabled.**
>
> The historical Windows executable remains available from Releases, but it is no longer developed and is not needed for the Web edition.

This is **osu! Batch Web 0.3.4**, the maintained Tampermonkey edition with Chinese/English interface switching and advanced filtering.

The default and active development branch is **`tampermonkey-web`**. **Development of the Python desktop application and Windows executable stopped on 2026-10-24.** Their source remains on [`main`](https://github.com/Noob-Bro/Osu-Batch/tree/main), with [historical Releases](https://github.com/Noob-Bro/Osu-Batch/releases) retained.

**Running from source:** Install Tampermonkey, then open the [raw userscript](https://raw.githubusercontent.com/Noob-Bro/Osu-Batch/tampermonkey-web/tampermonkey/osu-batch.user.js) and confirm installation. Sign in to [osu.ppy.sh](https://osu.ppy.sh/home) and click the floating **osu! Batch** button.

The userscript is in `tampermonkey/`. No Python installation or Windows EXE is required. See [the detailed Web guide](tampermonkey/README.md) for browser and download permissions.

Queue records and settings are saved in Tampermonkey storage. They are separate from the desktop SQLite queue; add the required links/IDs again when migrating.

**Language:** A first launch defaults to **English**. Use the panel's **中文** / **English** switch; the preference is saved.

User input, beatmap titles, and artist names remain in their original language. Filter values and download states are unaffected by the interface language.

---

## Batch Download by Filters

Open the **osu! Batch** panel on the osu! website.

For example:

1. Sign in to osu!; searching uses the official website regardless of the selected download source.
2. Enter `Laur` in **Artist** and enable **Exact artist**.
3. Select `Ranked` as the status and `osu! standard` as the mode.
4. Click **Search all pages** and review the paginated results.
5. Use **Select all** or select individual rows, click **Add selected**, choose a download source, and click **Start / resume**.

Searching does not automatically add tasks. Queue controls and the selected save method apply when downloads start.

The **search source** and **download source** are independent: official search can be followed by downloads from the official source or a mirror you explicitly select.

For local-library detection, click **Load osu!.db** and manually select osu!stable's database, normally `%LOCALAPPDATA%\osu!\osu!.db`. Parsing stays in the browser and the file is not uploaded. Extracted BeatmapSet IDs persist in Tampermonkey storage and matching queue rows/page links are highlighted pale green. Reload the database after installing or removing beatmaps. The script does not silently watch `Songs` or read osu!lazer's `client.realm`.

### Filtering Semantics

* **Exact artist matching** normalizes Unicode width, case and surrounding whitespace, and checks the regular and Unicode artist fields. `Laur feat. Sennzai` and `Laurinha Costa` do not match `Laur`.
* **Contains matching** may include collaborations and similar names. The separate **Artist (romanized)** field uses substring matching; use **Artist** for the exact-match example above. Artist aliases are not inferred.
* `Ranked` strictly means `ranked`; `Approved` is a separate status.
* Mode, BPM, length and star filters must be satisfied by the same difficulty. The complete matching beatmapset is downloaded as an `.osz`; other difficulties or modes are not removed.
* Advanced filters include title/artist (and romanized fields), mapper, source, genre, language, BPM, length, difficulty and submission/update/ranked-or-approved dates. Sorting supports ascending and descending order. Dates use the official website's fields; unavailable values are not inferred.
* The userscript follows official cursor pagination and rechecks returned metadata locally. The current search has a **200-page safety limit**; narrow the filters if that limit is reached.
* A failed or cancelled search is reported in the panel. It is not a successful full search; search again before selecting results.
* **All pages** means the pages the official endpoint returns for that search. Access restrictions, result limits and changing content can affect results; this is not a permanent or cross-source guarantee of completeness.
* Searches request NSFW-tagged beatmapsets as well. The panel displays text metadata without cover images.

---


## Quick Start

Install Tampermonkey, then open the raw userscript:

```text
https://raw.githubusercontent.com/Noob-Bro/Osu-Batch/tampermonkey-web/tampermonkey/osu-batch.user.js
```

Recommended for direct-folder saving:

* Edge or Chrome with Tampermonkey
* A browser that supports directory selection; use **Browser downloads** otherwise

1. Sign in to osu! and open the floating **osu! Batch** panel.
2. Choose a source. **osu! official** is the default; mirrors are selected manually.
3. Paste beatmapset links/IDs, collect links from the current page, or search and add selected results.
4. Click **Start / resume**. In direct-folder mode, select a download directory once; browser-download mode may ask for multiple-download permission.
5. Keep the page open while downloading, then drag completed `.osz` files into osu!.

The selected directory handle lasts for the current page session. Choose it again after reloading the page. The userscript does not automatically import files into stable or lazer.

---


## Download Source Is Controlled by the User

| Source | Behavior |
| --- | --- |
| **osu! official** — default | Uses the current browser login and official web download route |
| **Sayobot / Nerinyan / Mino** | Uses the mirror explicitly selected by the user |
| **Source changes** | Change the selected source yourself; the script does not silently fall back to a mirror |

Search uses the official endpoint independently of the download source.

Default concurrency is **3**, adjustable from **1 to 6**. The default interval between new starts is **1.5 seconds**, and can be changed in the panel. If a service rate-limits requests, pause, wait and reduce concurrency or increase spacing; do not assume the desktop retry/cooldown behavior exists in the userscript.

**No video** is supported by:

* Official osu! downloads
* Sayobot
* Nerinyan

Mino has no verified no-video endpoint in this script. Actual package availability depends on the source.

In **Choose folder once** mode, complete files are buffered before saving and existing same-name files can be overwritten. More concurrency uses more memory. **Browser downloads** remains available for compatibility.

---


## Official Login Method and Limitations

The userscript runs on `https://osu.ppy.sh/*` and uses the existing authenticated web search/download routes.

It does not require an OAuth application, an osu! password, or a manually pasted Cookie.

### Setting an Official Session

1. Sign in to the [osu! website](https://osu.ppy.sh/home) in your browser.
2. Complete any verification required by the website.
3. Open the **osu! Batch** panel and select the official download source.

> [!IMPORTANT]
> Your login session remains managed by the browser.
>
> **Do not paste session Cookies into chats, issues, screenshots or public logs.**

The script does not copy your `osu_session` value into its settings. Website requests use the current login, while mirror downloads do not require you to provide your official session.

If official requests are denied, sign in again and complete website verification, or manually select a download mirror. A mirror does not replace the official search endpoint.

Tampermonkey must permit the script's declared network/download operations. Numbered official file hosts are covered by the `ppy.sh` connection declaration.

---


## Input Formats

Supported examples:

```text
https://osu.ppy.sh/beatmapsets/123456#osu/789012
https://osu.ppy.sh/s/234567
345678
456789, 567890
```

Rules:

* Numeric values are **Beatmapset IDs** and downloads contain the entire set.
* Duplicate IDs in the queue are not added again.
* Single-difficulty URLs such as `/beatmaps/123` or `/b/123` are not resolved; use a beatmapset URL.
* **Collect this page** gathers beatmapset links from the current osu! webpage.
* Search results are previewed before you explicitly add selected records.
* Existing-library markers use the manually loaded stable `osu!.db` index. They do not prove a downloaded file is current or trigger an automatic scan of local files.

---


## Pause, Resume, and Validation

* **Pause** cancels active requests. **Start / resume** retries unfinished queue items; partial-file resume is not implemented.
* Queue state is saved in Tampermonkey storage. It is separate from the desktop SQLite queue and does not migrate that queue automatically.
* Keep the osu! page open during downloads. The selected directory is not retained across page reloads.
* The userscript does **not** implement ZIP CRC validation or verify the downloaded archive's `.osu` content / beatmapset ID. The historical desktop validation and size limits do not apply.
* Direct-folder mode buffers each complete download in memory before writing it. Lower concurrency when downloading large files.
* Existing files in the chosen directory can be overwritten when names match. Browser-download filename handling depends on the browser.
* Normal package filenames use:

```text
<BeatmapsetID> <Artist> - <Title>.osz
```

* No-video packages use:

```text
<BeatmapsetID>-novideo <Artist> - <Title>.osz
```

* For link/ID-only tasks, missing names are looked up before downloading; if unavailable, filenames use the known fields or ID. Invalid Windows filename characters are replaced and long names shortened.
* **Clear completed** removes completed queue records. **Clear all** asks for confirmation before clearing records. These actions do not delete downloaded files.
* **Browser downloads** may require multiple-download permission. If Tampermonkey reports `not_whitelisted` for `.osz`, use direct-folder mode, the native browser fallback, or permit `osz` in Tampermonkey's download settings.
* Native browser fallback starts a browser download; check the browser's download list for its final outcome.
* The local-library index stays in Tampermonkey storage until cleared or reloaded. The selected `osu!.db` is parsed locally and is not uploaded.

---


## Running from Source

The complete userscript is:

```text
tampermonkey/osu-batch.user.js
```

Open the [raw script](https://raw.githubusercontent.com/Noob-Bro/Osu-Batch/tampermonkey-web/tampermonkey/osu-batch.user.js) to install it, or copy its contents into a new Tampermonkey script. No Python environment or executable build is required.

### Development Validation and Packaging

Run the JavaScript tests with Node.js:

```powershell
node --test tampermonkey/osu-batch.test.js tampermonkey/osu-batch.concurrent.test.js
```

Tests mock download behavior and do not access live services. Distribute `osu-batch.user.js` as the userscript; keep its metadata and branch-specific update/download URLs intact.

The Python application, build files and desktop validation documents are retained on [`main`](https://github.com/Noob-Bro/Osu-Batch/tree/main), rather than in this Web branch. They are no longer maintained.

---


## Project Structure

* `tampermonkey/osu-batch.user.js` — userscript UI, filtering, local database parsing and download queue.
* `tampermonkey/osu-batch.test.js` — parsing and filtering tests.
* `tampermonkey/osu-batch.concurrent.test.js` — concurrent-queue and download tests.
* [`tampermonkey/README.md`](tampermonkey/README.md) — detailed Web usage instructions.
* `README.md` / `README.zh-CN.md` — English and Simplified Chinese project introductions.
* [`LICENSE`](LICENSE) — application license.

---


## API and Implementation References

Documentation updated: **2026-10-24**. This update is not a new live-service compatibility test.

External service behavior can change. The current userscript is the source of truth for implemented routes and limitations.

* [Official authentication and API documentation](https://osu.ppy.sh/docs/).
* [Official BeatmapsetsController](https://github.com/ppy/osu-web/blob/master/app/Http/Controllers/BeatmapsetsController.php) — web search/download implementation.
* [Nerinyan download service](https://github.com/Nerinyan/nerinyan-download-apiv1/blob/main/route/download/downloadBeatmapSetV2.go).
* [Mino](https://catboy.best/) and its [API documentation](https://catboy.best/docs).
* [Sayobot](https://osu.sayobot.cn/) download routes:

```text
https://txy1.sayobot.cn/beatmaps/download/full/{id}
https://txy1.sayobot.cn/beatmaps/download/novideo/{id}
```

Implementation and offline tests:

* [Userscript](tampermonkey/osu-batch.user.js)
* [Parsing/filtering tests](tampermonkey/osu-batch.test.js)
* [Concurrent-queue tests](tampermonkey/osu-batch.concurrent.test.js)

Historical Python/Windows validation documents remain on [`main`](https://github.com/Noob-Bro/Osu-Batch/tree/main); they do not certify this Web edition.

---


## License

See [`LICENSE`](LICENSE) for license information.
