#!/usr/bin/env python3
import pathlib
import sys

root = pathlib.Path(sys.argv[1]).resolve()
path = root / "app/src/main/java/com/lagradost/cloudstream3/utils/downloader/DownloadManager.kt"
s = path.read_text(encoding="utf-8")

helper = '''
// StreamVerse: prefer links labelled as Hindi audio (name or provider).
// If none are labelled, callers fall back to all links.
private fun isStreamVerseHindiAudio(link: ExtractorLink): Boolean {
    val text = "${link.name} ${link.source}".lowercase()
    return Regex("""(^|[^a-z])(hindi|hin|hi-in|dual audio|multi audio)([^a-z]|$)|हिंदी""")
        .containsMatchIn(text)
}

'''

if "private fun isStreamVerseHindiAudio" not in s:
    anchor = 'const val DOWNLOAD_CHANNEL_ID = "cloudstream3.general"'
    if anchor not in s:
        raise SystemExit("DownloadManager helper insertion point not found")
    s = s.replace(anchor, helper + anchor, 1)

old = '''        private fun downloadEpisodeWithLinks(
            links: List<ExtractorLink>,
            subs: List<SubtitleData>?
        ) {
            val downloadItem = downloadQueueWrapper.downloadItem ?: return
            try {'''
new = '''        private fun downloadEpisodeWithLinks(
            links: List<ExtractorLink>,
            subs: List<SubtitleData>?
        ) {
            val downloadItem = downloadQueueWrapper.downloadItem ?: return
            val hindiLinks = links.filter { isStreamVerseHindiAudio(it) }.ifEmpty { links }
            if (hindiLinks.isEmpty()) {
                isFailed = true
                return
            }
            try {'''
if "val hindiLinks = links.filter" not in s:
    if old not in s:
        raise SystemExit("Download link filter insertion point not found")
    s = s.replace(old, new, 1)

old2 = "val info = DownloadItem(src, folder, meta, links)"
new2 = "val info = DownloadItem(src, folder, meta, hindiLinks)"
if old2 in s:
    s = s.replace(old2, new2, 1)
elif new2 not in s:
    raise SystemExit("DownloadItem link argument not found")

old3 = '''            // Wait for link loading completion
            linkLoadingJob?.join()

            // Remove link loading notification'''
new3 = '''            // Wait for link loading completion
            linkLoadingJob?.join()

            // Keep only Hindi-labelled links, but only if at least one exists.
            if (currentLinks.any { isStreamVerseHindiAudio(it) }) {
                currentLinks.removeAll { !isStreamVerseHindiAudio(it) }
            }

            // Remove link loading notification'''
if "if (currentLinks.any { isStreamVerseHindiAudio(it) })" not in s:
    if old3 not in s:
        raise SystemExit("Generated-link filter insertion point not found")
    s = s.replace(old3, new3, 1)

path.write_text(s, encoding="utf-8")
print("SUCCESS: Hindi-audio download preference applied")
