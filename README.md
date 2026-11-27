# FitMomTrader input feed — development only

This repository currently contains an offline admission validator and synthetic fault tests. It is NOT a working input feed, publisher, or MT5 updater. No production input package is supplied. It cannot resume trading.

Run `python -m unittest discover -s src -p "test_*.py"`.

The CI workflow runs these tests on repository changes and manual dispatch. It does not schedule a refresh, read broker accounts, obtain credentials, publish inputs, or alter trading decisions. Source adapters, publisher authentication, cryptographic verification, native cache integration and hosted fault testing remain required.

The validator's `signature_verified` parameter is a caller contract; it is NOT signature verification. Never pass true merely because a package arrived over HTTPS. Source hashes establish provenance only, not correctness or complete news coverage. Synthetic fixtures use example.invalid and are not real calendars.

Production policy must remain DEMO-only, original exits and quantities, and unchanged risk settings. Feed packages cannot contain risk-counter updates. Missing or expired critical inputs must block new entries. A bounded last-known-good cache must never have its expiry extended by a retry or reboot.

Do not upload account history, balances, account IDs, passwords, API tokens, private signing keys, broker connection databases, risk snapshots or VPS journals.
