#!/usr/bin/env python3
"""
StreamVerse fix 4 (run AFTER the other patches):  python3 apply_fix4.py <cloudstream-source>
  * poster cards: when an item has no title, the empty 2-line title area under the poster is hidden
    (the card now wraps just the poster, so there is no empty framed space)
  * bottom bar: the selected tab lights up RED (white icon) in the white and the black theme
"""
import sys, pathlib

ROOT = pathlib.Path(sys.argv[1]).resolve()
RES = ROOT / 'app/src/main/res'
SRB = ROOT / 'app/src/main/java/com/lagradost/cloudstream3/ui/search/SearchResultBuilder.kt'

def read(p): return pathlib.Path(p).read_bytes().decode('utf-8')
def write(p, s): pathlib.Path(p).write_bytes(s.encode('utf-8'))
def rep(path, old, new, expect=1):
    s = read(path); k = s.count(old)
    if k != expect: raise SystemExit(f'PATCH FAILED: expected {expect}x {old[:60]!r} in {pathlib.Path(path).name}, found {k}')
    write(path, s.replace(old, new))

def main():
    rep(SRB, 'cardText?.isVisible = showTitle', 'cardText?.isVisible = showTitle && card.name.isNotBlank()')
    rep(RES / 'values/styles.xml', '<item name="colorSecondaryContainer">#E65B7CFF</item>', '<item name="colorSecondaryContainer">#E6E53935</item>')
    print('StreamVerse fix 4 applied OK')

main()
