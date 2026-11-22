#!/usr/bin/env python3
import pathlib
import sys

root = pathlib.Path(sys.argv[1]).resolve()
base = root / "app/src/main/java/com/lagradost/cloudstream3/ui/home"

# Unwanted homepage categories hide karo
home_vm = base / "HomeViewModel.kt"
s = home_vm.read_text(encoding="utf-8")

anchor = """                    data.value.forEach { home ->
                        home?.items?.forEach { list ->
                            val filteredList ="""

replacement = """                    data.value.forEach { home ->
                        home?.items?.forEach { list ->
                            val categoryName = list.name.trim().lowercase()
                            val unwantedCategory = listOf(
                                "anime", "k-drama", "k drama", "korean drama",
                                "c-drama", "c drama", "chinese drama",
                                "short show", "shorts", "short drama",
                                "preschool", "nursery rhyme", "nursery rhymes",
                                "kids songs", "children songs", "early learning"
                            ).any { categoryName.contains(it) }

                            if (unwantedCategory) return@forEach

                            val filteredList ="""

if "val unwantedCategory = listOf(" not in s:
    if anchor not in s:
        raise SystemExit("Homepage filter location not found")
    s = s.replace(anchor, replacement, 1)

home_vm.write_text(s, encoding="utf-8")

# Anime naam wale providers ko homepage selector se hide karo
home_fragment = base / "HomeFragment.kt"
s = home_fragment.read_text(encoding="utf-8")

anchor = """            val validAPIs = filterProviderByPreferredMedia().toMutableList()

            validAPIs.add(0, randomApi)"""

replacement = """            val validAPIs = filterProviderByPreferredMedia()
                .filterNot { api ->
                    api.name.trim().lowercase().contains("anime")
                }
                .toMutableList()

            validAPIs.add(0, randomApi)"""

if 'contains("anime")' not in s:
    if anchor not in s:
        raise SystemExit("Provider filter location not found")
    s = s.replace(anchor, replacement, 1)

home_fragment.write_text(s, encoding="utf-8")

print("SUCCESS: Content filters applied")
