#!/usr/bin/env python3
"""
StreamVerse glass update (run AFTER apply.py):  python3 apply_glass.py <cloudstream-source>
  * vivid liquid-glass wallpaper behind every screen
  * floating frosted pill bottom bar, glowing Play button, glass buttons/cards/poster edges
  * Compose settings screens: frosted cards + glass search pill
  * removes the remaining "CloudStream" name/logo from the app
"""
import re, sys, pathlib
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

def bezier(p0, p1, p2, p3, n=120):
    t = np.linspace(0, 1, n)[:, None]
    p0, p1, p2, p3 = map(np.array, (p0, p1, p2, p3))
    return ((1-t)**3*p0 + 3*(1-t)**2*t*p1 + 3*(1-t)*t**2*p2 + t**3*p3)

def make_wallpaper(path, W=810, H=1800, seed=7):
    rng = np.random.default_rng(seed)
    # deep navy -> near black base
    y = np.linspace(0, 1, H)[:, None, None]
    base = np.array([5, 6, 24])*(1-y) + np.array([10, 4, 38])*y
    img = np.repeat(base, W, axis=1).astype(np.float32)

    def layer(draw_fn, blur):
        im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im); draw_fn(d)
        im = im.filter(ImageFilter.GaussianBlur(blur))
        a = np.asarray(im).astype(np.float32)
        return a[..., :3], a[..., 3:4]/255.0

    def screen(dst, rgb, a):             # additive-ish "light" blend
        return 255 - (255-dst)*(1 - (rgb/255.0)*a)

    # 1) big lobe sweeping from lower-left to upper-right (cyan -> blue body, magenta rim)
    left = bezier((0.30*W, 1.05*H), (0.55*W, 0.78*H), (0.40*W, 0.40*H), (0.78*W, -0.05*H))
    poly = [tuple(p) for p in left] + [(1.2*W, -0.1*H), (1.2*W, 1.1*H)]
    img = screen(img, *layer(lambda d: d.polygon(poly, fill=(10, 175, 255, 255)), 75))
    # deeper blue inside
    inner = bezier((0.50*W, 1.05*H), (0.75*W, 0.80*H), (0.65*W, 0.45*H), (0.95*W, 0.02*H))
    poly2 = [tuple(p) for p in inner] + [(1.3*W, 0), (1.3*W, 1.1*H)]
    img = screen(img, *layer(lambda d: d.polygon(poly2, fill=(70, 60, 255, 235)), 85))
    # magenta / purple rim along the lobe edge
    img = screen(img, *layer(lambda d: d.line([tuple(p) for p in left], fill=(235, 50, 215, 255), width=int(0.13*W), joint='curve'), 38))
    # 2) purple swoosh upper-left
    sw = bezier((-0.2*W, 0.10*H), (0.3*W, 0.02*H), (0.5*W, 0.22*H), (0.9*W, 0.12*H))
    img = screen(img, *layer(lambda d: d.line([tuple(p) for p in sw], fill=(120, 40, 230, 220), width=int(0.20*W), joint='curve'), 60))
    # 3) magenta glow lower-right, cyan glow lower-left
    img = screen(img, *layer(lambda d: d.ellipse((0.55*W, 0.78*H, 1.35*W, 1.15*H), fill=(220, 50, 200, 190)), 90))
    img = screen(img, *layer(lambda d: d.ellipse((-0.4*W, 0.72*H, 0.35*W, 1.1*H), fill=(20, 160, 255, 150)), 90))

    # extra: violet haze mid-left, magenta ribbon crossing the lobe, cyan sparkle top-right
    img = screen(img, *layer(lambda d: d.ellipse((-0.5*W, 0.18*H, 0.6*W, 0.62*H), fill=(90, 40, 200, 170)), 110))
    rb = bezier((0.35*W, 0.95*H), (0.60*W, 0.70*H), (0.55*W, 0.40*H), (1.05*W, 0.28*H))
    img = screen(img, *layer(lambda d: d.line([tuple(p) for p in rb], fill=(255, 70, 190, 230), width=int(0.07*W), joint='curve'), 30))
    img = screen(img, *layer(lambda d: d.ellipse((0.65*W, -0.10*H, 1.3*W, 0.22*H), fill=(60, 220, 255, 200)), 80))
    # 4) dark ribbons for depth (subtract)
    dark = Image.new('L', (W, H), 0); d = ImageDraw.Draw(dark)
    rib = bezier((-0.1*W, 0.62*H), (0.3*W, 0.50*H), (0.5*W, 0.70*H), (0.7*W, 0.55*H))
    d.line([tuple(p) for p in rib], fill=150, width=int(0.14*W), joint='curve')
    dark = np.asarray(dark.filter(ImageFilter.GaussianBlur(55))).astype(np.float32)[..., None]/255.0
    img = img*(1 - 0.55*dark)
    # overall slight darkening + vignette so white text stays readable
    yy, xx = np.mgrid[0:H, 0:W]
    vig = 1 - 0.28*(((xx/W-0.5)**2 + (yy/H-0.5)**2)*2.0)[..., None]
    img = img*0.86*vig
    img += rng.normal(0, 1.6, img.shape)            # dither to avoid banding
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(path, 'WEBP', quality=90, method=6)


# ===================================================================== patcher
ROOT = pathlib.Path(sys.argv[1]).resolve()
MAIN = ROOT / 'app/src/main'
RES = MAIN / 'res'
KT = MAIN / 'java/com/lagradost/cloudstream3'
SHARED = ROOT / 'shared/src/commonMain/kotlin'

def read(p): return pathlib.Path(p).read_text(encoding='utf-8')
def write(p, s):
    p = pathlib.Path(p); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(s, encoding='utf-8')
def sub(path, pattern, repl, count=1, flags=0):
    s = read(path); n, k = re.subn(pattern, repl, s, count=count, flags=flags)
    if k == 0: raise SystemExit(f'PATCH FAILED: {pattern[:80]!r} not found in {path}')
    write(path, n)
def find(name, base=ROOT):
    hits = list(base.rglob(name))
    if not hits: raise SystemExit(f'file not found: {name}')
    return hits[0]
def add_imports(path, imports):
    s = read(path)
    for imp in imports:
        line = f'import {imp}'
        if line in s: continue
        s = re.sub(r'(^package [^\n]+\n)', r'\1\n' + line + '\n', s, count=1, flags=re.M)
    write(path, s)
def root_tag_sub(path, old, new):
    s = read(path); m = re.search(r'<(?![?!])[\w.]+[^>]*>', s); tag = m.group(0)
    if old not in tag: raise SystemExit(f'root attr {old!r} not found in {path}')
    write(path, s[:m.start()] + tag.replace(old, new, 1) + s[m.end():])

XML = '<?xml version="1.0" encoding="utf-8"?>\n'
RES_FILES = {
 # full-screen liquid wallpaper (used as window background everywhere + splash)
 'drawable/sv_glass_bg.xml': XML + '<bitmap xmlns:android="http://schemas.android.com/apk/res/android"\n    android:src="@drawable/sv_wallpaper"\n    android:gravity="fill" />\n',
 # floating frosted pill (bottom bar / side rail)
 'drawable/sv_glass_nav.xml': XML + '''<layer-list xmlns:android="http://schemas.android.com/apk/res/android">
    <item><shape android:shape="rectangle"><corners android:radius="40dp" /><solid android:color="#47182058" /></shape></item>
    <item><shape android:shape="rectangle"><corners android:radius="40dp" />
        <gradient android:angle="270" android:startColor="#52FFFFFF" android:endColor="#0DFFFFFF" /></shape></item>
    <item><shape android:shape="rectangle"><corners android:radius="40dp" />
        <stroke android:width="1dp" android:color="#8CFFFFFF" /></shape></item>
</layer-list>
''',
 # poster / card outline: faint glass edge, normal focus ring kept for TV
 'drawable/outline_drawable.xml': XML + '''<selector xmlns:android="http://schemas.android.com/apk/res/android">
    <item android:state_focused="true" android:drawable="@drawable/outline" />
    <item>
        <shape android:shape="rectangle">
            <corners android:radius="14dp" />
            <stroke android:width="1dp" android:color="#47FFFFFF" />
        </shape>
    </item>
</selector>
''',
 'color/item_select_color.xml': XML + '''<selector xmlns:android="http://schemas.android.com/apk/res/android">
    <item android:color="#FFFFFFFF" android:state_checked="true" />
    <item android:color="#FFFFFFFF" android:state_focused="true" />
    <item android:color="#FFFFFFFF" android:state_selected="true" />
    <item android:color="#CCFFFFFF" />
</selector>
''',
}

def main():
    if not (ROOT / 'app/build.gradle.kts').exists(): raise SystemExit('not a CloudStream checkout: ' + str(ROOT))
    if not (RES / 'drawable/sv_glass_bg.xml').exists(): raise SystemExit('run apply.py first')

    # ---- 1. wallpaper + resource drawables
    (RES / 'drawable-nodpi').mkdir(parents=True, exist_ok=True)
    make_wallpaper(str(RES / 'drawable-nodpi/sv_wallpaper.webp'))
    for rel, content in RES_FILES.items(): write(RES / rel, content)

    # ---- 2. replace every old cloud logo drawable with the StreamVerse logo (setup screen, notifications, TV)
    for f in list((RES).glob('drawable*/cloud_2*.xml')) + list(RES.glob('drawable*/ic_cloudstreamlogotv*.xml')):
        write(f, XML + '<bitmap xmlns:android="http://schemas.android.com/apk/res/android" android:src="@drawable/sv_logo" />\n')
    for f in RES.glob('drawable*/ic_cloudstream_monochrome*.xml'):
        write(f, XML + '<bitmap xmlns:android="http://schemas.android.com/apk/res/android" android:src="@drawable/sv_icon_mono" />\n')

    # ---- 3. glass palette (XML side)
    colors = RES / 'values/colors.xml'
    for name, val in {'primaryGrayBackground': '#38FFFFFF', 'boxItemBackground': '#2EFFFFFF'}.items():
        sub(colors, rf'(<color name="{name}">)#[0-9A-Fa-f]+(</color>)', rf'\g<1>{val}\g<2>')

    # ---- 4. styles: active-indicator glow, glowing white Play, glass buttons
    st = RES / 'values/styles.xml'
    sub(st, r'(<item name="android:windowSplashScreenBackground">@color/sv_bg_deep</item>)',
        r'\g<1>\n        <item name="colorSecondaryContainer">#B35B7CFF</item>')
    sub(st, r'(<style name="WhiteButton" parent="NiceButton">)',
        r'''\g<1>
        <item name="android:elevation">14dp</item>
        <item name="android:outlineSpotShadowColor">#CC9B6BFF</item>
        <item name="android:outlineAmbientShadowColor">#99B06BFF</item>''')
    s = read(st)
    m = re.search(r'<style name="BlackButton" parent="NiceButton">.*?</style>', s, re.S)
    blk = m.group(0)
    blk2 = re.sub(r'(<item name="backgroundTint">)[^<]*(</item>)', r'\g<1>#2EFFFFFF\g<2>', blk, count=1)
    blk2 = re.sub(r'(<item name="strokeColor">)[^<]*(</item>)', r'\g<1>#66FFFFFF\g<2>', blk2, count=1)
    if blk2 == blk: raise SystemExit('BlackButton style not patched')
    s = s[:m.start()] + blk2 + s[m.end():]
    i = s.rfind('</resources>')
    s = s[:i] + '''
    <!-- StreamVerse: tinted glass button (Play Movie / Resume) -->
    <style name="SvGlassAccentButton" parent="BlackButton">
        <item name="backgroundTint">#755B7CFF</item>
        <item name="strokeColor">#99FFFFFF</item>
    </style>
''' + s[i:]
    write(st, s)
    s = read(RES / 'layout/fragment_result.xml')
    for bid in ('result_play_movie', 'result_resume_series_button'):
        m = re.search(r'<com\.google\.android\.material\.button\.MaterialButton[^>]*android:id="@\+id/%s"[^>]*>' % bid, s)
        if not m: raise SystemExit('button not found: ' + bid)
        s = s[:m.start()] + m.group(0).replace('style="@style/WhiteButton"', 'style="@style/SvGlassAccentButton"') + s[m.end():]
    write(RES / 'layout/fragment_result.xml', s)

    # ---- 5. layouts: floating pill bar, transparent roots so the wallpaper shows through
    sub(RES / 'layout/activity_main.xml', r'android:layout_height="@dimen/nav_view_height"',
        'android:layout_height="@dimen/nav_view_height"\n            android:layout_marginStart="16dp"\n            android:layout_marginEnd="16dp"\n            android:layout_marginBottom="10dp"')
    for lay in ['fragment_result', 'fragment_result_tv', 'main_settings', 'provider_list', 'fragment_download_queue']:
        root_tag_sub(RES / f'layout/{lay}.xml', 'android:background="@drawable/sv_glass_bg"', 'android:background="@color/transparent"')
    root_tag_sub(RES / 'layout/fragment_home_head.xml', 'android:background="?attr/primaryBlackBackground"', 'android:background="@color/transparent"')
    root_tag_sub(RES / 'layout/activity_account_select.xml', 'android:background="?attr/primaryBlackBackground"', 'android:background="@drawable/sv_glass_bg"')

    # ---- 6. Compose side (settings & co): transparent page, glass colours, glass cards, glass search pill
    pal = SHARED / 'com/lagradost/cloudstream4/theme/Palette.kt'
    for name, val in {'DarkPrimaryGrayBg': '0x38FFFFFF', 'DarkBlackBg': '0xFF0B0D2B', 'DarkIconGrayBg': '0xE6121548',
                      'DarkBoxItemBg': '0x2EFFFFFF', 'Primary': '0xFF4DA3FF'}.items():
        sub(pal, rf'(val {name} = Color\()0x[0-9A-Fa-f]+(\))', rf'\g<1>{val}\g<2>')
    sub(SHARED / 'com/lagradost/cloudstream4/theme/Theme.kt',
        r'(darkColorScheme\(\s*primary = primary,\s*)background = background,', r'\g<1>background = Color.Transparent,')
    base = SHARED / 'com/mihon/presentation/settings/widget/BasePreferenceWidget.kt'
    sub(base, r'modifier = modifier\s*\.highlightBackground\(highlighted\)',
        '''modifier = modifier
                .padding(horizontal = 14.dp, vertical = 5.dp)
                .clip(RoundedCornerShape(26.dp))
                .background(Brush.verticalGradient(listOf(Color(0x4DFFFFFF), Color(0x14FFFFFF))))
                .border(
                    1.dp,
                    Brush.linearGradient(listOf(Color(0x99FFFFFF), Color(0x1AFFFFFF), Color(0x66FFFFFF))),
                    RoundedCornerShape(26.dp),
                )
                .highlightBackground(highlighted)''')
    add_imports(base, ['androidx.compose.foundation.border', 'androidx.compose.foundation.shape.RoundedCornerShape',
                       'androidx.compose.ui.draw.clip', 'androidx.compose.ui.graphics.Brush'])
    sset = KT / 'ui/settings/SettingsFragmentScreen.kt'
    sub(sset, r'(\.padding\(horizontal = 24\.dp - 12\.dp \* focusProgress\))',
        r'\g<1>\n                .clip(CircleShape)\n                .border(1.dp, Color(0x66FFFFFF), CircleShape)')
    add_imports(sset, ['androidx.compose.foundation.border', 'androidx.compose.ui.draw.clip'])

    # ---- 7. remove the CloudStream name everywhere the user can see it
    pat = re.compile(r'(?:(?<![A-Za-z/.@_])|(?<=\\n))cloud ?stream(?: ?3(?![0-9]))?', re.I)
    for f in list(RES.glob('values*/strings.xml')) + list(RES.glob('values*/donottranslate-strings.xml')):
        out = []
        for line in read(f).split('\n'):
            if 'http' not in line and '://' not in line and not re.search(r'name="[^"]*_key"', line): line = pat.sub('StreamVerse', line)
            out.append(line)
        write(f, '\n'.join(out))
    sub(find('CloudStreamPackage.kt', KT), r'appName = txt\("CloudStream"\)', 'appName = txt("StreamVerse")')
    sub(find('FcastManager.kt', KT), r'const val APP_PREFIX = "CloudStream"', 'const val APP_PREFIX = "StreamVerse"')
    sub(find('BackupAPI.kt', KT), r'"cloudstream-backup\.json"', '"streamverse-backup.json"')
    sub(find('PluginManager.kt', KT), r'\+ "/Cloudstream3/"', '+ "/StreamVerse/"')
    sub(find('ExtensionsScreen.kt', KT), r'name = "Cloudstream providers repository"', 'name = "StreamVerse providers repository"')
    print('StreamVerse glass patch applied OK')

main()
