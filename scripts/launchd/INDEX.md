# scripts/launchd/

macOS launchd job templates. `make track-install` fills in the paths and loads them; `make track-uninstall` unloads them.

## Files
| File | Purpose | Contains |
|---|---|---|
| `daily_track.plist.template` | weekday 18:30 job running `make track-daily` (观察账本 + 国家队 ETF proxy, plan 15 ph7b, D-126) | `com.quantcn.daily-track` |
