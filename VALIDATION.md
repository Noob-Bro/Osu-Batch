# UI and language validation — 2026-09-16

Base: user-provided osu-batch-v1.1-advanced-filter-source.zip.

- 64 tests passed, including supplied engine/search/GUI tests, first-launch English defaults, the 1.1.1 clear-all-records regression, osu! Songs highlighting in both the download queue and filter results, and the background scan workflow.
- Regressions cover language changes preserving filter values, user text, queue progress and selection; persisted language setting; calendar accept/cancel/clear; selection preserved across sorting.
- Tests ran with QT_SCALE_FACTOR=1.5. An 800 × 600 logical-pixel search window fits, with date filters reachable by scrolling and bottom actions accessible.
- Offscreen Qt renders inspected for Chinese/English main, search, session and calendar windows. Not a manual native Windows DPI or multi-monitor certification.
- Source startup smoke test uses isolated queue data. No real cookie or authenticated live downloads used this round.
- Local-song detection reads osu!stable `Songs` folder names and `.osu` metadata to match `BeatmapSetID` values in both the download queue and filter results. It runs in the background and does not modify the library. osu!lazer storage is not scanned.
- The download/search algorithms are unchanged from the supplied archive; only the user-agent version is updated to 1.1.1. Live official/mirror network validation was not repeated.

## Defender status

The build uses PyInstaller onedir with UPX disabled. No Defender settings, exclusions or threat records changed; no files were uploaded for antivirus analysis.

The previously reported Trojan:Win32/Bearfoos.A!ml detection is unresolved. Functional tests or source execution do not establish a false-positive verdict. Microsoft submission: https://www.microsoft.com/en-us/wdsi/filesubmission

## Reproduction

Install requirements plus pytest into Python 3.12+, set QT_QPA_PLATFORM=offscreen and QT_SCALE_FACTOR=1.5, then run: python -m pytest tests -q

The ZIP excludes caches, local environments, queue databases and credentials.

