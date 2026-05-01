# Autonomous DevOps Repair Agent for Production Servers

A proof-ready agent project designed for submissions that ask: **"Tell us what you built with agents."**

This project demonstrates an AI-driven DevOps workflow where an agent scans a Linux VPS, diagnoses likely production issues, creates an incident report, and prepares safe recovery recommendations.

## Why this is interesting

Small operators often run multiple services on a VPS without a full-time SRE. This agent acts like a lightweight incident commander:

- checks disk, memory, CPU load
- checks important ports
- checks configured systemd services
- checks Docker container health
- checks domain DNS resolution
- generates Markdown + JSON incident reports
- creates proof artifacts for review
- optionally sends Telegram alerts

It is **safe by default**: it does not delete files, restart production services, rotate secrets, or change live configs automatically.

## Quick Start

```bash
git clone https://github.com/omantoni040-ui/autonomous-devops-repair-agent.git
cd autonomous-devops-repair-agent
python3 vps_doctor.py --help
python3 vps_doctor.py scan
python3 vps_doctor.py report
python3 vps_doctor.py demo-incident
python3 vps_doctor.py notify-telegram --dry-run
```

## Configuration

Edit `config.example.json` or copy it:

```bash
cp config.example.json config.json
```

Example:

```json
{
  "ports": [80, 443, 3000],
  "services": ["nginx", "docker"],
  "domains": ["example.com"]
}
```

Run with custom config:

```bash
python3 vps_doctor.py --config config.json report
```

## Telegram Notification

Set env vars:

```bash
export TELEGRAM_BOT_TOKEN="REDACTED"
export TELEGRAM_CHAT_ID="REDACTED"
python3 vps_doctor.py notify-telegram
```

## What this repo is useful for

This repository is a practical starter kit for building a safe, agent-assisted DevOps monitoring and incident-response workflow on a Linux VPS.

Use it when you want to:

- quickly check whether a server is healthy or needs attention
- detect common VPS problems such as closed ports, high disk usage, memory pressure, failed systemd services, Docker issues, or DNS failures
- generate clean Markdown and JSON incident reports without manually collecting every metric
- prepare a safe recovery checklist before making risky production changes
- create proof artifacts for demos, grant submissions, hackathons, internal tools, or portfolio projects
- send optional Telegram alerts when a scan reports warning or critical findings

## How it works

```text
Scan server → classify risk → collect evidence → write report → suggest safe next steps → notify operator
```

The agent does not blindly modify production. It focuses on diagnosis, reporting, and operator-approved recovery. This makes it useful for solo builders, small teams, VPS operators, and anyone managing multiple services without a dedicated SRE.

## Example output

After running a scan, the tool prints a compact health summary and can save full artifacts:

```text
Status: critical | Risk: 55/100
- disk: healthy — Root disk usage is 31.24%
- memory: healthy — Memory usage is 4.67%
- ports: critical — Ports closed: 80, 443
- docker: warning — Docker command failed or permission denied

Saved JSON: reports/scan-YYYYMMDD-HHMMSS.json
Saved Markdown: reports/incident-YYYYMMDD-HHMMSS.md
```

## Why this matters

Small production servers often fail in simple but costly ways: a port is closed, disk fills up, Docker is unhealthy, a domain stops resolving, or a service silently dies. This repo turns those checks into a repeatable workflow that produces evidence, risk scoring, and clear next steps instead of scattered manual debugging.

## Demo checklist

You can demonstrate the project with a simple local or VPS run:

1. Run a health scan:
   ```bash
   python3 vps_doctor.py scan
   ```
2. Generate a full incident report:
   ```bash
   python3 vps_doctor.py report
   ```
3. Review the generated artifacts:
   - `reports/scan-*.json` for structured machine-readable findings
   - `reports/incident-*.md` for a human-readable incident summary
   - `incidents/demo-disk-pressure.md` for an example recovery scenario
4. Optional: test Telegram alert formatting without sending a real incident:
   ```bash
   python3 vps_doctor.py notify-telegram --dry-run
   ```

## Safety model

This project is designed to be safe by default. It diagnoses, reports, and recommends next steps, but avoids risky production actions unless an operator approves them.

Built-in safety rules:

- no destructive cleanup without approval
- no secrets printed in reports
- no automatic production restarts
- no database deletion actions
- no hardcoded credentials required
- no silent fixes without an audit trail

The goal is to help operators move faster during incidents while still keeping human approval in the loop for changes that can affect production.
