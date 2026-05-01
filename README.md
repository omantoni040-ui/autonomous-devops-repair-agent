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

## Submission Pitch

**Project title:** Autonomous DevOps Repair Agent for Production Servers

**Short description:**

```text
I built an autonomous DevOps repair agent for production Linux servers. The agent monitors server health, Docker containers, systemd services, disk pressure, memory, CPU load, critical ports, domains, and application logs. When something breaks, it collects evidence, diagnoses likely root causes, writes a safe fix plan, and generates an incident report for operator approval.
```

**Long form answer:**

```text
I built an autonomous DevOps repair agent for production Linux servers. The project solves a common operational problem: small teams and solo builders often run multiple VPS services but do not have a full-time SRE to monitor, diagnose, and repair incidents.

The agent monitors Docker containers, systemd services, disk usage, memory, CPU load, critical ports, domain health, and server state. When something breaks, it collects evidence from the machine, classifies findings as healthy/warning/critical, identifies likely root causes, proposes a safe recovery plan, and generates Markdown/JSON incident reports. It can also send Telegram alerts for high-risk incidents.

The workflow is agent-driven: Hermes Agent is used as the coding and operations operator. It inspects the system, writes and modifies the diagnostic code, runs terminal verification, reviews outputs, creates incident artifacts, and prepares handoff notes. For production use, the agent separates diagnosis, risk analysis, fix planning, human approval, verification, and post-incident reporting.

The impact is practical: it reduces downtime, speeds up debugging, creates consistent incident reports, and lets one operator manage multiple production services without manually checking every log, service, and server metric by hand.
```

## Proof to upload

Recommended proof artifacts:

1. Terminal screenshot running:
   ```bash
   python3 vps_doctor.py scan
   python3 vps_doctor.py report
   ```
2. Screenshot of `reports/incident-*.md`.
3. Screenshot of `reports/scan-*.json`.
4. Screenshot of `incidents/demo-disk-pressure.md`.
5. Optional Telegram dry-run alert screenshot:
   ```bash
   python3 vps_doctor.py notify-telegram --dry-run
   ```
6. GitHub repo or live demo URL.

## Safe Recovery Policy

The agent is intentionally conservative:

- no destructive cleanup without approval
- no secret printing
- no automatic production restarts
- no database deletion
- no hardcoded credentials

It recommends commands and requires a human/operator to approve risky changes.
