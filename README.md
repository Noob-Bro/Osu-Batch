# osu! Batch — Batch Beatmap Downloader for Windows

**English** | [简体中文](README.zh-CN.md)

> [!WARNING]
> **Security Notice**
>
> The Windows executable is packaged with PyInstaller and is not code-signed. Some security products may therefore block or flag it.
>
> **Do not disable your security software to run this program.**
>
> Verify the download source, scan the files if necessary, or review the source code and build the application yourself if you have concerns.

This repository contains the **UI fixes and Chinese/English language switching release (2026-09-09)** while retaining the advanced filtering features.

The source code is located in the repository root. The portable Windows x64 build is available from **Releases**. Extract the entire archive before running `OsuBatch.exe`.

**Running from source:** Clone or download the source code to a writable directory and double-click `start.cmd`.

Python 3.12+ is required. If dependencies are missing, the first launch creates a `.venv` directory inside the project folder and installs the required packages from PyPI. Subsequent launches do not reinstall them.

Close the previous version before upgrading. Existing queues and settings will be preserved.

**Language:** Select **中文** or **English** from the upper-right corner of the main window. The change takes effect immediately and the preference is saved.

User input, beatmap titles, and artist names remain in their original language. Filter values and download states are unaffected by the selected interface language.

---

## Batch Download by Filters

Open **Filter Search / Batch Download** from the main window.

For example:

1. Select `osu! Official` as the search source after configuring an official website session in the main window, or manually select `Sayobot` without logging in.
2. Enter `Laur` as the artist and enable **Exact Match**.
3. Select `Ranked` as the status and `osu! standard (std)` as the mode.
4. Click **Search All Pages** to view the artist, title, mapper, status, and included modes.
5. After the search finishes, click **Add All to Download Queue**, return to the main window, and click **Start / Resume**.

If downloads are already running, newly added tasks are appended to the queue automatically.

The **search source** and **download source** are independent.

For example, you may search with Sayobot and then download using the official source configured in the main window. The search source is never changed automatically.

The new version continues using the existing queue database. Close the previous version before upgrading.

### Filtering Semantics

* **Exact artist matching** ignores letter case, leading/trailing whitespace, and full-width/half-width character differences. Both the regular and Unicode artist fields are checked. `Laur feat. Sennzai` and `Laurinha Costa` do not match `Laur`.
* **Contains matching** may include collaborations and similar names such as `Laura`. Review the preview results carefully. Artist aliases are not inferred. Leaving the artist field empty disables artist filtering.
* `Ranked` strictly means `ranked`; legacy `approved` beatmaps are not included. `Approved` can be selected separately.
* Mode filtering means that the beatmapset contains at least one native difficulty for the selected mode. Mixed-mode beatmapsets may therefore match. The full `.osz` archive is still downloaded; other difficulties are not removed.
* Official cursor-based pagination and Sayobot `endid` pagination are handled separately. Results are automatically deduplicated and their artist, status, and mode fields are revalidated.
* If the official site session is missing or expired, the website may ignore filters and return a default list. The application attempts to detect this behavior and rejects such results.
* If a search is cancelled, encounters network errors, detects repeated pages, or receives fewer official results than expected, it is not marked as complete. **Add All** remains disabled, although selected partial results can still be added explicitly.
* **All** means every page provided by the selected search source during that search. Mirrors may have synchronization delays, while official search results may be affected by account blocklists, removed content, result limits, or changes that occur during the search. An absolute cross-source and cross-time complete dataset is therefore not guaranteed. New beatmaps are not appended automatically after the search finishes.
* Official searches include beatmapsets marked as NSFW to avoid silently omitting results. Only textual metadata is displayed; cover images are not shown.

---

## Quick Start

Extract the portable Windows build and run:

```text
OsuBatch.exe
```

Designed for:

* Windows 10 22H2 64-bit
* Windows 11 64-bit

This release was verified on Windows 11.

1. Select a download directory.
2. The default strategy is **Official Only**. Click **Set Official Session** and provide your own official website Cookie according to the instructions shown in the application. The session exists only for the current process.
3. Paste beatmapset URLs or IDs, or import a UTF-8 TXT file, then click **Add to Queue**.
4. Click **Start / Resume**. If you need mirrors, select an automatic fallback strategy or a mirror-only strategy.
5. When finished, drag the `.osz` files into osu!.

The application does not directly modify the `Songs` directory used by osu!stable or the internal storage used by osu!lazer.

---

## Download Source Is Controlled by the User

| Strategy                                 | Behavior                                                                                                                                                                                    |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Official Only** — default              | Downloads only from the official website and requires a valid website session                                                                                                               |
| **Official First, Then Selected Mirror** | Attempts the selected mirror when the official source fails, the session expires, or the official source becomes unavailable; if no session is configured, the mirror is attempted directly |
| **Selected Mirror Only**                 | Uses Sayobot, Nerinyan, or Mino (`catboy.best`) without sending the official website session                                                                                                |

HTTP `429` rate limits respect `Retry-After`.

Concurrent tasks using the same source share the same cooldown period. After three consecutive failures, a task is marked as failed. Rate limiting alone does not automatically switch the download source.

Default concurrency is `1`, with a maximum of `3`. New download requests are separated by approximately `1.5` seconds or more.

**No Video** is supported by:

* Official osu! download
* Sayobot
* Nerinyan

This option is disabled when using Mino. Actual availability of a no-video package depends on the selected source.

---

## Official Login Method and Limitations

The official osu! documentation states that endpoints marked `lazer` are not available to normal Authorization Code or Client Credentials OAuth applications.

For this reason, osu! Batch uses the existing authenticated web download route instead of requiring users to create an OAuth application.

The application does **not** request your osu! username or password.

### Setting an Official Session

1. Sign in to the [osu! website](https://osu.ppy.sh/home) in your own browser.
2. Open any beatmapset page.
3. Press **F12**, open **Network**, and click the official **Download** button.
4. Find the request under the `osu.ppy.sh` domain matching:

```text
/beatmapsets/<number>/download
```

5. Under **Request Headers**, copy the value of the `Cookie` header and paste it into the session window in osu! Batch.

Alternatively:

1. Open **Application → Cookies → https://osu.ppy.sh**
2. Copy the value of `osu_session`.

> [!IMPORTANT]
> Your Cookie represents your current authenticated session.
>
> **Do not share it with anyone and do not paste it into chats, issues, screenshots, or public logs.**

The Cookie is stored only in process memory.

It is not saved to:

* configuration files
* the queue database
* error messages

After closing the program, the session must be configured again.

The Cookie is sent only to:

```text
https://osu.ppy.sh:443
```

If the download redirects to a file server, the Cookie is not forwarded.

The official website may require browser verification or reject non-browser HTTP clients.

Copying a browser session does not guarantee that such protections can be bypassed, and this application does not attempt to automate those verification mechanisms.

If you receive HTTP `401` or `403`:

1. Sign in again in your browser.
2. Complete any website verification.
3. Reconfigure the session.

If the official source still does not work, you may manually choose a mirror.

The status:

```text
Session configured · Unverified
```

means only that the provided session value was accepted as input. The program does not claim that the session is valid until an actual official download succeeds.

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

* Numeric values are always interpreted as **Beatmapset IDs**.
* The entire beatmapset is downloaded.
* Different difficulty links belonging to the same beatmapset are deduplicated.
* The initial release does not resolve URLs containing only a single beatmap ID, such as `/beatmaps/123` or `/b/123`. Open the official website and copy the full URL containing `beatmapsets`.
* IDs already present in the current queue are not added again.
* To redownload a completed task, change its download directory, or switch the video option, remove the existing task record first and then add it again.
* Deduplication checks filenames generated by this tool in the configured download directory. The application does not scan your osu! song library and does not check whether the server contains a newer revision of an existing beatmapset.

---

## Pause, Resume, and Validation

* Pausing or cancelling preserves `.part` temporary files.
* Cancelled tasks do not resume automatically. Use **Retry Failed / Cancelled** to resume them.
* Closing the application stops downloads before saving the queue.
* While waiting for a network response, shutdown normally takes up to approximately 20 seconds, although multiple redirects or other network conditions may take longer.
* Resume requests are sent only when the source, beatmapset, and video option match and a usable `ETag` or `Last-Modified` value exists.
* If the server ignores `Range`, returns an inconsistent `Content-Range`, or otherwise cannot safely resume, the file is downloaded again to avoid combining data from different archive versions.
* After downloading, every ZIP entry is checked for CRC integrity.
* `.osu` files are validated.
* If a valid `BeatmapSetID` field exists, it is checked against the requested ID. Older beatmaps may lack this field, in which case ID validation cannot be performed using it.
* The temporary file is renamed to `.osz` only after validation succeeds.
* Maximum compressed archive size: **2 GiB**
* Maximum total uncompressed contents: **4 GiB**
* Archives are not extracted to disk during validation.
* If a file with the same name already exists, it is validated first. A valid file is skipped; an invalid file causes an error and the existing user file is preserved.
* Normal package filenames use:

```text
<BeatmapsetID>.osz
```

* No-video packages use:

```text
<BeatmapsetID>-novideo.osz
```

* **Remove Selected Record** removes only the queue record. It does not delete `.osz` or temporary files.
* Unneeded `.part` files and their corresponding `.json` metadata can be manually removed after closing the program.

Queue and settings are stored by default at:

```text
%LOCALAPPDATA%\OsuBatch\queue.sqlite3
```

For development and testing, another data directory can be specified with:

```text
OSU_BATCH_DATA_DIR
```

The application uses a single-instance lock to prevent multiple processes from modifying the same queue simultaneously.

---

## Running from Source

Requires Python 3.12+.

From the source directory:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

### Development Validation and Packaging

```powershell
.\.venv\Scripts\python.exe -m pip install pytest==9.1.1 pyinstaller==6.22.2
.\.venv\Scripts\python.exe -m pytest tests -q
.\.venv\Scripts\python.exe build.py
```

The portable build is generated at:

```text
dist/OsuBatch/
```

Distribute the **entire directory**, not only `OsuBatch.exe`.

The application uses PyInstaller's `onedir` layout with dynamic libraries stored separately, allowing dependency libraries to be replaced when necessary.

Third-party components remain subject to their respective licenses.

---

## Project Structure

* `app.py` — desktop UI and threaded task scheduling.
* `engine.py` — download source adapters, retries, resume support, and content validation.
* `store.py` — persistent queue and settings storage.
* `search.py` — official and Sayobot paginated search, local filtering, and search completeness validation.
* `search_dialog.py` — filtering interface, result preview, and queue insertion.
* `tests/` — tests for download failures, credential isolation, persistence, and UI workflows.
* `build.py` — Windows portable build entry point.
* `OsuBatch.spec` — PyInstaller dependency collection configuration and exclusion rules for potentially conflicting ICU dynamic libraries.

---

## API and Implementation References

Last verified: **2026-09-06**

External service behavior may change. Source-code implementation references do not guarantee that downloads will continue to work against current online services.

* [Official Authentication and API Documentation](https://osu.ppy.sh/docs/) — authorization limitations of lazer-marked endpoints.
* [Official BeatmapsetsController](https://github.com/ppy/osu-web/blob/master/app/Http/Controllers/BeatmapsetsController.php) — web downloads, `noVideo`, quotas, and redirects.
* [Official Helper Functions](https://github.com/ppy/osu-web/blob/master/app/helpers.php) — official Referer / Origin validation.
* [Nerinyan Download Service](https://github.com/Nerinyan/nerinyan-download-apiv1/blob/main/route/download/downloadBeatmapSetV2.go) — download behavior and `nv` / `noVideo` parameters.
* [Mino](https://catboy.best/) and its [API documentation](https://catboy.best/docs).
* [Sayobot](https://osu.sayobot.cn/) frontend download routes:

```text
https://txy1.sayobot.cn/beatmaps/download/full/{id}
https://txy1.sayobot.cn/beatmaps/download/novideo/{id}
```

Real online validation results and test results are documented in:

```text
VALIDATION.md
```

---

## License

See [`LICENSE`](LICENSE) for license information.
