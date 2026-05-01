# Demo Proof Script

Use this sequence to create screenshots for the Max Monthly Plan submission.

```bash
git clone https://github.com/omantoni040-ui/autonomous-devops-repair-agent.git
cd autonomous-devops-repair-agent
python3 vps_doctor.py --help
python3 vps_doctor.py scan
python3 vps_doctor.py report
python3 vps_doctor.py demo-incident
python3 vps_doctor.py notify-telegram --dry-run
```

Screenshot targets:

1. Terminal output from `scan`.
2. Terminal output showing saved report paths.
3. Open generated `reports/incident-*.md`.
4. Open generated `reports/scan-*.json`.
5. Open `incidents/demo-disk-pressure.md`.

Form choices:

- Agent tool: Hermes Agent
- Model series: GPT, DeepSeek, Claude, or Other depending actual usage
- Project link/demo URL: GitHub repo URL after pushing this folder
