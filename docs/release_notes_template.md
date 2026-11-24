# Pocket Ledger v{{VERSION}} (Windows x64)

Pocket Ledger is a private, local-only finance tracker. This release ships a
self-contained portable build and a per-user Windows installer; both use the
same application code and the supplied desktop icon.

## Highlights

- Desktop Qt interface with the violet / lime / black / white brand system.
- Database-backed dashboard with account/currency-scoped totals and date filters.
- Add, edit, delete, filter and import transactions with exact integer
  minor-unit money handling; grouping commas are accepted in manual amounts.
- Dashboard, accounts and transactions refresh after every data change.
- Windows title bar and taskbar use the supplied PC icon.
- User data is kept outside program files. Installed builds use
  `%LOCALAPPDATA%\Pocket Ledger\data`; portable builds use `data\` beside the
  extracted EXE.

## Artifacts

- `PocketLedger-v{{VERSION}}-win64-portable.zip` — extract anywhere and run
  `PocketLedger.exe`; no installation or admin rights required.
- `PocketLedger-v{{VERSION}}-win64-setup.exe` — standard per-user Windows
  installer with Start Menu shortcut, optional desktop shortcut and an
  Apps & Features uninstall entry.

## Upgrade notes

- Future installers use the same AppId, so they upgrade in place.
- Upgrades and uninstalls never delete `%LOCALAPPDATA%\Pocket Ledger\data`.
  Back up that folder before removing it manually.
- If you used the portable build, keep the whole extracted folder; its database
  lives in `data\` next to `PocketLedger.exe`.
- An explicit `POCKET_LEDGER_DB` environment variable still overrides the
  default location.

## Verify the download

`SHA256SUMS.txt` is published with the release. In PowerShell, from the folder
containing the downloads:

```powershell
Get-Content .\SHA256SUMS.txt
Get-FileHash .\PocketLedger-v{{VERSION}}-win64-portable.zip -Algorithm SHA256
Get-FileHash .\PocketLedger-v{{VERSION}}-win64-setup.exe -Algorithm SHA256
```

Compare each uppercase hash with its lowercase entry in `SHA256SUMS.txt` (the
comparison is case-insensitive). Do not run an artifact whose hash does not
match.
