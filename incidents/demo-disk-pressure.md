# Demo Incident: Disk Pressure on Production VPS

## Alert
Root disk usage reached 92% and Docker logs were growing quickly.

## Agent Investigation
- Checked `df -h` for filesystem usage.
- Checked `docker system df` for image/container/log storage.
- Checked top-level directory sizes with safe read-only commands.
- Identified rotated logs and stale build cache as likely contributors.

## Safe Fix Plan
1. Back up important app config.
2. Truncate only verified oversized container logs.
3. Prune unused Docker build cache, not volumes.
4. Re-run disk scan.
5. Create post-incident report and Telegram summary.

## Verification
- Disk usage dropped below warning threshold.
- Containers stayed healthy.
- No application data was deleted.
