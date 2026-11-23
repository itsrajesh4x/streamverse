#!/usr/bin/env python3
"""
StreamVerse features patch.
Run AFTER apply_player.py and apply_hindi_audio_download.py:
    python3 apply_streamverse_features.py <cloudstream-source>

Player (GeneratorPlayer.kt)
  1. Hindi links are sorted first, so the first Hindi link auto-plays
  2. "[Hindi]" / "[Dual]" badge in the Sources list
  3. Hindi audio track is selected by default (dual audio videos)
  4. Hindi subtitles are selected by default (if the user did not choose "no subtitles")
  5. New "Quality" button in the portrait panel under the video

Downloads (DownloadManager.kt)
  6. Quality preference: 1080p first, then 720p (edit SV_DOWNLOAD_PREFERRED_QUALITIES)
  7. Wi-Fi only downloads (pref key sv_wifi_only_downloads, default OFF)
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(sys.argv[1]).resolve()
MAIN = ROOT / 'app/src/main'
GP = MAIN / 'java/com/lagradost/cloudstream3/ui/player/GeneratorPlayer.kt'
DM = MAIN / 'java/com/lagradost/cloudstream3/utils/downloader/DownloadManager.kt'
LAYOUTS = [MAIN / 'res/layout/fragment_player.xml', MAIN / 'res/layout/fragment_player_tv.xml']


def read(p):
    return pathlib.Path(p).read_bytes().decode('utf-8').replace('\r\n', '\n')


def write(p, s):
    pathlib.Path(p).write_bytes(s.encode('utf-8'))


def rep(s, old, new, expect=1, name=''):
    k = s.count(old)
    if k != expect:
        raise SystemExit(f'PATCH FAILED: expected {expect}x, found {k}x: {old[:80]!r} in {name}')
    return s.replace(old, new)


# ---------------------------------------------------------------- layouts: Quality button
QUALITY_BTN = '''                    <com.google.android.material.button.MaterialButton
                        android:id="@+id/sv_btn_quality"
                        style="@style/BlackButton"
                        android:layout_width="wrap_content"
                        android:layout_height="wrap_content"
                        android:layout_marginEnd="8dp"
                        android:text="Quality"
                        android:textAllCaps="false"
                        android:textSize="13sp"
                        app:cornerRadius="22dp" />
'''


def patch_layouts():
    for p in LAYOUTS:
        s = read(p)
        if 'sv_btn_quality' in s:
            continue
        i = s.find('android:id="@+id/sv_btn_tracks"')
        if i < 0:
            raise SystemExit(f'PATCH FAILED: sv_btn_tracks not found in {p.name} (run apply_player.py first)')
        start = s.rfind('<com.google.android.material.button.MaterialButton', 0, i)
        # keep the indentation of the existing button
        line_start = s.rfind('\n', 0, start) + 1
        s = s[:line_start] + QUALITY_BTN + s[line_start:]
        write(p, s)


# ---------------------------------------------------------------- GeneratorPlayer.kt
GP_HELPERS = '''    // ======================= StreamVerse features (Hindi first + portrait quality) =======================
    private val svHindiStrict = Regex("""(^|[^a-z])(hindi|hin|hi-in)([^a-z]|$)|हिंदी""")
    private val svHindiLoose = Regex("""(^|[^a-z])(dual audio|multi audio)([^a-z]|$)""")
    private var svHindiAudioApplied = false
    private var svHindiSubApplied = false

    private fun svLinkText(d: DisplayLink): String {
        val l = d.link.first
        val name = if (l != null) "${l.name} ${l.source}" else (d.link.second?.name ?: "")
        return name.lowercase()
    }

    /** 0 = labelled Hindi, 1 = dual / multi audio, 2 = everything else */
    private fun svHindiRank(d: DisplayLink): Int {
        val t = svLinkText(d)
        return when {
            svHindiStrict.containsMatchIn(t) -> 0
            svHindiLoose.containsMatchIn(t) -> 1
            else -> 2
        }
    }

    private fun svBadge(d: DisplayLink): String {
        return when (svHindiRank(d)) {
            0 -> "[Hindi] "
            1 -> "[Dual] "
            else -> ""
        }
    }

    /** Same order as the normal sorting, but Hindi links first (sortedBy is stable). */
    private fun svSortLinks(profile: Int): List<DisplayLink> =
        viewModel.state.sortLinks(profile).sortedBy { svHindiRank(it) }

    private fun svIsHindiAudio(language: String?, label: String?): Boolean {
        val lang = language?.trim()?.lowercase().orEmpty()
        if (lang == "hi" || lang == "hin" || lang == "hindi" || lang.startsWith("hi-") || lang.startsWith("hi_")) {
            return true
        }
        return label?.contains("hindi", ignoreCase = true) == true || label?.contains("हिंदी") == true
    }

    private fun svIsHindiSub(s: SubtitleData): Boolean =
        s.matchesLanguageCode("hi") ||
                s.originalName.contains("hindi", ignoreCase = true) ||
                s.originalName.contains("हिंदी")

    /** Returns true when Hindi subtitles are (or already were) selected, so other auto select is skipped. */
    private fun svAutoSelectHindiSubtitle(): Boolean {
        if (svHindiSubApplied) return true
        // null / "" = the user chose "no subtitles", respect that
        if (preferredAutoSelectSubtitles.isNullOrEmpty()) return false
        val hindi = sortSubs(viewModel.state.subtitles).firstOrNull { svIsHindiSub(it) } ?: return false
        val ctx = context ?: return false
        if (player.getCurrentPreferredSubtitle() == hindi) {
            svHindiSubApplied = true
            return true
        }
        if (!setSubtitles(hindi, false)) return false
        svHindiSubApplied = true
        player.saveData()
        player.reloadPlayer(ctx)
        player.handleEvent(CSPlayerEvent.Play)
        return true
    }

    /** Quality picker for the portrait panel. Falls back to the Sources list when the
     *  video has no selectable resolutions (most providers give one link per quality). */
    private fun svShowQualityDialog() {
        try {
            val tracks = player.getVideoTracks()
            val videos = tracks.allVideoTracks
                .filter { (it.height ?: NO_VALUE) > 0 && (it.width ?: NO_VALUE) > 0 }
                .sortedByDescending { it.height ?: 0 }
                .distinctBy { it.height }
            if (videos.size < 2) {
                showMirrorsDialogue()
                return
            }
            val names = videos.map { "${it.height}p" }
            val current = videos.indexOfFirst { it.id == tracks.currentVideoTrack?.id }.coerceAtLeast(0)
            activity?.showDialog(names, current, "Quality", true, {}) { index ->
                videos.getOrNull(index)?.let { v ->
                    val w = v.width ?: NO_VALUE
                    val h = v.height ?: NO_VALUE
                    if (w != NO_VALUE && h != NO_VALUE) {
                        player.setMaxVideoSize(w, h, v.id)
                    }
                }
            }
        } catch (e: Exception) {
            logError(e)
        }
    }

'''


def patch_generator_player():
    s = read(GP)
    if 'StreamVerse features (Hindi first' in s:
        print('GeneratorPlayer already patched, skipping')
        return
    n = 'GeneratorPlayer.kt'

    # helpers
    s = rep(s, '    override fun embeddedSubtitlesFetched(subtitles: List<SubtitleData>) {',
            GP_HELPERS + '    override fun embeddedSubtitlesFetched(subtitles: List<SubtitleData>) {', name=n)

    # 3. Hindi audio track by default
    s = rep(s, '''        if (tracks.allAudioTracks.any { it.language == preferredAudioTrackLanguage }) {
            player.setPreferredAudioTrack(preferredAudioTrackLanguage)
        }''', '''        // StreamVerse: prefer a Hindi audio track (once per loaded link)
        val svHindiTrack = tracks.allAudioTracks.firstOrNull { svIsHindiAudio(it.language, it.label) }
        if (svHindiTrack != null) {
            if (!svHindiAudioApplied) {
                svHindiAudioApplied = true
                if (!svIsHindiAudio(tracks.currentAudioTrack?.language, tracks.currentAudioTrack?.label)) {
                    player.setPreferredAudioTrack(svHindiTrack.language, svHindiTrack.id, svHindiTrack.formatIndex)
                }
            }
        } else if (tracks.allAudioTracks.any { it.language == preferredAudioTrackLanguage }) {
            player.setPreferredAudioTrack(preferredAudioTrackLanguage)
        }''', name=n)

    # reset the "applied" flags when a new link / episode is loaded
    s = rep(s, '''        isPlayerActive.set(true)
        // manage UI''', '''        isPlayerActive.set(true)
        svHindiAudioApplied = false
        if (!sameEpisode) svHindiSubApplied = false
        // manage UI''', name=n)

    # 1. Hindi links first everywhere links are sorted
    s, k1 = re.subn(r'viewModel\.state\.sortLinks\(currentQualityProfile\)', 'svSortLinks(currentQualityProfile)', s)
    s, k2 = re.subn(r'viewModel\.state\.sortLinks\(qualityProfile\)', 'svSortLinks(qualityProfile)', s)
    if k1 < 4 or k2 < 1:
        raise SystemExit(f'PATCH FAILED: sortLinks calls found {k1}+{k2}, expected 4+1 in {n}')
    # 2. badge in the Sources list
    s = rep(s, '"$name ${Qualities.getStringByInt(link?.quality)}"',
            'svBadge(displayLink) + "$name ${Qualities.getStringByInt(link?.quality)}"', name=n)

    # 4. Hindi subtitles by default
    s = rep(s, 'if (!autoSelectFromSettings()) {',
            'if (!svAutoSelectHindiSubtitle() && !autoSelectFromSettings()) {', name=n)

    # 5. Quality button wiring
    s = rep(s, '        super.onBindingCreated(binding, savedInstanceState)\n',
            '        super.onBindingCreated(binding, savedInstanceState)\n'
            '        binding.svBtnQuality.setOnClickListener { svShowQualityDialog() }\n', name=n)
    write(GP, s)


# ---------------------------------------------------------------- DownloadManager.kt
DM_HELPERS = '''// StreamVerse: download quality preference, first match wins (change the list to taste).
private val SV_DOWNLOAD_PREFERRED_QUALITIES = listOf(1080, 720)

private fun svDownloadQualityRank(link: ExtractorLink): Int {
    val idx = SV_DOWNLOAD_PREFERRED_QUALITIES.indexOf(link.quality)
    return if (idx >= 0) idx else SV_DOWNLOAD_PREFERRED_QUALITIES.size
}

// StreamVerse: true when Wi-Fi only downloads are on (default) and the device is not on Wi-Fi / unmetered network.
private fun svWifiOnlyBlocked(context: Context): Boolean {
    val prefs = PreferenceManager.getDefaultSharedPreferences(context)
    if (!prefs.getBoolean("sv_wifi_only_downloads", false)) return false
    if (SDK_INT < Build.VERSION_CODES.M) return false
    val cm = context.getSystemService(Context.CONNECTIVITY_SERVICE) as? android.net.ConnectivityManager
        ?: return false
    val caps = cm.getNetworkCapabilities(cm.activeNetwork) ?: return false
    val allowed = caps.hasTransport(android.net.NetworkCapabilities.TRANSPORT_WIFI) ||
            caps.hasTransport(android.net.NetworkCapabilities.TRANSPORT_ETHERNET) ||
            caps.hasCapability(android.net.NetworkCapabilities.NET_CAPABILITY_NOT_METERED)
    return !allowed
}

'''


def patch_download_manager():
    s = read(DM)
    n = 'DownloadManager.kt'
    if 'svWifiOnlyBlocked' in s:
        print('DownloadManager already patched, skipping')
        return
    if 'isStreamVerseHindiAudio' not in s:
        raise SystemExit('PATCH FAILED: run apply_hindi_audio_download.py before this script')

    anchor = 'const val DOWNLOAD_CHANNEL_ID = "cloudstream3.general"'
    s = rep(s, anchor, DM_HELPERS + anchor, name=n)

    # 6. quality preference on top of the Hindi filter
    s, k = re.subn(
        r'val hindiLinks = links\.filter \{ isStreamVerseHindiAudio\(it\) \}(\.ifEmpty \{ links \})?',
        lambda m: m.group(0) + '.sortedBy { svDownloadQualityRank(it) }', s, count=1)
    if k != 1:
        raise SystemExit('PATCH FAILED: hindiLinks line not found in ' + n)

    # 7. Wi-Fi only
    s = rep(s, '''            ioSafe {
                if (downloadQueueWrapper.resumePackage != null) {''', '''            ioSafe {
                if (svWifiOnlyBlocked(context)) {
                    main {
                        showToast("Wi-Fi only downloads: connect to Wi-Fi first", Toast.LENGTH_LONG)
                    }
                    isFailed = true
                    return@ioSafe
                }
                if (downloadQueueWrapper.resumePackage != null) {''', name=n)
    write(DM, s)


def main():
    patch_layouts()
    patch_generator_player()
    patch_download_manager()
    print('SUCCESS: StreamVerse features applied')


main()
