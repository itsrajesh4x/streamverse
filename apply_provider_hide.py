#!/usr/bin/env python3
"""
StreamVerse: remove a provider from the Provider Selection list.  python3 apply_provider_hide.py <cloudstream-source>
  * swipe a provider row left or right -> confirm -> the provider is hidden (the extension stays installed)
  * long-press "None" / "Random" -> shows hidden providers and "Restore all"
  * stored in app preferences (key sv_hidden_providers); helpers svGetHiddenProviders / svSetHiddenProviders
    are public so other screens (Provider test) can use the same list
"""
import pathlib
import sys

ROOT = pathlib.Path(sys.argv[1]).resolve()
HF = ROOT / 'app/src/main/java/com/lagradost/cloudstream3/ui/home/HomeFragment.kt'


def rep(s, old, new, name):
    k = s.count(old)
    if k != 1:
        raise SystemExit(f'PATCH FAILED: expected 1x, found {k}x: {old[:80]!r} in {name}')
    return s.replace(old, new)


HELPERS = '''// ===== StreamVerse: hidden providers =====
private const val SV_HIDDEN_PROVIDERS_KEY = "sv_hidden_providers"

fun svGetHiddenProviders(context: Context): Set<String> =
    PreferenceManager.getDefaultSharedPreferences(context)
        .getStringSet(SV_HIDDEN_PROVIDERS_KEY, emptySet())?.toSet() ?: emptySet()

fun svSetHiddenProviders(context: Context, names: Set<String>) {
    PreferenceManager.getDefaultSharedPreferences(context).edit()
        .putStringSet(SV_HIDDEN_PROVIDERS_KEY, names.toSet()).apply()
}

/** Asks for confirmation, then hides the provider. [onDone] runs after it was hidden. */
fun svConfirmHideProvider(context: Context, providerName: String, onDone: () -> Unit) {
    AlertDialog.Builder(context)
        .setTitle("Delete provider?")
        .setMessage("Remove \\"$providerName\\" from the list? The extension stays installed.")
        .setPositiveButton(R.string.delete) { _, _ ->
            svSetHiddenProviders(context, svGetHiddenProviders(context) + providerName)
            onDone()
        }
        .setNegativeButton(R.string.cancel, null)
        .show()
}

/** Lists the hidden providers and offers to bring them all back. */
fun svShowRestoreHiddenDialog(context: Context, onDone: () -> Unit) {
    val hidden = svGetHiddenProviders(context)
    if (hidden.isEmpty()) return
    AlertDialog.Builder(context)
        .setTitle("Hidden providers (${hidden.size})")
        .setMessage(hidden.sorted().joinToString("\\n"))
        .setPositiveButton("Restore all") { _, _ ->
            svSetHiddenProviders(context, emptySet())
            onDone()
        }
        .setNegativeButton(R.string.cancel, null)
        .show()
}

'''

SWIPE = '''                // StreamVerse: swipe a provider row left / right to hide it
                if (listView != null) {
                    val svCtx = dialog.context
                    val svDetector = android.view.GestureDetector(
                        svCtx,
                        object : android.view.GestureDetector.SimpleOnGestureListener() {
                            override fun onDown(e: android.view.MotionEvent): Boolean = true

                            override fun onFling(
                                e1: android.view.MotionEvent?,
                                e2: android.view.MotionEvent,
                                velocityX: Float,
                                velocityY: Float
                            ): Boolean {
                                if (e1 == null) return false
                                val dx = e2.x - e1.x
                                val dy = e2.y - e1.y
                                if (kotlin.math.abs(dx) < 120.toPx || kotlin.math.abs(dx) < kotlin.math.abs(dy) * 2f) {
                                    return false
                                }
                                val pos = listView.pointToPosition(e1.x.toInt(), e1.y.toInt())
                                // 0 = None, 1 = Random, they can not be removed
                                if (pos <= 1 || pos >= currentValidApis.size) return false
                                val api = currentValidApis[pos]
                                if (api.name == currentApiName) {
                                    showToast("The selected provider can not be removed", Toast.LENGTH_SHORT)
                                    return true
                                }
                                svConfirmHideProvider(svCtx, api.name) { updateList() }
                                return true
                            }
                        })
                    listView.setOnTouchListener { _, ev ->
                        svDetector.onTouchEvent(ev)
                        false // never consume, normal click / scroll keep working
                    }
                }

'''


def main():
    s = HF.read_bytes().decode('utf-8').replace('\r\n', '\n')
    n = 'HomeFragment.kt'
    if 'svConfirmHideProvider' in s:
        print('HomeFragment already patched, skipping')
        return

    s = rep(s, 'private const val TAG = "HomeFragment"', HELPERS + 'private const val TAG = "HomeFragment"', n)

    # hidden providers are not listed
    s = rep(s, '''                    val sortedApis = validAPIs
                        .filter {
''', '''                    val svHidden = svGetHiddenProviders(this@selectHomepage)
                    val sortedApis = validAPIs
                        .filter {
                            if (svHidden.contains(it.name)) return@filter false
''', n)

    # long press on None / Random -> restore dialog (long press on providers still pins them)
    s = rep(s, '''                listView?.setOnItemLongClickListener { _, _, i, _ ->
                    if (currentValidApis.isNotEmpty() && i > 1) {''', '''                listView?.setOnItemLongClickListener { _, _, i, _ ->
                    if (i <= 1 && svGetHiddenProviders(dialog.context).isNotEmpty()) {
                        svShowRestoreHiddenDialog(dialog.context) { updateList() }
                        return@setOnItemLongClickListener true
                    }
                    if (currentValidApis.isNotEmpty() && i > 1) {''', n)

    # swipe to hide
    s = rep(s, '''                bindChips(
                    binding.tvtypesChipsScroll.tvtypesChips,''', SWIPE + '''                bindChips(
                    binding.tvtypesChipsScroll.tvtypesChips,''', n)

    HF.write_bytes(s.encode('utf-8'))
    print('StreamVerse provider hide applied OK')


main()
