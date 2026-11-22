#!/usr/bin/env python3
import pathlib
import sys

root = pathlib.Path(sys.argv[1]).resolve()

path = root / "app/src/main/java/com/lagradost/cloudstream3/ui/home/HomeViewModel.kt"

s = path.read_text(encoding="utf-8")

# 1. Add provider cache
anchor = "    private val expandable: MutableMap<String, ExpandableHomepageList> = mutableMapOf()"

insert = anchor + """
    // StreamVerse Fast Provider Cache
    private val homepageCache: MutableMap<String, Map<String, ExpandableHomepageList>> = mutableMapOf()
"""

if "private val homepageCache:" not in s:
    if anchor not in s:
        raise SystemExit("Cache insertion point not found")
    s = s.replace(anchor, insert, 1)

# 2. Show cached provider lists immediately
anchor = """        _apiName.postValue(repo?.name)
        _randomItems.postValue(listOf())"""

replacement = """        _apiName.postValue(repo?.name)

        val cachedHomepage = homepageCache[api.name]

        if (cachedHomepage != null) {
            expandable.clear()
            expandable.putAll(cachedHomepage)
            _page.postValue(Resource.Success(expandable.toMap()))
        } else {
            _page.postValue(Resource.Loading())
        }

        _randomItems.postValue(listOf())"""

if "val cachedHomepage = homepageCache[api.name]" not in s:
    if anchor not in s:
        raise SystemExit("Cache loading point not found")
    s = s.replace(anchor, replacement, 1)

# 3. Do not block homepage lists for preview loading
anchor = """        _page.postValue(Resource.Loading())
        _preview.postValue(Resource.Loading())"""

replacement = """        if (cachedHomepage == null) {
            _page.postValue(Resource.Loading())
        }
        _preview.postValue(Resource.Loading())"""

if replacement not in s:
    if anchor not in s:
        raise SystemExit("Loading point not found")
    s = s.replace(anchor, replacement, 1)

# 4. Publish homepage lists before preview requests
anchor = """                    val items = data.value.mapNotNull { it?.items }.flatten()"""

replacement = """                    homepageCache[api.name] = expandable.toMap()
                    _page.postValue(Resource.Success(expandable.toMap()))

                    val items = data.value.mapNotNull { it?.items }.flatten()"""

if "homepageCache[api.name] = expandable.toMap()" not in s:
    if anchor not in s:
        raise SystemExit("Homepage publishing point not found")
    s = s.replace(anchor, replacement, 1)

path.write_text(s, encoding="utf-8")

print("SUCCESS: Fast Provider Loading patch applied")
