#!/usr/bin/env python3
"""
StreamVerse patcher.
Usage: python3 apply.py <path-to-cloudstream-source> [logo_source.png]

Turns an upstream CloudStream checkout into "StreamVerse":
  * new name + new package id (com.streamverse.app)
  * new launcher icon / TV banner / splash generated from logo_source.png
  * "liquid glass" look (gradient backdrop, frosted translucent panels,
    glass bottom bar, real background blur on dialogs for Android 12+)
  * upstream in-app updater switched off (it would install the original app)
"""
import os, re, sys, pathlib
import numpy as np
from PIL import Image, ImageDraw

ROOT = pathlib.Path(sys.argv[1]).resolve()
LOGO = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else pathlib.Path(__file__).with_name('logo_source.png'))
MAIN = ROOT / 'app/src/main'
RES = MAIN / 'res'
NEW_APP_ID = 'com.streamverse.app'
APP_NAME = 'StreamVerse'

def read(p):  return pathlib.Path(p).read_text(encoding='utf-8')
def write(p, s):
    p = pathlib.Path(p); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(s, encoding='utf-8')
def sub(path, pattern, repl, count=1, flags=0):
    s = read(path); n, k = re.subn(pattern, repl, s, count=count, flags=flags)
    if k == 0: raise SystemExit(f'PATCH FAILED: pattern not found in {path}: {pattern[:70]}')
    write(path, n)

# ------------------------------------------------------------------ icons / splash art
def gen_art():
    c = np.asarray(Image.open(LOGO).convert('RGB')).astype(float)
    h, w, _ = c.shape
    def patch(x, y, r=10): return c[max(0,y-r):y+r, max(0,x-r):x+r].reshape(-1,3).mean(axis=0)
    tl, tr, bl, br = patch(14,14), patch(w-14,14), patch(14,h-14), patch(w-14,h-14)
    yy, xx = np.mgrid[0:h, 0:w]; u, v = xx/(w-1), yy/(h-1)
    bg = (tl*((1-u)*(1-v))[...,None] + tr*(u*(1-v))[...,None] + bl*((1-u)*v)[...,None] + br*(u*v)[...,None])
    diff = np.clip(c - bg, 0, None).max(axis=2)
    a = np.clip((diff - 14) / 80.0, 0, 1)
    F = np.clip((c - bg*(1-a)[...,None]) / np.maximum(a, 1e-3)[...,None], 0, 255)
    logo = Image.fromarray(np.dstack([F, a*255]).astype(np.uint8), 'RGBA')
    logo = logo.crop(logo.getchannel('A').point(lambda p: 255 if p > 40 else 0).getbbox())

    def canvas(img, side, ratio):
        s = ratio*side/max(img.size)
        im = img.resize((max(1, round(img.width*s)), max(1, round(img.height*s))), Image.LANCZOS)
        cv = Image.new('RGBA', (side, side), (0,0,0,0)); cv.alpha_composite(im, ((side-im.width)//2, (side-im.height)//2))
        return cv
    def plate(w_, h_):
        yy, xx = np.mgrid[0:h_, 0:w_]; u, v = xx/(w_-1), yy/(h_-1)
        p = (tl*((1-u)*(1-v))[...,None] + tr*(u*(1-v))[...,None] + bl*((1-u)*v)[...,None] + br*(u*v)[...,None])
        return Image.fromarray(np.clip(p,0,255).astype(np.uint8), 'RGB').convert('RGBA')
    def legacy(size, round_):
        S = size*4; pl = plate(S, S); pl.alpha_composite(canvas(logo, S, 0.74))
        m = Image.new('L', (S,S), 0); d = ImageDraw.Draw(m)
        if round_: d.ellipse((0,0,S-1,S-1), fill=255)
        else: d.rounded_rectangle((0,0,S-1,S-1), radius=int(S*0.22), fill=255)
        pl.putalpha(m); return pl.resize((size,size), Image.LANCZOS)

    nodpi = RES / 'drawable-nodpi'; nodpi.mkdir(parents=True, exist_ok=True)
    canvas(logo, 768, 0.92).save(nodpi / 'sv_logo.png')
    fg = canvas(logo, 432, 0.60); fg.save(nodpi / 'sv_icon_fg.png')
    mono = Image.new('RGBA', fg.size, (255,255,255,0)); mono.putalpha(fg.getchannel('A')); mono.save(nodpi / 'sv_icon_mono.png')
    for d_, s in {'mdpi':48,'hdpi':72,'xhdpi':96,'xxhdpi':144,'xxxhdpi':192}.items():
        (RES / f'mipmap-{d_}').mkdir(parents=True, exist_ok=True)
        legacy(s, False).save(RES / f'mipmap-{d_}' / 'ic_launcher.png')
        legacy(s, True).save(RES / f'mipmap-{d_}' / 'ic_launcher_round.png')
    bn = plate(1280, 720); bn.alpha_composite(canvas(logo, 720, 0.86), (280, 0))
    bn.convert('RGB').resize((320,180), Image.LANCZOS).save(RES / 'mipmap-xhdpi' / 'ic_banner.png')

# ------------------------------------------------------------------ XML resources
XML = '<?xml version="1.0" encoding="utf-8"?>\n'
FILES = {
'values/streamverse_glass.xml': XML + '''<resources>
    <color name="sv_bg_deep">#0B0D2B</color>
    <color name="sv_bg_mid">#16134D</color>
    <color name="sv_bg_end">#1D0F45</color>
    <color name="sv_glow_blue">#3D4DA3FF</color>
    <color name="sv_glow_pink">#33FF7AC8</color>
</resources>
''',
'drawable/sv_glass_bg.xml': XML + '''<layer-list xmlns:android="http://schemas.android.com/apk/res/android">
    <item>
        <shape android:shape="rectangle">
            <gradient android:angle="270" android:startColor="@color/sv_bg_deep"
                android:centerColor="@color/sv_bg_mid" android:endColor="@color/sv_bg_end" />
        </shape>
    </item>
    <item>
        <shape android:shape="rectangle">
            <gradient android:type="radial" android:centerX="0.12" android:centerY="0.08"
                android:gradientRadius="460dp" android:startColor="@color/sv_glow_blue" android:endColor="#004DA3FF" />
        </shape>
    </item>
    <item>
        <shape android:shape="rectangle">
            <gradient android:type="radial" android:centerX="0.95" android:centerY="0.92"
                android:gradientRadius="460dp" android:startColor="@color/sv_glow_pink" android:endColor="#00FF7AC8" />
        </shape>
    </item>
</layer-list>
''',
'drawable/sv_glass_nav.xml': XML + '''<layer-list xmlns:android="http://schemas.android.com/apk/res/android">
    <item><shape android:shape="rectangle"><solid android:color="#CC0E1240" /></shape></item>
    <item>
        <shape android:shape="rectangle">
            <gradient android:angle="270" android:startColor="#38FFFFFF" android:endColor="#06FFFFFF" />
        </shape>
    </item>
    <item android:height="1dp" android:gravity="top">
        <shape android:shape="rectangle"><solid android:color="#66FFFFFF" /></shape>
    </item>
</layer-list>
''',
# bottom sheets
'drawable/rounded_dialog.xml': XML + '''<layer-list xmlns:android="http://schemas.android.com/apk/res/android">
    <item>
        <shape android:shape="rectangle">
            <corners android:topLeftRadius="26dp" android:topRightRadius="26dp" />
            <solid android:color="#E6121548" />
        </shape>
    </item>
    <item>
        <shape android:shape="rectangle">
            <corners android:topLeftRadius="26dp" android:topRightRadius="26dp" />
            <gradient android:angle="270" android:startColor="#38FFFFFF" android:endColor="#08FFFFFF" />
        </shape>
    </item>
    <item>
        <shape android:shape="rectangle">
            <corners android:topLeftRadius="26dp" android:topRightRadius="26dp" />
            <stroke android:width="1dp" android:color="#55FFFFFF" />
        </shape>
    </item>
</layer-list>
''',
# alert dialogs
'drawable/dialog__window_background.xml': XML + '''<layer-list xmlns:android="http://schemas.android.com/apk/res/android">
    <item>
        <shape android:shape="rectangle">
            <corners android:radius="22dp" />
            <solid android:color="#E6121548" />
        </shape>
    </item>
    <item>
        <shape android:shape="rectangle">
            <corners android:radius="22dp" />
            <gradient android:angle="270" android:startColor="#38FFFFFF" android:endColor="#08FFFFFF" />
        </shape>
    </item>
    <item>
        <shape android:shape="rectangle">
            <corners android:radius="22dp" />
            <stroke android:width="1dp" android:color="#55FFFFFF" />
        </shape>
    </item>
</layer-list>
''',
'drawable/sv_icon_bg.xml': XML + '''<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle">
    <gradient android:angle="315" android:startColor="#1F336D" android:centerColor="#13164A" android:endColor="#140431" />
</shape>
''',
'drawable/splash_background.xml': XML + '''<layer-list xmlns:android="http://schemas.android.com/apk/res/android">
    <item android:drawable="@drawable/sv_glass_bg" />
    <item android:width="240dp" android:height="240dp" android:gravity="center" android:drawable="@drawable/sv_logo" />
</layer-list>
''',
'mipmap-anydpi-v26/ic_launcher.xml': XML + '''<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@drawable/sv_icon_bg" />
    <foreground android:drawable="@drawable/sv_icon_fg" />
    <monochrome android:drawable="@drawable/sv_icon_mono" />
</adaptive-icon>
''',
}
FILES['mipmap-anydpi-v26/ic_launcher_round.xml'] = FILES['mipmap-anydpi-v26/ic_launcher.xml']

# ------------------------------------------------------------------ patch steps
def main():
    if not (ROOT / 'app/build.gradle.kts').exists(): raise SystemExit('not a CloudStream checkout: ' + str(ROOT))
    # 1. package id
    sub(ROOT/'app/build.gradle.kts', r'applicationId = "com\.lagradost\.cloudstream3"', f'applicationId = "{NEW_APP_ID}"')

    # 2. visible name in every language file (skip keys and URLs)
    pat = re.compile(r'(?<![\w/.\-])CloudStream(?![\w\-])')
    for f in RES.glob('values*/strings.xml'):
        out = []
        for line in read(f).split('\n'):
            if 'http' not in line and not re.search(r'name="[^"]*_key"', line): line = pat.sub(APP_NAME, line)
            out.append(line)
        write(f, '\n'.join(out))

    # 3. art + xml resources
    gen_art()
    for rel, content in FILES.items(): write(RES / rel, content)
    banner_xml = RES / 'mipmap-anydpi-v26/ic_banner.xml'
    if banner_xml.exists(): banner_xml.unlink()     # use the PNG banner instead

    # 4. palette (navy / glass)
    colors = RES / 'values/colors.xml'
    for name, val in {'primaryBlackBackground':'#0B0D2B', 'iconGrayBackground':'#10133A',
                      'primaryGrayBackground':'#4D303A80', 'boxItemBackground':'#332A3170',
                      'colorPrimary':'#4DA3FF', 'colorAccent':'#8C7CFF'}.items():
        sub(colors, rf'(<color name="{name}">)#[0-9A-Fa-f]+(</color>)', rf'\g<1>{val}\g<2>')

    # 5. theme: gradient window, splash colour, blur on dialogs, launch theme
    st = RES / 'values/styles.xml'
    sub(st, r'(<item name="android:windowBackground">)@drawable/splash_background(</item>)',
        r'\g<1>@drawable/sv_glass_bg\g<2>\n        <item name="android:windowSplashScreenBackground">@color/sv_bg_deep</item>')
    sub(st, r'(<style name="Theme\.AlertDialog"[^>]*>)',
        r'''\g<1>
        <item name="android:windowBackgroundBlurRadius">48dp</item>
        <item name="android:windowBlurBehindEnabled">true</item>
        <item name="android:windowBlurBehindRadius">18dp</item>''')
    sub(st, r'(<style name="AppBottomSheetDialogTheme"[^>]*>)',
        r'''\g<1>
        <item name="android:windowBlurBehindEnabled">true</item>
        <item name="android:windowBlurBehindRadius">22dp</item>''')
    sub(st, r'<item name="backgroundTint">\?attr/primaryBlackBackground</item>', '<item name="backgroundTint">@null</item>')
    s = read(st); i = s.rfind('</resources>')
    write(st, s[:i] + '''
    <!-- StreamVerse: launcher activity shows the logo splash until the app theme takes over -->
    <style name="SvLaunchTheme" parent="AppTheme">
        <item name="android:windowBackground">@drawable/splash_background</item>
    </style>
''' + s[i:])

    # 6. glass bottom bar / rail
    sub(RES/'layout/activity_main.xml', r'android:background="\?attr/primaryGrayBackground"',
        'android:background="@drawable/sv_glass_nav"', count=0)

    # 7. gradient backdrop for full-page fragments that paint their own background
    for lay in ['fragment_result','fragment_result_tv','main_settings','provider_list','fragment_download_queue']:
        p = RES / f'layout/{lay}.xml'
        s = read(p)
        m = re.search(r'<(?![?!])[\w.]+[^>]*>', s)       # root start tag (skips <?xml ?> and comments)
        tag = m.group(0)
        if 'android:background="?attr/primaryBlackBackground"' not in tag: raise SystemExit(f'root background not found in {lay}')
        tag2 = tag.replace('android:background="?attr/primaryBlackBackground"', 'android:background="@drawable/sv_glass_bg"', 1)
        write(p, s[:m.start()] + tag2 + s[m.end():])

    # 8. launcher activity -> logo splash theme
    sub(MAIN/'AndroidManifest.xml', r'(android:name="\.ui\.account\.AccountSelectActivity2")',
        r'\g<1>\n            android:theme="@style/SvLaunchTheme"')

    # 9. no upstream updates (would install the original CloudStream)
    sub(MAIN/'java/com/lagradost/cloudstream3/utils/InAppUpdater.kt',
        r'// No updates on debug version\s*\n(\s*)BuildConfig\.DEBUG ->',
        r'// StreamVerse: updates disabled (upstream builds are a different app)\n\1BuildConfig.DEBUG || true ->')
    print('StreamVerse patch applied OK')

main()
