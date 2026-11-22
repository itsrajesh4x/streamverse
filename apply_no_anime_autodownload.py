#!/usr/bin/env python3
import pathlib
import sys

root = pathlib.Path(sys.argv[1]).resolve()

path = root / "app/src/main/java/com/lagradost/cloudstream3/plugins/PluginManager.kt"

s = path.read_text(encoding="utf-8")

anchor = """            val sitePlugin = onlineData.plugin
            val tvtypes = sitePlugin.tvTypes ?: listOf()
"""

replacement = anchor + """
            // StreamVerse: Block automatic Anime extension downloads
            val pluginName = (
                sitePlugin.name + " " + sitePlugin.internalName
            ).lowercase()

            if (pluginName.contains("anime")) {
                return@mapNotNull null
            }
"""

if "Block automatic Anime extension downloads" not in s:
    if anchor not in s:
        raise SystemExit("Anime filter insertion point not found")
    s = s.replace(anchor, replacement, 1)

path.write_text(s, encoding="utf-8")

print("SUCCESS: Anime auto-download blocked")
