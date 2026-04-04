Calendar override architecture

- Path format: `calendar_overrides/<year>/<language>.json`
- Supported language file names: `English.json`, `Hindi.json`, `Odia.json`
- The app uses bundled local calendar files as the base.
- These override files are merged on top of the base.
- If the same date exists locally and in the override file, the override date fully replaces the local date entries.
- If a date exists only in the override file, it is added to the calendar.

Example:

```json
{
  "2026": {
    "04-03": [
      { "name": "Good Friday", "type": "public holiday" }
    ],
    "04-14": [
      { "name": "Baisakhi", "type": "festival" }
    ]
  }
}
```
