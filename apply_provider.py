#!/usr/bin/env python3
"""
StreamVerse provider sheet + chips (run AFTER the other patches):  python3 apply_provider.py <cloudstream-source>
  * Provider Selection sheet: title, every provider is a rounded glass pill row, gear icon for provider settings
  * Chips (Movies / TV Series / Anime ... on the provider sheet and the extensions page): glass, readable in white and black themes
  * Extensions page: transparent top bar / filter row so the wallpaper shows through
"""
import re, sys, pathlib

ROOT = pathlib.Path(sys.argv[1]).resolve()
RES = ROOT / 'app/src/main/res'

def read(p): return pathlib.Path(p).read_bytes().decode('utf-8')
def write(p, s):
    p = pathlib.Path(p); p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(s.encode('utf-8'))
def rep(path, old, new, expect=1):
    s = read(path); k = s.count(old)
    if k != expect: raise SystemExit(f'PATCH FAILED: expected {expect}x {old[:60]!r} in {pathlib.Path(path).name}, found {k}')
    write(path, s.replace(old, new))

XML = '<?xml version="1.0" encoding="utf-8"?>\n'
FILES = {
 'drawable/sv_glass_row.xml': XML + '''<layer-list xmlns:android="http://schemas.android.com/apk/res/android">
    <item><shape android:shape="rectangle"><corners android:radius="28dp" /><solid android:color="?attr/svGlassFill" /></shape></item>
    <item><shape android:shape="rectangle"><corners android:radius="28dp" />
        <gradient android:angle="270" android:startColor="?attr/svGlassSheen" android:endColor="#00FFFFFF" /></shape></item>
    <item><shape android:shape="rectangle"><corners android:radius="28dp" />
        <stroke android:width="1dp" android:color="?attr/svGlassEdge" /></shape></item>
</layer-list>
''',
 # simple gear: ring + 8 spokes (own drawing, tinted by the theme text colour)
 'drawable/ic_sv_gear.xml': XML + '''<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp" android:height="24dp" android:viewportWidth="24" android:viewportHeight="24"
    android:tint="?attr/textColor">
    <path android:strokeColor="#FFFFFFFF" android:strokeWidth="2.2" android:strokeLineCap="round" android:fillColor="#00000000"
        android:pathData="M12,8.6a3.4,3.4 0 1 0 0.001,0z" />
    <path android:strokeColor="#FFFFFFFF" android:strokeWidth="2.6" android:strokeLineCap="round" android:fillColor="#00000000"
        android:pathData="M12,3.2v2.3M12,18.5v2.3M3.2,12h2.3M18.5,12h2.3M5.8,5.8l1.6,1.6M16.6,16.6l1.6,1.6M5.8,18.2l1.6,-1.6M16.6,7.4l1.6,-1.6" />
</vector>
''',
 # chips: strong blue glass when selected (white text), theme glass when not (theme text colour)
 'color/chip_color.xml': XML + '''<selector xmlns:android="http://schemas.android.com/apk/res/android">
    <item android:color="#E65B7CFF" android:state_checked="true"/>
    <item android:color="?attr/svGlassFill" android:state_checked="false"/>
</selector>
''',
 'color/chip_color_text.xml': XML + '''<selector xmlns:android="http://schemas.android.com/apk/res/android">
    <item android:color="#FFFFFFFF" android:state_checked="true"/>
    <item android:color="?attr/textColor" android:state_checked="false"/>
</selector>
''',
 'color/sv_chip_stroke.xml': XML + '''<selector xmlns:android="http://schemas.android.com/apk/res/android">
    <item android:state_focused="true" android:color="?attr/white"/>
    <item android:color="?attr/svGlassEdge"/>
</selector>
''',
 # one provider = one glass pill row
 'layout/sort_bottom_single_provider_choice.xml': XML + '''<FrameLayout xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:tools="http://schemas.android.com/tools"
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:paddingStart="16dp"
    android:paddingTop="5dp"
    android:paddingEnd="16dp"
    android:paddingBottom="5dp">

    <FrameLayout
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:background="@drawable/sv_glass_row"
        android:minHeight="56dp">

        <TextView
            android:id="@+id/text1"
            style="@style/CheckLabel"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:layout_gravity="center"
            android:paddingEnd="56dp"
            tools:text="hello" />

        <LinearLayout
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:layout_gravity="end|center_vertical"
            android:orientation="horizontal">

            <ImageView
                android:id="@+id/action_settings"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:background="?attr/selectableItemBackgroundBorderless"
                android:contentDescription="@string/title_settings"
                android:padding="10dp"
                android:src="@drawable/ic_sv_gear"
                android:visibility="gone"
                tools:visibility="visible" />

            <ImageView
                android:id="@+id/pinicon"
                android:layout_width="50dp"
                android:layout_height="24dp"
                android:layout_gravity="center_vertical"
                android:src="@drawable/pin_ic"
                android:visibility="gone"
                tools:ignore="RtlHardcoded"
                tools:visibility="visible" />
        </LinearLayout>
    </FrameLayout>
</FrameLayout>
''',
}

def main():
    if not (RES / 'values/sv_attrs.xml').exists(): raise SystemExit('run the other patches first')
    for rel, content in FILES.items(): write(RES / rel, content)

    # title above the list
    sel = RES / 'layout/home_select_mainpage.xml'
    rep(sel, '''    <ListView
        android:id="@+id/listview1"''', '''    <TextView
        android:id="@+id/sv_provider_title"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:layout_gravity="top"
        android:paddingStart="24dp"
        android:paddingTop="18dp"
        android:paddingEnd="24dp"
        android:text="Provider Selection"
        android:textColor="?attr/textColor"
        android:textSize="20sp"
        android:textStyle="bold" />

    <ListView
        android:id="@+id/listview1"''')
    rep(sel, 'android:layout_marginTop="10dp"', 'android:layout_marginTop="62dp"')

    # chips: thin glass edge instead of a heavy 2dp outline
    st = RES / 'values/styles.xml'
    rep(st, '<item name="chipStrokeColor">@color/white_transparent_toggle</item>', '<item name="chipStrokeColor">@color/sv_chip_stroke</item>')
    s = read(st)
    i = s.index('<style name="ChipFilled"'); j = s.index('</style>', i)
    blk = s[i:j]
    if '<item name="chipStrokeWidth">2dp</item>' not in blk: raise SystemExit('chipStrokeWidth not found')
    write(st, s[:i] + blk.replace('<item name="chipStrokeWidth">2dp</item>', '<item name="chipStrokeWidth">1dp</item>') + s[j:])

    # extensions / plugins page: let the wallpaper show through
    pl = RES / 'layout/fragment_plugins.xml'
    rep(pl, 'android:background="?attr/primaryGrayBackground"', 'android:background="@color/transparent"', expect=3)
    rep(pl, 'android:background="?attr/primaryBlackBackground"', 'android:background="@color/transparent"', expect=1)
    print('StreamVerse provider sheet + chips applied OK')

main()
