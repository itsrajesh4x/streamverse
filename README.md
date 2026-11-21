# StreamVerse

CloudStream-based media center with a StreamVerse identity (name, icon, splash) and a "liquid glass" look.
No video sources are bundled - you add your own extensions, same as CloudStream.

Build: Actions tab -> "Build StreamVerse" -> Run workflow. The signed APK appears under Releases.

Signing: add 3 repository secrets (Settings -> Secrets and variables -> Actions):
SV_KEYSTORE_BASE64, SV_KEYSTORE_PASSWORD, SV_KEY_ALIAS  (values are in SIGNING_SECRETS.txt - never commit that file).
