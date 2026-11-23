#!/usr/bin/env python3
"""
StreamVerse: double tap to seek is ON by default.  python3 apply_double_tap_default.py <cloudstream-source>
  * double tap on the left / right side of the player seeks back / forward (10 s by default)
  * only the DEFAULT changes; if the user already switched it in settings, that choice is kept
"""
import pathlib
import sys

ROOT = pathlib.Path(sys.argv[1]).resolve()
P = ROOT / 'app/src/main/java/com/lagradost/cloudstream3/ui/player/PlayerGestureHelper.kt'

OLD = 'doubleTapEnabled = sm.getBoolean(context.getString(R.string.double_tap_enabled_key), false)'
NEW = 'doubleTapEnabled = sm.getBoolean(context.getString(R.string.double_tap_enabled_key), true)'

s = P.read_bytes().decode('utf-8')
if NEW in s:
    print('double tap default already ON, skipping')
elif s.count(OLD) != 1:
    raise SystemExit(f'PATCH FAILED: expected 1x double tap line, found {s.count(OLD)}x in PlayerGestureHelper.kt')
else:
    P.write_bytes(s.replace(OLD, NEW).encode('utf-8'))
    print('StreamVerse double tap default ON applied OK')
