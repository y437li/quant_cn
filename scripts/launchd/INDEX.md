# scripts/launchd/

macOS launchd job templates. `make track-install` / `make report-install` fill in the paths and load them; `make track-uninstall` unloads and deletes the track job, `make report-uninstall` only unloads the report job.

## Files
| File | Purpose | Contains |
|---|---|---|
| `daily_track.plist.template` | weekday 06:00 (US Eastern, after the China close) job running `make track-daily`: every daily market dataset, 观察账本, ETF proxy, macro, futures, risk model, holdings; started through /bin/zsh, which needs Full Disk Access (plan 15 ph7b, D-126, D-165) | `com.quantcn.daily-track` |
| `morning_report.plist.template` | weekday 08:00 job running `make morning-report` (持仓监测 + 机会清单 e-mails; started through /bin/zsh, plan 15 ph7e, D-136, D-165) | `com.quantcn.morning-report` |
