#!/usr/bin/env python3
"""
StreamVerse glass v3 - white-theme fixes (run AFTER apply_glass2.py):  python3 apply_glass3.py <cloudstream-source>
  * bottom bar: strong blue active indicator + white icon (readable on the white theme)
  * glass fill in light themes is a frosted periwinkle instead of near-white (pill, filter button, chips, buttons)
  * bottom sheets / dialogs follow the theme: light glass + dark text on white theme, dark glass on black theme
  * settings search pill is glass in light themes
"""
import re, sys, pathlib

ROOT = pathlib.Path(sys.argv[1]).resolve()
RES = ROOT / 'app/src/main/res'
SCREEN = ROOT / 'app/src/main/java/com/lagradost/cloudstream3/ui/settings/SettingsFragmentScreen.kt'
SHARED = ROOT / 'shared/src/commonMain/kotlin'

def read(p): return pathlib.Path(p).read_bytes().decode('utf-8')
def write(p, s): pathlib.Path(p).write_bytes(s.encode('utf-8'))
def rep(path, old, new, expect=1):
    s = read(path); k = s.count(old)
    if k != expect: raise SystemExit(f'PATCH FAILED: expected {expect}x {old[:60]!r} in {pathlib.Path(path).name}, found {k}')
    write(path, s.replace(old, new))

XML = '<?xml version="1.0" encoding="utf-8"?>\n'
SHEET = lambda corners: XML + f'''<layer-list xmlns:android="http://schemas.android.com/apk/res/android">
    <item>
        <shape android:shape="rectangle">
            {corners}
            <solid android:color="?attr/svSheetFill" />
        </shape>
    </item>
    <item>
        <shape android:shape="rectangle">
            {corners}
            <gradient android:angle="270" android:startColor="?attr/svGlassSheen" android:endColor="#08FFFFFF" />
        </shape>
    </item>
    <item>
        <shape android:shape="rectangle">
            {corners}
            <stroke android:width="1dp" android:color="?attr/svGlassEdge" />
        </shape>
    </item>
</layer-list>
'''

def main():
    if not (RES / 'values/sv_attrs.xml').exists(): raise SystemExit('run apply_glass2.py first')
    rep(RES / 'values/sv_attrs.xml', '<attr name="svGlassAccent" format="color" />',
        '<attr name="svGlassAccent" format="color" />\n    <attr name="svSheetFill" format="color" />')
    st = RES / 'values/styles.xml'
    # strong indicator so the white selected icon is readable in every theme
    rep(st, '<item name="colorSecondaryContainer">#B35B7CFF</item>', '<item name="colorSecondaryContainer">#E65B7CFF</item>')
    # dark default
    rep(st, '<item name="svGlassAccent">#B04D6BFF</item>', '<item name="svGlassAccent">#B04D6BFF</item>\n        <item name="svSheetFill">#F2141A4D</item>')
    # the two light themes
    rep(st, '<item name="svGlassFill">#D9FFFFFF</item>', '<item name="svGlassFill">#A6E1E8FF</item>', expect=2)
    rep(st, '<item name="svGlassEdge">#664B5BD8</item>', '<item name="svGlassEdge">#804B5BD8</item>', expect=2)
    rep(st, '<item name="svGlassAccent">#B39AA8FF</item>', '<item name="svGlassAccent">#B39AA8FF</item>\n        <item name="svSheetFill">#F5F4F6FF</item>', expect=2)
    # theme-aware sheets and dialogs
    write(RES / 'drawable/rounded_dialog.xml', SHEET('<corners android:topLeftRadius="26dp" android:topRightRadius="26dp" />'))
    write(RES / 'drawable/dialog__window_background.xml', SHEET('<corners android:radius="22dp" />'))
    # Compose search pill: glass in light themes
    s = read(SCREEN)
    s, k = re.subn(r'(focusedContainerColor|unfocusedContainerColor) = MaterialTheme\.colorScheme\.surfaceVariant,',
                   r'\1 = if (MaterialTheme.colorScheme.onBackground.luminance() < 0.5f) Color(0xCCFFFFFF) else MaterialTheme.colorScheme.surfaceVariant,', s)
    if k != 2: raise SystemExit('search field colours not found')
    if 'import androidx.compose.ui.graphics.luminance' not in s:
        s = re.sub(r'(^package [^\n]+\n)', r'\1\nimport androidx.compose.ui.graphics.luminance\n', s, count=1, flags=re.M)
    write(SCREEN, s)
    print('StreamVerse glass v3 applied OK')

main()
