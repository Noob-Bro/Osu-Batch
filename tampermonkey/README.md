# osu! Batch Web — Tampermonkey edition

This branch contains a browser userscript version of osu! Batch. It runs on `https://osu.ppy.sh/*` and does not replace or modify the Python/Windows application on `main`.

## Install

1. Install Tampermonkey in a supported browser.
2. Open the raw userscript URL below and choose **Install**:

   <https://raw.githubusercontent.com/Noob-Bro/Osu-Batch/tampermonkey-web/tampermonkey/osu-batch.user.js>

3. Sign in to `osu.ppy.sh`, then click the floating **osu! Batch** button.

## Features

- English is the initial interface language, with a one-click Chinese switch.
- Parse beatmapset IDs and `osu.ppy.sh/beatmapsets/...` links.
- Collect beatmapset links from the current osu! webpage.
- Search every page of the official beatmapset search endpoint.
- Desktop-style filters for artist/title (including romanized fields), mapper, source, status, mode, genre, language, BPM, length, star difficulty, submission/update/ranked-or-approved dates, and ascending/descending sorting.
- Paginated search results with individual checkboxes, select-all/select-none, and an explicit **Add selected** action. Searching no longer adds every result directly to the download queue.
- Exact artist matching after normalising Unicode width and letter case.
- Import osu!stable's `osu!.db` locally and detect installed beatmapsets by BeatmapSet ID. Matching rows in the queue and links on osu! webpages are highlighted pale green.
- Persistent download queue, pause/resume, configurable spacing, and completed/failed states.
- Official downloads use the current browser login session; the script never asks for or stores an `osu_session` cookie.
- Optional Sayobot, Nerinyan, and Mino download sources. Mirrors are always selected explicitly.

## Local osu!stable library detection

Click **Load osu!.db**, then select the stable database. Its usual location is:

```text
%LOCALAPPDATA%\osu!\osu!.db
```

The browser requires this explicit file selection and cannot silently open that path. Parsing happens entirely inside the browser tab; the database is not uploaded. The extracted BeatmapSet IDs are kept in Tampermonkey storage so the green markers remain available after a refresh. Reload the file after installing or deleting beatmaps to refresh the index.

## Important differences from the desktop build

- Browsers may ask for permission before allowing multiple downloads. Tampermonkey's download permission must be enabled.
- Some Tampermonkey configurations reject the `.osz` extension with `not_whitelisted`. Version 0.2.1 automatically retries those cases through the browser's native download path. Adding `osz` to Tampermonkey's download file-extension whitelist remains the most reliable option for very large batches.
- The userscript cannot safely provide partial-file resume, ZIP CRC validation, or verify the downloaded `.osz` contents without buffering large files in browser memory.
- osu!stable is supported through user-selected `osu!.db`. The script still cannot silently watch the `Songs` directory, and osu!lazer's `client.realm` is not supported yet.
- Queue state is Tampermonkey extension storage, not the desktop SQLite queue.
- The official website and mirror endpoints may change. Failures are shown in the queue and are not silently treated as completed.

## Development test

The pure parsing/filtering functions can be tested with Node.js:

```powershell
node --test tampermonkey/osu-batch.test.js
```

The test does not perform network downloads.

