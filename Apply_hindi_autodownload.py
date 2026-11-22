#!/usr/bin/env python3
import pathlib
import re
import sys

ROOT = pathlib.Path(sys.argv[1]).resolve()
BASE = ROOT / "app/src/main/java/com/lagradost/cloudstream3"

def read(path):
    return path.read_text(encoding="utf-8")

def write(path, content):
    path.write_text(content, encoding="utf-8")

# 1. Add built-in repositories
repo_file = BASE / "plugins/RepositoryManager.kt"
s = read(repo_file)

old = """val PREBUILT_REPOSITORIES: Array<RepositoryData> by lazy {
        getKey<Array<RepositoryData>>("PREBUILT_REPOSITORIES") ?: emptyArray()
    }"""

new = """val PREBUILT_REPOSITORIES: Array<RepositoryData> by lazy {
        arrayOf(
            RepositoryData("Phisher Extensions", "https://raw.githubusercontent.com/phisher98/cloudstream-extensions-phisher/refs/heads/builds/repo.json"),
            RepositoryData("CSX", "https://raw.githubusercontent.com/SaurabhKaperwan/CSX/builds/CS.json"),
            RepositoryData("CNCVerse", "https://raw.githubusercontent.com/NivinCNC/CNCVerse-Cloud-Stream-Extension/refs/heads/builds/CNC.json"),
            RepositoryData("NetMirror", "https://raw.githubusercontent.com/Sushan64/NetMirror-Extension/refs/heads/builds/Netflix.json"),
            RepositoryData("Desi", "https://raw.githubusercontent.com/Faisal0786/Desi/main/repo.json")
        )
    }"""

if old not in s:
    raise SystemExit("RepositoryManager patch location not found")

write(repo_file, s.replace(old, new, 1))

# 2. Hindi-only language filter
plugin_file = BASE / "plugins/PluginManager.kt"
s = read(plugin_file)

old = """if (mode == AutoDownloadMode.FilterByLang) {
                val lang = sitePlugin.language ?: return@mapNotNull null
                //If set to 'universal', don't skip any language
                if (!providerLang.contains(AllLanguagesName) && !providerLang.contains(lang)) {
                    return@mapNotNull null
                }
                //Log.i(TAG, "sitePlugin lang => $lang")
            }"""

new = """if (mode == AutoDownloadMode.FilterByLang) {
                val lang = sitePlugin.language?.trim()?.lowercase()
                    ?: return@mapNotNull null
                if (lang != "hi" && lang != "hindi" && !lang.startsWith("hi-")) {
                    return@mapNotNull null
                }
            }"""

if old not in s:
    raise SystemExit("Hindi language filter location not found")

write(plugin_file, s.replace(old, new, 1))

# 3. Enable automatic download and activation at startup
main_file = BASE / "MainActivity.kt"
s = read(main_file)

if "import com.lagradost.cloudstream3.AutoDownloadMode" not in s:
    marker = "import com.lagradost.cloudstream3.plugins.PluginManager"
    if marker not in s:
        raise SystemExit("MainActivity import location not found")
    s = s.replace(
        marker,
        "import com.lagradost.cloudstream3.AutoDownloadMode\n" + marker,
        1
    )

old = """//Automatically download not existing plugins, using mode specified.
                    /*val autoDownloadPlugin = AutoDownloadMode.getEnum(
                        settingsManager.getInt(
                            getString(R.string.auto_download_plugins_key),
                            0
                        )
                    ) ?: AutoDownloadMode.Disable
                    if (autoDownloadPlugin != AutoDownloadMode.Disable) {
                        PluginManager.___DO_NOT_CALL_FROM_A_PLUGIN_downloadNotExistingPluginsAndLoad(
                            this@MainActivity,
                            autoDownloadPlugin
                        )
                    }*/"""

new = """// Automatically download and activate Hindi extensions.
                    PluginManager.___DO_NOT_CALL_FROM_A_PLUGIN_downloadNotExistingPluginsAndLoad(
                        this@MainActivity,
                        AutoDownloadMode.FilterByLang
                    )"""

if old not in s:
    raise SystemExit("MainActivity auto-download location not found")

write(main_file, s.replace(old, new, 1))

print("SUCCESS: Hindi auto-download patch applied.")
