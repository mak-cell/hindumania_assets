# Alarm & alert tones

Devotional tones for the HinduMania Morning Alarm and event / reminder alerts.
The app downloads these on demand, verifies each file's SHA-256 (listed in
`tones.json` and pinned in the app), and keeps them on the device.

- `<id>_v1.ogg` — full alarm tone (loops until the alarm is dismissed)
- `<id>_short_v1.ogg` — short variant for event and reminder notifications

All tones are synthesised by `gen_tones.py` (no samples or recordings), released
under CC0. Files are immutable: to change a tone, add a `_v2` file and bump the
app's catalog rather than overwriting — jsDelivr caches `@master` paths.
