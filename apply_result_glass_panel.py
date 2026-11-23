#!/usr/bin/env python3
"""
StreamVerse: result (movie / series) page glass panel.  Run LAST:  python3 apply_result_glass_panel.py <cloudstream-source>
  * the solid black box behind title / Play / Resume / Download becomes a theme-aware glass panel
    (dark glass in dark themes, white glass in light themes), so the glass buttons really look like glass
  * the panel fills the whole page, so there is no black block followed by an empty wallpaper area
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(sys.argv[1]).resolve()
RES = ROOT / 'app/src/main/res'
LAYOUT = RES / 'layout/fragment_result.xml'
PANEL = RES / 'drawable/sv_glass_panel.xml'

PANEL_XML = '''<?xml version="1.0" encoding="utf-8"?>
<layer-list xmlns:android="http://schemas.android.com/apk/res/android">
    <item><shape android:shape="rectangle"><solid android:color="?attr/svGlassFill" /></shape></item>
    <item><shape android:shape="rectangle">
        <gradient android:angle="270" android:startColor="?attr/svGlassSheen" android:endColor="#00FFFFFF" /></shape></item>
</layer-list>
'''


def set_attr(tag, name, value):
    pat = re.compile(r'android:%s="[^"]*"' % re.escape(name))
    if pat.search(tag):
        return pat.sub(f'android:{name}="{value}"', tag, count=1)
    return tag[:-1].rstrip() + f'\n    android:{name}="{value}">'


def main():
    if not (RES / 'drawable/sv_glass_nav.xml').exists():
        raise SystemExit('PATCH FAILED: run the glass patches (apply_glass2.py) first')
    s = LAYOUT.read_bytes().decode('utf-8').replace('\r\n', '\n')
    if 'sv_glass_panel' in s:
        print('result page already patched, skipping')
        return

    m = re.search(r'<androidx\.core\.widget\.NestedScrollView[^>]*android:id="@\+id/result_scroll"[^>]*>', s)
    if not m:
        raise SystemExit('PATCH FAILED: result_scroll not found in fragment_result.xml')
    scroll = m.group(0)
    new_scroll = scroll
    new_scroll = set_attr(new_scroll, 'layout_height', '0dp')
    new_scroll = set_attr(new_scroll, 'layout_weight', '1')
    new_scroll = set_attr(new_scroll, 'fillViewport', 'true')
    new_scroll = re.sub(r'\s*android:paddingBottom="[^"]*"', '', new_scroll, count=1)

    m2 = re.compile(r'<LinearLayout[^>]*>').search(s, m.end())
    if not m2:
        raise SystemExit('PATCH FAILED: content layout not found under result_scroll')
    inner = m2.group(0)
    new_inner = set_attr(inner, 'background', '@drawable/sv_glass_panel')
    new_inner = set_attr(new_inner, 'paddingBottom', '100dp')

    s = s[:m.start()] + new_scroll + s[m.end():m2.start()] + new_inner + s[m2.end():]
    LAYOUT.write_bytes(s.encode('utf-8'))
    PANEL.write_bytes(PANEL_XML.encode('utf-8'))
    print('StreamVerse result glass panel applied OK')


main()
