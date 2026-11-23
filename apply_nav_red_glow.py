#!/usr/bin/env python3
"""
StreamVerse: bottom bar red glow (run AFTER apply_fix4.py):  python3 apply_nav_red_glow.py <cloudstream-source>
  * selected tab: red icon on a soft translucent red "glow" pill (like the YouTube-style reference)
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(sys.argv[1]).resolve()
RES = ROOT / 'app/src/main/res'

GLOW = '#40E53935'   # soft red glow behind the selected icon
ICON = '#FFE53935'   # red selected icon

IND = re.compile(r'<item name="colorSecondaryContainer">#[0-9A-Fa-f]+</item>')
ONC = re.compile(r'<item name="colorOnSecondaryContainer">[^<]*</item>')


def patch(path):
    s = pathlib.Path(path).read_bytes().decode('utf-8')
    hits = list(IND.finditer(s))
    if not hits:
        return 0
    for m in reversed(hits):
        start = s.rfind('<style', 0, m.start())
        end = s.find('</style>', m.end())
        if start < 0 or end < 0:
            raise SystemExit(f'PATCH FAILED: no enclosing <style> in {path}')
        block = s[start:end]
        block = IND.sub(f'<item name="colorSecondaryContainer">{GLOW}</item>', block)
        if ONC.search(block):
            block = ONC.sub(f'<item name="colorOnSecondaryContainer">{ICON}</item>', block)
        else:
            block = block.replace(
                f'<item name="colorSecondaryContainer">{GLOW}</item>',
                f'<item name="colorSecondaryContainer">{GLOW}</item>\n        <item name="colorOnSecondaryContainer">{ICON}</item>', 1)
        s = s[:start] + block + s[end:]
    pathlib.Path(path).write_bytes(s.encode('utf-8'))
    return len(hits)


def main():
    total = 0
    for f in RES.glob('values*/styles.xml'):
        total += patch(f)
    if total == 0:
        raise SystemExit('PATCH FAILED: colorSecondaryContainer not found (run apply_fix4.py first)')
    print(f'StreamVerse nav red glow applied OK ({total} theme(s))')


main()
