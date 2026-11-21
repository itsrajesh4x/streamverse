#!/usr/bin/env python3
"""
StreamVerse social + themes (run AFTER the other patches):  python3 apply_social.py <cloudstream-source> [instagram_url telegram_url]
  * "About" block on the main Settings page with Instagram + Telegram (icon + link)
  * App theme list reduced to two: Black and White
"""
import re, sys, pathlib

# ====== YOUR LINKS ======
INSTAGRAM_URL = "https://www.instagram.com/its___rajesh___4x__"
TELEGRAM_URL = "https://t.me/fixmyapp"
# ========================

ROOT = pathlib.Path(sys.argv[1]).resolve()
if len(sys.argv) >= 4: INSTAGRAM_URL, TELEGRAM_URL = sys.argv[2], sys.argv[3]
for u in (INSTAGRAM_URL, TELEGRAM_URL):
    if not u.startswith('http'): raise SystemExit('Set INSTAGRAM_URL and TELEGRAM_URL (must start with https://) at the top of apply_social.py')
RES = ROOT / 'app/src/main/res'
SCREEN = ROOT / 'app/src/main/java/com/lagradost/cloudstream3/ui/settings/SettingsFragmentScreen.kt'

def read(p): return pathlib.Path(p).read_bytes().decode('utf-8')
def write(p, s): pathlib.Path(p).write_bytes(s.encode('utf-8'))
def kt(s): return s.replace('\\', '\\\\').replace('"', '\\"').replace('$', '\\$')

XML = '<?xml version="1.0" encoding="utf-8"?>\n'
ICONS = {
 # simple monochrome glyphs (tinted by the theme: white on dark themes, dark on light themes)
 'drawable/ic_sv_instagram.xml': XML + '''<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp" android:height="24dp" android:viewportWidth="24" android:viewportHeight="24">
    <path android:strokeColor="#FFFFFFFF" android:strokeWidth="2" android:fillColor="#00000000"
        android:pathData="M7,2.5h10a4.5,4.5 0 0 1 4.5,4.5v10a4.5,4.5 0 0 1 -4.5,4.5h-10a4.5,4.5 0 0 1 -4.5,-4.5v-10a4.5,4.5 0 0 1 4.5,-4.5z" />
    <path android:strokeColor="#FFFFFFFF" android:strokeWidth="2" android:fillColor="#00000000"
        android:pathData="M12,7.9a4.1,4.1 0 1 0 0.001,0z" />
    <path android:fillColor="#FFFFFFFF"
        android:pathData="M17.5,5.4a1.2,1.2 0 1 0 0.001,0z" />
</vector>
''',
 'drawable/ic_sv_telegram.xml': XML + '''<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp" android:height="24dp" android:viewportWidth="24" android:viewportHeight="24">
    <path android:fillColor="#FFFFFFFF"
        android:pathData="M21.6,3.4L2.6,10.7L8,12.8L9.6,19.3L12.9,15.6L18,19.2z" />
</vector>
''',
}

def main():
    if not SCREEN.exists(): raise SystemExit('not a CloudStream checkout: ' + str(ROOT))
    for rel, content in ICONS.items(): write(RES / rel, content)

    # ---- About block (above the version line on the main Settings page)
    s = read(SCREEN)
    block = f'''Text(
                                text = "About",
                                style = MaterialTheme.typography.titleSmall,
                                modifier = Modifier.padding(start = 28.dp, top = 12.dp, bottom = 2.dp),
                            )
                            TextPreferenceWidget(
                                title = "Instagram",
                                subtitle = "{kt(INSTAGRAM_URL)}",
                                icon = painterResource(R.drawable.ic_sv_instagram),
                                onPreferenceClick = {{
                                    com.lagradost.cloudstream3.CloudStreamApp.openBrowser("{kt(INSTAGRAM_URL)}")
                                }},
                            )
                            TextPreferenceWidget(
                                title = "Telegram",
                                subtitle = "{kt(TELEGRAM_URL)}",
                                icon = painterResource(R.drawable.ic_sv_telegram),
                                onPreferenceClick = {{
                                    com.lagradost.cloudstream3.CloudStreamApp.openBrowser("{kt(TELEGRAM_URL)}")
                                }},
                            )
                            '''
    if s.count('BuildStamp()') < 2 or 'ic_sv_instagram' in s: raise SystemExit('BuildStamp call not found (or already patched)')
    i = s.index('BuildStamp()')               # first occurrence = the call inside the Column
    s = s[:i] + block + s[i:]
    write(SCREEN, s)

    # ---- themes: only Black (AmoledLight = the default pure-black theme) and White (Light)
    arr = RES / 'values/array.xml'; a = read(arr)
    a, k1 = re.subn(r'<string-array name="themes_names">.*?</string-array>',
                    '<string-array name="themes_names">\n        <item>Black</item>\n        <item>White</item>\n    </string-array>', a, flags=re.S)
    a, k2 = re.subn(r'<string-array name="themes_names_values">.*?</string-array>',
                    '<string-array name="themes_names_values">\n        <item>AmoledLight</item>\n        <item>Light</item>\n    </string-array>', a, flags=re.S)
    if k1 != 1 or k2 != 1: raise SystemExit('theme arrays not found')
    write(arr, a)
    for f in RES.glob('values-*/array.xml'):          # translated name lists would no longer match -> fall back to the default
        t = read(f); t2 = re.sub(r'[ \t]*<string-array name="themes_names">.*?</string-array>\s*', '', t, flags=re.S)
        if t2 != t: write(f, t2)
    print('StreamVerse social + themes applied OK')

main()
