#!/usr/bin/env python3
"""
StreamVerse removal patch (run AFTER apply.py and apply_glass.py):  python3 apply_remove.py <cloudstream-source>
Removes: GitHub/QuickNovel/Discord/Wiki links, Chromecast, AniList/MAL/Kitsu/Simkl sync accounts,
         App-update + Backup settings, and the easter-egg trigger.
Everything is removed from the UI / switched off at the entry point; no core code is deleted.
"""
import re, sys, pathlib

ROOT = pathlib.Path(sys.argv[1]).resolve()
KT = ROOT / 'app/src/main/java/com/lagradost/cloudstream3'
RES = ROOT / 'app/src/main/res'

def read(p):  return pathlib.Path(p).read_bytes().decode('utf-8')
def write(p, s): pathlib.Path(p).write_bytes(s.encode('utf-8'))

def scan(s, start=0, stop_at_zero=False):
    """walk Kotlin source from start, skipping strings/comments; returns (index after matching ')', final depth)"""
    depth, i, n = 0, start, len(s)
    while i < n:
        c = s[i]
        if s.startswith('"""', i):
            j = s.find('"""', i + 3); i = (j + 3) if j != -1 else n; continue
        if c == '"':
            i += 1
            while i < n and s[i] != '"':
                i += 2 if s[i] == '\\' else 1
            i += 1; continue
        if s.startswith('//', i):
            j = s.find('\n', i); i = j if j != -1 else n; continue
        if s.startswith('/*', i):
            j = s.find('*/', i + 2); i = (j + 2) if j != -1 else n; continue
        if c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if stop_at_zero and depth == 0: return i + 1, 0
        i += 1
    return n, depth

def remove_call(path, header_regex):
    """delete the whole Kotlin call expression that starts with header_regex (plus its trailing comma)"""
    s = read(path)
    m = re.search(header_regex, s)
    if not m: raise SystemExit(f'PATCH FAILED: {header_regex[:70]!r} not found in {pathlib.Path(path).name}')
    op = s.index('(', m.start())
    end, _ = scan(s, op, stop_at_zero=True)
    ls = s.rfind('\n', 0, m.start()) + 1
    start = ls if s[ls:m.start()].strip() == '' else m.start()
    tail = re.match(r'[ \t]*,?[ \t]*\r?\n', s[end:])
    end2 = end + (tail.end() if tail else 0)
    new = s[:start] + s[end2:]
    if scan(new)[1] != 0 or scan(s)[1] != 0: raise SystemExit(f'bracket check failed in {pathlib.Path(path).name}')
    write(path, new)

def sub(path, pattern, repl, count=1, flags=0, expect=None):
    s = read(path); n, k = re.subn(pattern, repl, s, count=count, flags=flags)
    if k == 0 or (expect is not None and k != expect):
        raise SystemExit(f'PATCH FAILED: {pattern[:70]!r} matched {k}x in {pathlib.Path(path).name}')
    write(path, n)

def main():
    if not (KT / 'MainActivity.kt').exists(): raise SystemExit('not a CloudStream checkout: ' + str(ROOT))

    # 1. GitHub / QuickNovel / Discord / Wiki links  (+ easter-egg "benene" counter)
    gen = KT / 'ui/settings/SettingsGeneralScreen.kt'
    remove_call(gen, r'Preference\.PreferenceGroup\(\s*title = stringResource\(R\.string\.pref_category_links\)')
    remove_call(gen, r'Preference\.PreferenceItem\.TextPreference\(\s*title = stringResource\(R\.string\.benene\)')
    sub(RES / 'xml/settings_general.xml', r'\s*<Preference\s+android:icon="@drawable/benene"[^>]*?/>', '', flags=re.S)
    scr = KT / 'ui/settings/SettingsFragmentScreen.kt'
    sub(scr, r'(R\.string\.pref_category_bypass),\s*R\.string\.pref_category_links', r'\1')

    # 2. App updates + Backup settings
    upd = KT / 'ui/settings/SettingsUpdatesScreen.kt'
    remove_call(upd, r'Preference\.PreferenceGroup\(\s*title = stringResource\(R\.string\.pref_category_app_updates\)')
    remove_call(upd, r'Preference\.PreferenceGroup\(\s*title = stringResource\(R\.string\.pref_category_backup\)')
    sub(scr, r'R\.string\.pref_category_app_updates,\s*R\.string\.pref_category_backup,\s*', '')

    # 3. Chromecast: switch the whole cast API off + remove its subtitle-settings entry
    sub(KT / 'utils/AppContextUtils.kt', r'(fun Context\.isCastApiAvailable\(\): Boolean \{)',
        r'\1\n        // StreamVerse: Chromecast removed\n        if (true) return false')
    remove_call(KT / 'ui/settings/SettingsPlayerScreen.kt',
                r'Preference\.PreferenceItem\.TextPreference\(\s*title = stringResource\(R\.string\.chromecast_subtitles_settings\)')

    # 4. AniList / MAL / Kitsu / Simkl sync accounts (local library + subtitle accounts stay)
    sub(KT / 'syncproviders/AccountManager.kt', r'[ \t]*SyncRepo\((?:malApi|kitsuApi|aniListApi|simklApi)\),?\r?\n', '', count=0, expect=8)
    sub(KT / 'ui/settings/SettingsAccountScreen.kt', r'[ \t]*SyncRepo\((?:malApi|kitsuApi|aniListApi|simklApi)\),?\r?\n', '', count=0, expect=4)
    print('StreamVerse removal patch applied OK')

main()
