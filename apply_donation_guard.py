#!/usr/bin/env python3
"""
StreamVerse: auto-dismiss the donation / "support the repo" popup that CNCVerse extensions show.
    python3 apply_donation_guard.py <cloudstream-source>
Those plugins show a DialogFragment named com.cncverse.donation.DonationDialogFragment.
The app watches every fragment that opens and dismisses any DialogFragment whose class name contains "donat".
(Covers the CNCVerse and Phisher extensions.)

The Desi extensions (OttSource, MovieBox, AniStream, SDmovies, StreamHubOne, The Movie Flix, WatchDrama, vegamovies)
show a Telegram popup (DesiExtensionPopup) at most once per 24 h. They remember the last time in the preferences file
"desi_extension_popup_prefs" (key "last_popup_shown_at"), so the app writes a far-future time there and the popup never counts as due.
"""
import pathlib
import sys

ROOT = pathlib.Path(sys.argv[1]).resolve()
HF = ROOT / 'app/src/main/java/com/lagradost/cloudstream3/ui/home/HomeFragment.kt'

HELPER = '''// ===== StreamVerse: dismiss donation popups shown by extensions =====
private var svGuardedFm: java.lang.ref.WeakReference<androidx.fragment.app.FragmentManager>? = null
private val svDonationRegex = Regex("donat", RegexOption.IGNORE_CASE)

/** Desi extensions: pretend their popup was just shown, so it is never due again. */
fun svBlockDesiPopup(context: Context) {
    try {
        context.applicationContext
            .getSharedPreferences("desi_extension_popup_prefs", Context.MODE_PRIVATE)
            .edit()
            .putLong("last_popup_shown_at", Long.MAX_VALUE / 4)
            .apply()
    } catch (_: Throwable) {
    }
}

fun svInstallDonationGuard(activity: Activity?) {
    if (activity != null) svBlockDesiPopup(activity)
    val fm = (activity as? androidx.fragment.app.FragmentActivity)?.supportFragmentManager ?: return
    if (svGuardedFm?.get() === fm) return
    svGuardedFm = java.lang.ref.WeakReference(fm)
    fm.registerFragmentLifecycleCallbacks(
        object : androidx.fragment.app.FragmentManager.FragmentLifecycleCallbacks() {
            override fun onFragmentCreated(
                fm: androidx.fragment.app.FragmentManager,
                f: androidx.fragment.app.Fragment,
                savedInstanceState: Bundle?
            ) {
                if (f is androidx.fragment.app.DialogFragment &&
                    svDonationRegex.containsMatchIn(f.javaClass.name)
                ) {
                    f.dismissAllowingStateLoss()
                }
            }
        },
        true
    )
}

'''

s = HF.read_bytes().decode('utf-8').replace('\r\n', '\n')
if 'svInstallDonationGuard' in s:
    print('donation guard already applied, skipping')
    raise SystemExit(0)


def rep(s, old, new):
    if s.count(old) != 1:
        raise SystemExit(f'PATCH FAILED: expected 1x, found {s.count(old)}x: {old[:70]!r}')
    return s.replace(old, new)


s = rep(s, 'private const val TAG = "HomeFragment"', HELPER + 'private const val TAG = "HomeFragment"')
s = rep(s, '''    override fun onBindingCreated(binding: FragmentHomeBinding) {
        context?.let { HomeChildItemAdapter.updatePosterSize(it) }
''', '''    override fun onBindingCreated(binding: FragmentHomeBinding) {
        context?.let { HomeChildItemAdapter.updatePosterSize(it) }
        svInstallDonationGuard(activity)
''')
HF.write_bytes(s.encode('utf-8'))
print('StreamVerse donation guard applied OK')
