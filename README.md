# FitMomTrader input feed — development only

This repository currently contains an offline admission validator and synthetic fault tests. It is NOT a working input feed, publisher, or MT5 updater. No production input package is supplied. It cannot resume trading.

Run `python -m unittest discover -s src -p "test_*.py"`.

The admission-test workflow runs tests on repository changes and manual dispatch. A separate public-source evidence workflow requests four official sources every six hours and on relevant code changes. It reports retrieval failures and hashes, but semantic source validation is not implemented. Successful retrieval does NOT validate a trading calendar. Neither workflow reads broker accounts, obtains credentials, publishes trading inputs, or alters trading decisions. GitHub schedule delivery is not guaranteed and the runtime consumer must enforce expiry independently. Source adapters, publisher authentication, cryptographic verification, native cache integration and hosted fault testing remain required.

The validator's `signature_verified` parameter is a caller contract; it is NOT signature verification. Never pass true merely because a package arrived over HTTPS. Source hashes establish provenance only, not correctness or complete news coverage. Synthetic fixtures use example.invalid and are not real calendars.

Production policy must remain DEMO-only, original exits and quantities, and unchanged risk settings. Feed packages cannot contain risk-counter updates. Missing or expired critical inputs must block new entries. A bounded last-known-good cache must never have its expiry extended by a retry or reboot.

Do not upload account history, balances, account IDs, passwords, API tokens, private signing keys, broker connection databases, risk snapshots or VPS journals.

