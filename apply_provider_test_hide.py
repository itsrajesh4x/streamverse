#!/usr/bin/env python3
"""
StreamVerse: remove a provider from the Provider test screen.  Run AFTER apply_provider_hide.py:
    python3 apply_provider_test_hide.py <cloudstream-source>
  * long-press a provider -> "Delete provider?" -> it disappears from the list (the extension stays installed)
  * uses the same hidden list as Provider Selection; restore from Provider Selection (long-press None / Random)
"""
import pathlib
import sys

ROOT = pathlib.Path(sys.argv[1]).resolve()
D = ROOT / 'app/src/main/java/com/lagradost/cloudstream3/ui/settings/testing'
SCREEN = D / 'TestScreen.kt'
VM = D / 'TestViewModel2.kt'
HOME = ROOT / 'app/src/main/java/com/lagradost/cloudstream3/ui/home/HomeFragment.kt'


def rep(s, old, new, name):
    k = s.count(old)
    if k != 1:
        raise SystemExit(f'PATCH FAILED: expected 1x, found {k}x: {old[:80]!r} in {name}')
    return s.replace(old, new)


def read(p):
    return pathlib.Path(p).read_bytes().decode('utf-8').replace('\r\n', '\n')


def patch_screen():
    s = read(SCREEN)
    n = 'TestScreen.kt'
    if 'svDeleteShown' in s:
        print('TestScreen already patched, skipping')
        return

    s = rep(s, 'import androidx.compose.foundation.clickable\n',
            'import androidx.compose.foundation.clickable\n'
            'import androidx.compose.foundation.combinedClickable\n'
            'import androidx.compose.ui.platform.LocalContext\n'
            'import com.lagradost.cloudstream3.ui.home.svGetHiddenProviders\n'
            'import com.lagradost.cloudstream3.ui.home.svSetHiddenProviders\n', n)

    # hidden providers are not listed
    s = rep(s, '''        LaunchedEffect(Unit) {
            viewModel.onAction(TestAction.Init(allProviders.withLock { allProviders.toPersistentList() }))
        }''', '''        val svContext = LocalContext.current
        LaunchedEffect(Unit) {
            val svHidden = svGetHiddenProviders(svContext)
            viewModel.onAction(
                TestAction.Init(
                    allProviders.withLock { allProviders.toPersistentList() }
                        .filter { api -> !svHidden.contains(api.name) }
                )
            )
        }''', n)

    # long press -> delete dialog
    s = rep(s, '''    @Composable
    fun TestResult(
        result: ImmutableTestResult,
        onAction: (TestAction) -> Unit,
        modifier: Modifier = Modifier,
    ) {
        var dialogShown by remember { mutableStateOf(false) }
''', '''    @OptIn(androidx.compose.foundation.ExperimentalFoundationApi::class)
    @Composable
    fun TestResult(
        result: ImmutableTestResult,
        onAction: (TestAction) -> Unit,
        modifier: Modifier = Modifier,
    ) {
        var dialogShown by remember { mutableStateOf(false) }
        var svDeleteShown by remember { mutableStateOf(false) }
        val svContext = LocalContext.current

        if (svDeleteShown) {
            AlertDialog(
                containerColor = MaterialTheme.colorScheme.background,
                onDismissRequest = { svDeleteShown = false },
                title = { Text(text = "Delete provider?") },
                text = { Text(text = "Remove \\"${result.name}\\" from the list? The extension stays installed.") },
                confirmButton = {
                    WhiteButton(text = stringResource(R.string.delete)) {
                        svSetHiddenProviders(svContext, svGetHiddenProviders(svContext) + result.name)
                        onAction(TestAction.Hide(result.uuid))
                        svDeleteShown = false
                    }
                },
                dismissButton = {
                    BlackButton(
                        text = stringResource(R.string.cancel),
                        onClick = { svDeleteShown = false },
                    )
                },
            )
        }
''', n)

    s = rep(s, '''                .clickable(onClick = {
                    dialogShown = !dialogShown
                })''', '''                .combinedClickable(
                    onClick = { dialogShown = !dialogShown },
                    onLongClick = { svDeleteShown = true },
                )''', n)
    SCREEN.write_bytes(s.encode('utf-8'))


def patch_vm():
    s = read(VM)
    n = 'TestViewModel2.kt'
    if 'TestAction.Hide' in s:
        print('TestViewModel2 already patched, skipping')
        return

    s = rep(s, '    data class Search(val query: String) : TestAction()\n',
            '    data class Search(val query: String) : TestAction()\n'
            '    data class Hide(val uuid: Uuid) : TestAction()\n', n)

    s = rep(s, '            is TestAction.Search -> {\n', '''            is TestAction.Hide -> {
                viewModelScope.launch {
                    dispatcher.cancelOne(action.uuid)
                }
                updateState {
                    copy(
                        internalApis = internalApis.remove(action.uuid),
                        items = items.setTo(items.data.toPersistentMap().remove(action.uuid)),
                    )
                }
            }

            is TestAction.Search -> {
''', n)
    VM.write_bytes(s.encode('utf-8'))


def main():
    if 'svGetHiddenProviders' not in read(HOME):
        raise SystemExit('PATCH FAILED: run apply_provider_hide.py before this script')
    patch_screen()
    patch_vm()
    print('StreamVerse provider test hide applied OK')


main()
