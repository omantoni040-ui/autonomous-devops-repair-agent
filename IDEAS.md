# Project Ideas

This file lists practical next steps for improving the Autonomous DevOps Repair Agent. The focus is to keep the project useful, demo-friendly, and safe for production-style VPS operations.

## 1. Web dashboard

Build a small dashboard that shows the latest scan status, risk score, open warnings, and generated incident reports.

Useful features:

- latest server health summary
- risk score timeline
- warning and critical issue list
- links to Markdown/JSON reports
- simple mobile-friendly UI for quick checks

Why it helps: makes the project easier to demo and easier to use without opening the terminal every time.

## 2. Scheduled health checks

Add a cron-friendly command that runs scans automatically every few minutes or hours.

Useful features:

- `vps_doctor.py schedule-check`
- daily report rotation
- configurable scan interval
- alert only when status changes from healthy to warning/critical
- keep last N reports to avoid disk bloat

Why it helps: turns the tool from manual scanner into lightweight monitoring.

## 3. Service-specific playbooks

Add reusable recovery playbooks for common production problems.

Example playbooks:

- Docker container down
- Nginx/Apache port closed
- disk usage above threshold
- failed systemd service
- domain DNS not resolving
- high memory usage

Why it helps: operators get clearer next steps instead of generic advice.

## 4. Config file support

Add a `config.yaml` or `config.json` file so users can define what their server should look like.

Example config options:

- required ports: `80`, `443`, `22`
- required systemd services
- expected Docker containers
- domains to check
- disk and memory thresholds
- Telegram alert settings

Why it helps: each VPS can have its own expected baseline.

## 5. Auto-generated incident timeline

Improve reports by showing a timeline of what the agent checked and what it found.

Example timeline:

```text
01:00:02 checked disk usage
01:00:03 checked memory usage
01:00:04 checked required ports
01:00:05 detected port 443 closed
01:00:06 wrote incident report
```

Why it helps: reports become more trustworthy and easier to review after an incident.

## 6. Safe fix preview mode

Add a command that shows proposed repair commands without executing them.

Example:

```bash
python3 vps_doctor.py fix-plan --issue closed-port-443
```

The output should include:

- what command might fix the issue
- why the command is suggested
- risk level
- rollback note
- manual approval reminder

Why it helps: gives operators speed while avoiding blind automated changes.

## 7. Multi-server mode

Support checking multiple VPS targets from one control machine.

Useful features:

- server list file
- SSH-based scan runner
- per-server reports
- combined fleet summary
- Telegram alert showing which server failed

Why it helps: one operator can monitor multiple small production servers.

## 8. GitHub Actions demo

Add a GitHub Actions workflow that runs a safe demo scan on every push.

Useful features:

- syntax check
- test report generation
- upload sample reports as artifacts
- verify Markdown output exists

Why it helps: makes the repo look more complete and proves the project works automatically.

## 9. Report archive page

Generate a static HTML page from saved reports.

Useful features:

- list previous incidents
- filter by status: healthy, warning, critical
- show risk score per report
- link to original Markdown and JSON files

Why it helps: gives the project a simple reporting UI without needing a database.

## 10. Plugin-style checks

Refactor checks into a plugin pattern so new checks can be added easily.

Example structure:

```text
checks/
  disk.py
  memory.py
  ports.py
  docker.py
  systemd.py
  dns.py
```

Why it helps: makes the project easier to extend and more professional.

## Recommended build order

Best order for the next improvements:

1. Config file support
2. Scheduled health checks
3. Service-specific playbooks
4. Safe fix preview mode
5. Web dashboard or static report archive
6. GitHub Actions demo
7. Multi-server mode
8. Plugin-style checks

This order keeps the project realistic: first make it configurable, then automated, then easier to demo, then scalable.
