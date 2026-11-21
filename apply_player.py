#!/usr/bin/env python3
"""
StreamVerse YouTube-style player (run AFTER the other patches):  python3 apply_player.py <cloudstream-source>
Phones only. The video now opens in PORTRAIT: video on top (16:9), title + Sources / Subtitles / Speed / Episodes
buttons below on the glass wallpaper. The fullscreen button in the player controls (or turning the phone, or the
Episodes button) switches to landscape fullscreen; Back (or the same button) returns to portrait.
TV / emulator behaviour is unchanged.
"""
import re, sys, pathlib

ROOT = pathlib.Path(sys.argv[1]).resolve()
MAIN = ROOT / 'app/src/main'
RES = MAIN / 'res'
PL = MAIN / 'java/com/lagradost/cloudstream3/ui/player'

def read(p): return pathlib.Path(p).read_bytes().decode('utf-8')
def write(p, s): pathlib.Path(p).write_bytes(s.encode('utf-8'))
def sub(path, pattern, repl, count=1, flags=0):
    s = read(path); n, k = re.subn(pattern, repl, s, count=count, flags=flags)
    if k == 0: raise SystemExit(f'PATCH FAILED: {pattern[:80]!r} not found in {pathlib.Path(path).name}')
    write(path, n)
def add_imports(path, imports):
    s = read(path)
    for imp in imports:
        line = f'import {imp}'
        if line in s: continue
        s = re.sub(r'(^package [^\n]+\n)', r'\1\n' + line + '\n', s, count=1, flags=re.M)
    write(path, s)

BTN = '''                    <com.google.android.material.button.MaterialButton
                        android:id="@+id/%s"
                        style="@style/BlackButton"
                        android:layout_width="wrap_content"
                        android:layout_height="wrap_content"
                        android:layout_marginEnd="8dp"
                        android:text="%s"
                        android:textAllCaps="false"
                        android:textSize="13sp"
                        app:cornerRadius="22dp" />
'''
PANEL = '''
    <!-- StreamVerse: portrait (YouTube style) panel under the video -->
    <ScrollView
        android:id="@+id/sv_player_panel"
        android:layout_width="0dp"
        android:layout_height="0dp"
        android:background="?attr/svWallpaper"
        android:fillViewport="true"
        android:visibility="gone"
        app:layout_constraintBottom_toBottomOf="parent"
        app:layout_constraintEnd_toEndOf="parent"
        app:layout_constraintStart_toStartOf="parent"
        app:layout_constraintTop_toBottomOf="@id/player_view">

        <LinearLayout
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:orientation="vertical"
            android:padding="16dp">

            <TextView
                android:id="@+id/sv_player_title"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:ellipsize="end"
                android:maxLines="3"
                android:textColor="?attr/textColor"
                android:textSize="20sp"
                android:textStyle="bold" />

            <TextView
                android:id="@+id/sv_player_sub"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:layout_marginTop="4dp"
                android:alpha="0.7"
                android:textColor="?attr/textColor"
                android:textSize="13sp" />

            <HorizontalScrollView
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:layout_marginTop="16dp"
                android:scrollbars="none">

                <LinearLayout
                    android:layout_width="wrap_content"
                    android:layout_height="wrap_content"
                    android:orientation="horizontal">
''' + BTN % ('sv_btn_sources', 'Sources') + BTN % ('sv_btn_tracks', 'Subtitles / Audio') + BTN % ('sv_btn_speed', 'Speed') + BTN % ('sv_btn_episodes', 'Episodes') + '''                </LinearLayout>
            </HorizontalScrollView>
        </LinearLayout>
    </ScrollView>
'''

KOTLIN = '''
    // ======================= StreamVerse: YouTube style player (phones) =======================
    private var svPrevLightStatus: Boolean? = null

    private fun svIsInline(): Boolean {
        if (!isLayout(PHONE)) return false
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N && activity?.isInPictureInPictureMode == true) return false
        return resources.configuration.orientation == Configuration.ORIENTATION_PORTRAIT
    }

    protected fun svUpdatePanelTexts() {
        val b = binding ?: return
        val title = playerBinding?.playerVideoTitle?.text?.toString().orEmpty()
        val sub = playerBinding?.playerVideoTitleRez?.text?.toString().orEmpty()
        b.svPlayerTitle.text = title.ifBlank { sub }
        b.svPlayerSub.text = if (title.isBlank()) "" else sub
        b.svPlayerSub.isVisible = b.svPlayerSub.text.isNotBlank()
        b.svBtnEpisodes.isVisible = isThereEpisodes()
    }

    private fun svToggleFullscreen() {
        val act = activity ?: return
        act.requestedOrientation = if (svIsInline())
            ActivityInfo.SCREEN_ORIENTATION_SENSOR_LANDSCAPE
        else
            ActivityInfo.SCREEN_ORIENTATION_SENSOR_PORTRAIT
        rotatedManually = true
    }

    private fun svSetupPanel() {
        if (!isLayout(PHONE)) return
        val b = binding ?: return
        b.svBtnSources.setOnClickListener { playerBinding?.playerSourcesBtt?.performClick() }
        b.svBtnTracks.setOnClickListener { playerBinding?.playerTracksBtt?.performClick() }
        b.svBtnSpeed.setOnClickListener { playerBinding?.playerSpeedBtt?.performClick() }
        b.svBtnEpisodes.setOnClickListener {
            if (svIsInline()) {
                svToggleFullscreen()
                view?.postDelayed({ playerBinding?.playerEpisodesButton?.performClick() }, 900)
            } else {
                playerBinding?.playerEpisodesButton?.performClick()
            }
        }
        playerBinding?.playerFullscreen?.let { fs ->
            fs.isVisible = true
            fs.setOnClickListener { svToggleFullscreen() }
        }
        svUpdatePanelTexts()
    }

    private fun svRestoreStatusBar() {
        try {
            val win = activity?.window ?: return
            svPrevLightStatus?.let {
                androidx.core.view.WindowCompat.getInsetsController(win, win.decorView)?.isAppearanceLightStatusBars = it
            }
            svPrevLightStatus = null
        } catch (t: Throwable) {
            t.printStackTrace()
        }
    }

    private fun svApplyLayout() {
        if (!isLayout(PHONE)) return
        try {
            val b = binding ?: return
            val root = b.root as? androidx.constraintlayout.widget.ConstraintLayout ?: return
            val inline = svIsInline()
            b.svPlayerPanel.isVisible = inline
            val set = androidx.constraintlayout.widget.ConstraintSet()
            set.clone(root)
            for (id in intArrayOf(R.id.player_view, R.id.player_loading_overlay)) {
                set.constrainWidth(id, androidx.constraintlayout.widget.ConstraintSet.MATCH_CONSTRAINT)
                set.constrainHeight(id, androidx.constraintlayout.widget.ConstraintSet.MATCH_CONSTRAINT)
                if (inline) {
                    set.setDimensionRatio(id, "16:9")
                    set.clear(id, androidx.constraintlayout.widget.ConstraintSet.BOTTOM)
                } else {
                    set.setDimensionRatio(id, null)
                    set.connect(
                        id, androidx.constraintlayout.widget.ConstraintSet.BOTTOM,
                        androidx.constraintlayout.widget.ConstraintSet.PARENT_ID,
                        androidx.constraintlayout.widget.ConstraintSet.BOTTOM
                    )
                }
            }
            set.applyTo(root)
            root.setPadding(0, if (inline) (context?.getStatusBarHeight() ?: 0) else 0, 0, 0)
            // the bottom button row of the controller is replaced by the panel in portrait
            playerBinding?.playerControlsScroll?.isGone = inline
            playerBinding?.playerFullscreen?.setImageResource(
                if (inline) R.drawable.baseline_fullscreen_24 else R.drawable.baseline_fullscreen_exit_24
            )
            if (inline) activity?.showSystemUI() else activity?.hideSystemUI()
            val win = activity?.window
            if (win != null) {
                val ctrl = androidx.core.view.WindowCompat.getInsetsController(win, win.decorView)
                if (inline) {
                    if (svPrevLightStatus == null) svPrevLightStatus = ctrl?.isAppearanceLightStatusBars
                    ctrl?.isAppearanceLightStatusBars = false
                } else {
                    svPrevLightStatus?.let { ctrl?.isAppearanceLightStatusBars = it }
                    svPrevLightStatus = null
                }
            }
            svUpdatePanelTexts()
            playerHostView?.requestUpdateBrightnessOverlayOnNextLayout()
        } catch (t: Throwable) {
            t.printStackTrace()
        }
    }

'''

def main():
    if not (RES / 'values/sv_attrs.xml').exists(): raise SystemExit('run the other patches first')
    # ---- 1. panel in both player layouts (view-binding needs the same ids in the TV layout)
    for name in ('fragment_player.xml', 'fragment_player_tv.xml'):
        p = RES / 'layout' / name; s = read(p)
        if 'sv_player_panel' in s: raise SystemExit('already patched: ' + name)
        if '@+id/player_view"' not in s: raise SystemExit('player_view id missing in ' + name)
        i = s.rfind('</androidx.constraintlayout.widget.ConstraintLayout>')
        if i < 0: raise SystemExit('root closing tag not found in ' + name)
        write(p, s[:i] + PANEL + s[i:])

    # ---- 2. FullScreenPlayer
    fsp = PL / 'FullScreenPlayer.kt'
    add_imports(fsp, ['com.lagradost.cloudstream3.utils.UIHelper.showSystemUI',
                      'com.lagradost.cloudstream3.utils.UIHelper.getStatusBarHeight'])
    sub(fsp, r'(\n    override fun onConfigurationChanged\(newConfig: Configuration\) \{)', lambda m: KOTLIN + m.group(1))
    sub(fsp, r'(super\.onConfigurationChanged\(newConfig\)\r?\n)', r'\1        svApplyLayout()\n')
    sub(fsp, r'(playerHostView\?\.isFullScreen = true\r?\n)', r'\1        svSetupPanel()\n        svApplyLayout()\n')
    sub(fsp, r'(private fun updateOrientation\(ignoreDynamicOrientation: Boolean = false\) \{\r?\n)',
        r'\1        if (isLayout(PHONE)) return // StreamVerse: portrait first, orientation is user driven\n')
    sub(fsp, r'\} else \{(\s*)activity\?\.popCurrentPage\("FullScreenPlayer"\)',
        r'} else if (isLayout(PHONE) && resources.configuration.orientation == Configuration.ORIENTATION_LANDSCAPE) {\1svToggleFullscreen()\1} else {\1activity?.popCurrentPage("FullScreenPlayer")')
    sub(fsp, r'(playerHostView\?\.releaseOverlayLayoutListener\(\)\r?\n)(\s*)playerBinding = null', r'\1\2svRestoreStatusBar()\n\2playerBinding = null')

    # ---- 3. keep the system bars visible while inline (portrait)
    sub(PL / 'PlayerView.kt',
        r'(fun enterFullscreen\(updateOrientation: \(\) -> Unit = \{\}\) \{\r?\n\s*val activity = context as\? Activity\r?\n)(\s*)if \(isFullScreen\) \{\r?\n(\s*)activity\?\.hideSystemUI\(\)',
        lambda m: (m.group(1) + m.group(2) + 'val svInline = !isLayout(TV or EMULATOR) &&\n' + m.group(2) +
                   '    resources.configuration.orientation == android.content.res.Configuration.ORIENTATION_PORTRAIT\n' +
                   m.group(2) + 'if (isFullScreen) {\n' + m.group(3) + 'if (svInline) activity?.showSystemUI() else activity?.hideSystemUI()'))

    # ---- 4. keep the panel title in sync with the player title
    gp = PL / 'GeneratorPlayer.kt'
    sub(gp, r'(playerBinding\?\.playerVideoTitle\?\.text = playerVideoTitle\r?\n)', r'\1        svUpdatePanelTexts()\n')
    sub(gp, r'(isVisible = result\.isNotBlank\(\)\r?\n\s*\}\r?\n)', r'\1        svUpdatePanelTexts()\n')
    print('StreamVerse player patch applied OK')

main()
