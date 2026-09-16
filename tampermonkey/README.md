# osu! Batch Web — Tampermonkey edition

This branch contains a browser userscript version of osu! Batch. It runs on `https://osu.ppy.sh/*` and does not replace or modify the Python/Windows application on `main`.

## Install

1. Install Tampermonkey in a supported browser.
2. Open the raw userscript URL below and choose **Install**:

   <https://raw.githubusercontent.com/Noob-Bro/Osu-Batch/tampermonkey-web/tampermonkey/osu-batch.user.js>

3. Sign in to `osu.ppy.sh`, then click the floating **osu! Batch** button.

## Features

- Chinese and English interface.
- Parse beatmapset IDs and `osu.ppy.sh/beatmapsets/...` links.
- Collect beatmapset links from the current osu! webpage.
- Search every page of the official beatmapset search endpoint by artist, title, mapper, status, and mode.
- Exact artist matching after normalising Unicode width and letter case.
- Persistent download queue, pause/resume, configurable spacing, and completed/failed states.
- Official downloads use the current browser login session; the script never asks for or stores an `osu_session` cookie.
- Optional Sayobot, Nerinyan, and Mino download sources. Mirrors are always selected explicitly.

## Important differences from the desktop build

- Browsers may ask for permission before allowing multiple downloads. Tampermonkey's download permission must be enabled.
- The userscript cannot safely provide partial-file resume, ZIP CRC validation, or verify the downloaded `.osz` contents without buffering large files in browser memory.
- Browser sandboxing prevents the userscript from reading osu!stable's `Songs` directory or osu!lazer's `client.realm`. Therefore the green local-library detection from the desktop build is intentionally unavailable.
- Queue state is Tampermonkey extension storage, not the desktop SQLite queue.
- The official website and mirror endpoints may change. Failures are shown in the queue and are not silently treated as completed.

## Development test

The pure parsing/filtering functions can be tested with Node.js:

```powershell
node --test tampermonkey/osu-batch.test.js
```

The test does not perform network downloads.

