#!/usr/bin/env python3
"""
StreamVerse glass v2 (run AFTER apply.py, apply_glass.py, apply_remove.py):  python3 apply_glass2.py <cloudstream-source>
  * theme-aware glass: dark themes get the vivid wallpaper + dark glass, light themes get a pastel wallpaper + white glass
  * wallpaper shows in EVERY theme (opaque page backgrounds made transparent)
  * bottom bar is a compact floating pill (no longer stretched over the system bar)
  * Play Movie / Download buttons, filter FAB and chips are glass and readable in light and dark
  * settings dialogs are solid again (they were see-through); settings cards adapt to light/dark
"""
import re, sys, pathlib
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = pathlib.Path(sys.argv[1]).resolve()
MAIN = ROOT / 'app/src/main'
RES = MAIN / 'res'
KT = MAIN / 'java/com/lagradost/cloudstream3'
SHARED = ROOT / 'shared/src/commonMain/kotlin'

def read(p): return pathlib.Path(p).read_bytes().decode('utf-8')
def write(p, s):
    p = pathlib.Path(p); p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(s.encode('utf-8'))
def sub(path, pattern, repl, count=1, flags=0, expect=None):
    s = read(path); n, k = re.subn(pattern, repl, s, count=count, flags=flags)
    if k == 0 or (expect is not None and k != expect):
        raise SystemExit(f'PATCH FAILED: {pattern[:80]!r} matched {k}x in {pathlib.Path(path).name}')
    write(path, n)
def lit(path, old, new):
    s = read(path)
    if old not in s: raise SystemExit(f'PATCH FAILED: text not found in {pathlib.Path(path).name}: {old[:70]!r}')
    write(path, s.replace(old, new, 1))
def add_imports(path, imports):
    s = read(path)
    for imp in imports:
        line = f'import {imp}'
        if line in s: continue
        s = re.sub(r'(^package [^\n]+\n)', r'\1\n' + line + '\n', s, count=1, flags=re.M)
    write(path, s)

# ------------------------------------------------------------------ light wallpaper (pastel liquid glass)
def bezier(p0, p1, p2, p3, n=120):
    t = np.linspace(0, 1, n)[:, None]; p0, p1, p2, p3 = map(np.array, (p0, p1, p2, p3))
    return ((1-t)**3*p0 + 3*(1-t)**2*t*p1 + 3*(1-t)*t**2*p2 + t**3*p3)

def make_light_wallpaper(path, W=810, H=1800, seed=11):
    rng = np.random.default_rng(seed)
    y = np.linspace(0, 1, H)[:, None, None]
    img = np.repeat(np.array([208, 216, 252])*(1-y) + np.array([226, 212, 252])*y, W, axis=1).astype(np.float32)
    def over(img, color, draw_fn, blur, strength=1.0):
        im = Image.new('RGBA', (W, H), tuple(color) + (0,)); d = ImageDraw.Draw(im); draw_fn(d, tuple(color))
        a = np.asarray(im.filter(ImageFilter.GaussianBlur(blur))).astype(np.float32)[..., 3:4]/255.0*strength
        return img*(1-a) + np.array(color, dtype=np.float32)*a
    left = bezier((0.30*W, 1.05*H), (0.55*W, 0.78*H), (0.40*W, 0.40*H), (0.78*W, -0.05*H))
    poly = [tuple(p) for p in left] + [(1.2*W, -0.1*H), (1.2*W, 1.1*H)]
    img = over(img, (120, 196, 255), lambda d, c: d.polygon(poly, fill=c + (255,)), 75, 0.95)
    inner = bezier((0.50*W, 1.05*H), (0.75*W, 0.80*H), (0.65*W, 0.45*H), (0.95*W, 0.02*H))
    poly2 = [tuple(p) for p in inner] + [(1.3*W, 0), (1.3*W, 1.1*H)]
    img = over(img, (150, 160, 255), lambda d, c: d.polygon(poly2, fill=c + (255,)), 85, 0.85)
    img = over(img, (236, 150, 240), lambda d, c: d.line([tuple(p) for p in left], fill=c + (255,), width=int(0.13*W), joint='curve'), 38, 0.9)
    sw = bezier((-0.2*W, 0.10*H), (0.3*W, 0.02*H), (0.5*W, 0.22*H), (0.9*W, 0.12*H))
    img = over(img, (186, 160, 255), lambda d, c: d.line([tuple(p) for p in sw], fill=c + (255,), width=int(0.20*W), joint='curve'), 60, 0.8)
    img = over(img, (255, 170, 226), lambda d, c: d.ellipse((0.55*W, 0.78*H, 1.35*W, 1.15*H), fill=c + (255,)), 90, 0.85)
    img = over(img, (150, 226, 255), lambda d, c: d.ellipse((-0.4*W, 0.72*H, 0.35*W, 1.1*H), fill=c + (255,)), 90, 0.85)
    img = over(img, (255, 214, 240), lambda d, c: d.ellipse((-0.5*W, 0.18*H, 0.6*W, 0.62*H), fill=c + (255,)), 110, 0.7)
    img += rng.normal(0, 1.4, img.shape)
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(path, 'WEBP', quality=90, method=6)

XML = '<?xml version="1.0" encoding="utf-8"?>\n'
FILES = {
 'values/sv_attrs.xml': XML + '''<resources>
    <attr name="svWallpaper" format="reference" />
    <attr name="svGlassFill" format="color" />
    <attr name="svGlassSheen" format="color" />
    <attr name="svGlassEdge" format="color" />
    <attr name="svGlassAccent" format="color" />
</resources>
''',
 'drawable/sv_glass_bg_light.xml': XML + '<bitmap xmlns:android="http://schemas.android.com/apk/res/android"\n    android:src="@drawable/sv_wallpaper_light"\n    android:gravity="fill" />\n',
 # floating pill: fill / sheen / edge all come from the active theme (dark or light)
 'drawable/sv_glass_nav.xml': XML + '''<layer-list xmlns:android="http://schemas.android.com/apk/res/android">
    <item><shape android:shape="rectangle"><corners android:radius="40dp" /><solid android:color="?attr/svGlassFill" /></shape></item>
    <item><shape android:shape="rectangle"><corners android:radius="40dp" />
        <gradient android:angle="270" android:startColor="?attr/svGlassSheen" android:endColor="#00FFFFFF" /></shape></item>
    <item><shape android:shape="rectangle"><corners android:radius="40dp" />
        <stroke android:width="1dp" android:color="?attr/svGlassEdge" /></shape></item>
</layer-list>
''',
 'drawable/sv_glass_outline.xml': XML + '''<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle">
    <corners android:radius="50dp" />
    <stroke android:width="1dp" android:color="?attr/svGlassEdge" />
</shape>
''',
 # unselected icons follow the theme text colour (white on dark, dark on light); selected icon is white on the blue glow
 'color/item_select_color.xml': XML + '''<selector xmlns:android="http://schemas.android.com/apk/res/android">
    <item android:color="#FFFFFFFF" android:state_checked="true" />
    <item android:color="#FFFFFFFF" android:state_focused="true" />
    <item android:color="#FFFFFFFF" android:state_selected="true" />
    <item android:color="?attr/textColor" android:alpha="0.8" />
</selector>
''',
 'color/chip_color.xml': XML + '''<selector xmlns:android="http://schemas.android.com/apk/res/android">
    <item android:color="?attr/colorPrimary" android:state_checked="true"/>
    <item android:color="?attr/svGlassFill" android:state_checked="false"/>
</selector>
''',
}

def main():
    if not (RES / 'drawable/sv_glass_nav.xml').exists(): raise SystemExit('run apply.py and apply_glass.py first')
    make_light_wallpaper(str(RES / 'drawable-nodpi/sv_wallpaper_light.webp'))
    for rel, content in FILES.items(): write(RES / rel, content)

    # ---- theme values: dark default in AppTheme, light override in the two light themes
    st = RES / 'values/styles.xml'
    lit(st, '<item name="colorSecondaryContainer">#B35B7CFF</item>', '''<item name="colorSecondaryContainer">#B35B7CFF</item>
        <item name="svWallpaper">@drawable/sv_glass_bg</item>
        <item name="svGlassFill">#8C141A4D</item>
        <item name="svGlassSheen">#38FFFFFF</item>
        <item name="svGlassEdge">#8CFFFFFF</item>
        <item name="svGlassAccent">#B04D6BFF</item>''')
    light = '''\\g<1>
        <item name="svWallpaper">@drawable/sv_glass_bg_light</item>
        <item name="svGlassFill">#D9FFFFFF</item>
        <item name="svGlassSheen">#99FFFFFF</item>
        <item name="svGlassEdge">#664B5BD8</item>
        <item name="svGlassAccent">#B39AA8FF</item>'''
    for theme in ('LightMode', 'LavenderMode'):
        sub(st, r'(<style name="%s"[^>]*>)' % theme, light)

    # ---- glass buttons / FAB: colours come from the theme so they stay readable in light and dark
    s = read(st)
    m = re.search(r'<style name="BlackButton" parent="NiceButton">.*?</style>', s, re.S); blk = m.group(0)
    blk2 = blk.replace('#2EFFFFFF', '?attr/svGlassFill').replace('#66FFFFFF', '?attr/svGlassEdge')
    if blk2 == blk: raise SystemExit('BlackButton glass colours not found')
    s = s[:m.start()] + blk2 + s[m.end():]
    s = s.replace('<item name="backgroundTint">#755B7CFF</item>', '<item name="backgroundTint">?attr/svGlassAccent</item>', 1)
    s = s.replace('<item name="strokeColor">#99FFFFFF</item>', '<item name="strokeColor">?attr/svGlassEdge</item>', 1)
    m = re.search(r'<style name="ExtendedFloatingActionButton">.*?</style>', s, re.S); fab = m.group(0)
    fab2 = fab.replace('<item name="backgroundTint">?attr/primaryGrayBackground</item>', '<item name="backgroundTint">?attr/svGlassFill</item>')
    fab2 = fab2.replace('<item name="textColor">?attr/colorPrimary</item>', '<item name="textColor">?attr/textColor</item>')
    fab2 = fab2.replace('<item name="elevation">0dp</item>', '''<item name="elevation">0dp</item>
        <item name="shapeAppearance">@style/ShapeAppearance.Material3.Corner.Full</item>
        <item name="android:foreground">@drawable/sv_glass_outline</item>''')
    if fab2 == fab: raise SystemExit('FAB style not patched')
    s = s[:m.start()] + fab2 + s[m.end():]
    write(st, s)

    # ---- wallpaper behind every screen, whatever the theme; opaque page roots -> transparent
    sub(RES / 'layout/activity_main.xml', r'(<FrameLayout)(\s)', r'\1\n    android:background="?attr/svWallpaper"\2')
    for lay in ['fragment_child_downloads', 'fragment_downloads', 'fragment_extensions', 'fragment_library', 'fragment_plugins',
                'fragment_search', 'fragment_testing', 'home_scroll_view', 'settings_title_top']:
        p = RES / f'layout/{lay}.xml'; t = read(p)
        m = re.search(r'<(?![?!])[\w.]+[^>]*>', t); tag = m.group(0)
        if 'android:background="?attr/primaryGrayBackground"' not in tag: continue
        write(p, t[:m.start()] + tag.replace('android:background="?attr/primaryGrayBackground"', 'android:background="@color/transparent"', 1) + t[m.end():])

    # ---- bottom bar: compact floating pill (lift by the system-bar inset instead of stretching/padding the pill)
    lit(MAIN / 'java/com/lagradost/cloudstream3/MainActivity.kt', '''            fixSystemBarsPadding(
                navView,
                heightResId = R.dimen.nav_view_height,
                padTop = false,
                overlayCutout = false
            )''', '''            // StreamVerse: floating glass pill, lifted above the system bar instead of stretched over it
            androidx.core.view.ViewCompat.setOnApplyWindowInsetsListener(navView) { view, windowInsets ->
                if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.R) {
                    val bars = windowInsets.getInsets(androidx.core.view.WindowInsetsCompat.Type.systemBars())
                    (view.layoutParams as? android.view.ViewGroup.MarginLayoutParams)?.let { lp ->
                        lp.bottomMargin = (10 * view.resources.displayMetrics.density).toInt() + bars.bottom
                        view.layoutParams = lp
                    }
                }
                androidx.core.view.WindowInsetsCompat.CONSUMED
            }''')

    # ---- Compose: solid dialogs, theme-aware cards, transparent page in light themes too
    for f in ('Dialog.kt', 'ColorDialog.kt'):
        sub(SHARED / 'com/lagradost/cloudstream4/compose' / f, r'containerColor(: Color)? = MaterialTheme\.colorScheme\.background',
            r'containerColor\1 = MaterialTheme.colorScheme.surface', count=0)
    lit(SHARED / 'com/lagradost/cloudstream4/theme/Palette.kt', 'DarkIconGrayBg = Color(0xE6121548)', 'DarkIconGrayBg = Color(0xFF141A4D)')
    sub(SHARED / 'com/lagradost/cloudstream4/theme/Theme.kt', r'(lightColorScheme\(\s*primary = primary,\s*)background = background,', r'\1background = Color.Transparent,')
    base = SHARED / 'com/mihon/presentation/settings/widget/BasePreferenceWidget.kt'
    lit(base, 'val minHeight = LocalPreferenceMinHeight.current', '''val minHeight = LocalPreferenceMinHeight.current
    val isLightTheme = MaterialTheme.colorScheme.onBackground.luminance() < 0.5f
    val glassTop = if (isLightTheme) Color(0xD9FFFFFF) else Color(0x4DFFFFFF)
    val glassBottom = if (isLightTheme) Color(0x99FFFFFF) else Color(0x14FFFFFF)
    val glassEdge = if (isLightTheme) listOf(Color(0xFFFFFFFF), Color(0x664B5BD8), Color(0xCCFFFFFF))
        else listOf(Color(0x99FFFFFF), Color(0x1AFFFFFF), Color(0x66FFFFFF))''')
    lit(base, '.background(Brush.verticalGradient(listOf(Color(0x4DFFFFFF), Color(0x14FFFFFF))))', '.background(Brush.verticalGradient(listOf(glassTop, glassBottom)))')
    lit(base, 'Brush.linearGradient(listOf(Color(0x99FFFFFF), Color(0x1AFFFFFF), Color(0x66FFFFFF))),', 'Brush.linearGradient(glassEdge),')
    add_imports(base, ['androidx.compose.ui.graphics.luminance'])
    lit(KT / 'ui/settings/SettingsFragmentScreen.kt', '.border(1.dp, Color(0x66FFFFFF), CircleShape)',
        '.border(1.dp, MaterialTheme.colorScheme.onBackground.copy(alpha = 0.3f), CircleShape)')
    print('StreamVerse glass v2 applied OK')

main()
