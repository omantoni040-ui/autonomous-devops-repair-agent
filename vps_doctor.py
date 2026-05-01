#!/usr/bin/env python3
"""Autonomous VPS Doctor Agent.

A safe-by-default DevOps diagnostic CLI for proving agentic server workflows:
scan services, diagnose likely incidents, create reports, and optionally notify
Telegram. It never performs destructive fixes; recovery commands are generated
as recommendations unless the operator runs them manually.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
import textwrap
import time
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "reports"
DEFAULT_INCIDENT_DIR = PROJECT_ROOT / "incidents"
DEFAULT_CONFIG = PROJECT_ROOT / "config.example.json"


@dataclass
class CheckResult:
    name: str
    status: str
    summary: str
    evidence: dict[str, Any] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)


@dataclass
class ScanReport:
    generated_at: str
    host: str
    platform: str
    checks: list[CheckResult]

    def risk_score(self) -> int:
        score = 0
        for check in self.checks:
            if check.status == "critical":
                score += 40
            elif check.status == "warning":
                score += 15
        return min(score, 100)

    def overall_status(self) -> str:
        statuses = {check.status for check in self.checks}
        if "critical" in statuses:
            return "critical"
        if "warning" in statuses:
            return "warning"
        return "healthy"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def run_command(command: list[str], timeout: int = 8) -> tuple[int, str]:
    """Run a read-only diagnostic command and return exit code + output."""
    try:
        proc = subprocess.run(
            command,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout,
        )
        return proc.returncode, proc.stdout.strip()
    except FileNotFoundError:
        return 127, f"command not found: {command[0]}"
    except subprocess.TimeoutExpired:
        return 124, f"timeout after {timeout}s: {' '.join(command)}"


def percent_to_status(value: float, warning: float, critical: float) -> str:
    if value >= critical:
        return "critical"
    if value >= warning:
        return "warning"
    return "healthy"


def check_disk() -> CheckResult:
    usage = shutil.disk_usage("/")
    used_pct = round((usage.used / usage.total) * 100, 2)
    status = percent_to_status(used_pct, warning=80, critical=92)
    recommendations: list[str] = []
    if status != "healthy":
        recommendations.extend(
            [
                "Inspect large directories: sudo du -xhd1 / | sort -h",
                "Check Docker usage: docker system df",
                "Clean only verified temporary/cache files; avoid deleting app data.",
            ]
        )
    return CheckResult(
        name="disk",
        status=status,
        summary=f"Root disk usage is {used_pct}%",
        evidence={
            "total_gb": round(usage.total / 1024**3, 2),
            "used_gb": round(usage.used / 1024**3, 2),
            "free_gb": round(usage.free / 1024**3, 2),
            "used_percent": used_pct,
        },
        recommendations=recommendations,
    )


def check_memory() -> CheckResult:
    meminfo = Path("/proc/meminfo")
    if not meminfo.exists():
        return CheckResult(
            name="memory",
            status="warning",
            summary="/proc/meminfo not available; memory check skipped",
        )

    values: dict[str, int] = {}
    for line in meminfo.read_text().splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0].rstrip(":") in {"MemTotal", "MemAvailable"}:
            values[parts[0].rstrip(":")] = int(parts[1])

    total = values.get("MemTotal", 0)
    available = values.get("MemAvailable", 0)
    if total <= 0:
        return CheckResult("memory", "warning", "Unable to parse memory info")

    used_pct = round(((total - available) / total) * 100, 2)
    status = percent_to_status(used_pct, warning=85, critical=95)
    recommendations = []
    if status != "healthy":
        recommendations.extend(
            [
                "Inspect top memory processes: ps aux --sort=-%mem | head -20",
                "Check container memory: docker stats --no-stream",
                "Consider adding swap or reducing worker concurrency.",
            ]
        )
    return CheckResult(
        name="memory",
        status=status,
        summary=f"Memory usage is {used_pct}%",
        evidence={
            "total_mb": round(total / 1024, 2),
            "available_mb": round(available / 1024, 2),
            "used_percent": used_pct,
        },
        recommendations=recommendations,
    )


def check_load() -> CheckResult:
    try:
        load1, load5, load15 = os.getloadavg()
    except OSError:
        return CheckResult("load", "warning", "Load average unavailable")
    cpu_count = os.cpu_count() or 1
    load_ratio = round((load5 / cpu_count) * 100, 2)
    status = percent_to_status(load_ratio, warning=120, critical=250)
    recommendations = []
    if status != "healthy":
        recommendations.extend(
            [
                "Inspect CPU-heavy processes: ps aux --sort=-%cpu | head -20",
                "Check recent logs for restart loops or traffic spikes.",
                "Scale workers or reduce concurrency if sustained.",
            ]
        )
    return CheckResult(
        name="load",
        status=status,
        summary=f"5-minute load is {load5:.2f} across {cpu_count} CPU(s)",
        evidence={"load1": load1, "load5": load5, "load15": load15, "cpu_count": cpu_count},
        recommendations=recommendations,
    )


def check_ports(ports: list[int]) -> CheckResult:
    evidence: dict[str, Any] = {}
    missing: list[int] = []
    for port in ports:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        try:
            result = sock.connect_ex(("127.0.0.1", port))
            open_ = result == 0
            evidence[str(port)] = "open" if open_ else "closed"
            if not open_:
                missing.append(port)
        finally:
            sock.close()

    if not ports:
        return CheckResult("ports", "healthy", "No ports configured for checking")

    status = "critical" if missing else "healthy"
    recommendations = []
    if missing:
        recommendations.extend(
            [
                f"Check listening services: ss -ltnp | grep -E ':({'|'.join(map(str, missing))})'",
                "Check reverse proxy and app service status.",
            ]
        )
    return CheckResult(
        name="ports",
        status=status,
        summary=(
            f"Ports closed: {', '.join(map(str, missing))}"
            if missing
            else f"All configured ports are open: {', '.join(map(str, ports))}"
        ),
        evidence=evidence,
        recommendations=recommendations,
    )


def check_systemd(services: list[str]) -> CheckResult:
    if not services:
        return CheckResult("systemd", "healthy", "No systemd services configured")
    if shutil.which("systemctl") is None:
        return CheckResult("systemd", "warning", "systemctl not available")

    evidence: dict[str, str] = {}
    failed: list[str] = []
    for service in services:
        code, output = run_command(["systemctl", "is-active", service], timeout=5)
        state = output.splitlines()[-1] if output else f"exit-{code}"
        evidence[service] = state
        if state != "active":
            failed.append(service)

    status = "critical" if failed else "healthy"
    recommendations = []
    for service in failed:
        recommendations.append(f"Inspect service: systemctl status {service} --no-pager")
        recommendations.append(f"Read logs: journalctl -u {service} -n 100 --no-pager")
    return CheckResult(
        name="systemd",
        status=status,
        summary=(f"Inactive services: {', '.join(failed)}" if failed else "All configured services active"),
        evidence=evidence,
        recommendations=recommendations,
    )


def check_docker() -> CheckResult:
    if shutil.which("docker") is None:
        return CheckResult("docker", "warning", "Docker not installed or not in PATH")

    code, ps_output = run_command(
        ["docker", "ps", "--format", "{{.Names}}|{{.Status}}"], timeout=10
    )
    if code != 0:
        return CheckResult(
            name="docker",
            status="warning",
            summary="Docker command failed or permission denied",
            evidence={"output": ps_output[:1200]},
            recommendations=["Check Docker daemon and user permissions: docker ps"],
        )

    unhealthy: list[str] = []
    containers: dict[str, str] = {}
    for line in ps_output.splitlines():
        if "|" not in line:
            continue
        name, status = line.split("|", 1)
        containers[name] = status
        if "unhealthy" in status.lower() or "restarting" in status.lower():
            unhealthy.append(name)

    status = "critical" if unhealthy else "healthy"
    recommendations = []
    for name in unhealthy:
        recommendations.append(f"Inspect container: docker logs --tail 100 {name}")
        recommendations.append(f"Check health: docker inspect --format='{{{{json .State.Health}}}}' {name}")
    return CheckResult(
        name="docker",
        status=status,
        summary=(f"Unhealthy containers: {', '.join(unhealthy)}" if unhealthy else "No unhealthy running containers detected"),
        evidence={"containers": containers},
        recommendations=recommendations,
    )


def check_domains(domains: list[str]) -> CheckResult:
    if not domains:
        return CheckResult("domains", "healthy", "No domains configured")

    evidence: dict[str, Any] = {}
    failed: list[str] = []
    for domain in domains:
        try:
            ip = socket.gethostbyname(domain)
            evidence[domain] = {"dns": "ok", "ip": ip}
        except OSError as exc:
            evidence[domain] = {"dns": "failed", "error": str(exc)}
            failed.append(domain)

    status = "critical" if failed else "healthy"
    recommendations = []
    if failed:
        recommendations.extend(
            [
                "Check DNS records at provider/Cloudflare.",
                "Verify nameservers and proxy status.",
            ]
        )
    return CheckResult(
        name="domains",
        status=status,
        summary=(f"DNS failed: {', '.join(failed)}" if failed else "All configured domains resolve"),
        evidence=evidence,
        recommendations=recommendations,
    )


def load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"ports": [80, 443], "services": [], "domains": []}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON config {path}: {exc}") from exc


def run_scan(config_path: Path) -> ScanReport:
    config = load_config(config_path)
    checks = [
        check_disk(),
        check_memory(),
        check_load(),
        check_ports([int(p) for p in config.get("ports", [])]),
        check_systemd([str(s) for s in config.get("services", [])]),
        check_docker(),
        check_domains([str(d) for d in config.get("domains", [])]),
    ]
    return ScanReport(
        generated_at=now_iso(),
        host=socket.gethostname(),
        platform=f"{platform.system()} {platform.release()}",
        checks=checks,
    )


def report_to_dict(report: ScanReport) -> dict[str, Any]:
    return {
        "generated_at": report.generated_at,
        "host": report.host,
        "platform": report.platform,
        "overall_status": report.overall_status(),
        "risk_score": report.risk_score(),
        "checks": [asdict(check) for check in report.checks],
    }


def render_markdown(report: ScanReport) -> str:
    lines = [
        "# Autonomous VPS Doctor Incident Report",
        "",
        f"- Generated: `{report.generated_at}`",
        f"- Host: `{report.host}`",
        f"- Platform: `{report.platform}`",
        f"- Overall status: **{report.overall_status().upper()}**",
        f"- Risk score: **{report.risk_score()}/100**",
        "",
        "## Executive Summary",
        "",
    ]
    critical = [c for c in report.checks if c.status == "critical"]
    warnings = [c for c in report.checks if c.status == "warning"]
    if not critical and not warnings:
        lines.append("All configured checks are healthy. No immediate action required.")
    else:
        if critical:
            lines.append(f"Critical findings: {len(critical)}. Immediate operator review recommended.")
        if warnings:
            lines.append(f"Warnings: {len(warnings)}. Monitor and schedule cleanup/follow-up.")
    lines.extend(["", "## Findings", ""])

    for check in report.checks:
        lines.extend(
            [
                f"### {check.name} — {check.status.upper()}",
                "",
                check.summary,
                "",
                "**Evidence:**",
                "```json",
                json.dumps(check.evidence, indent=2, sort_keys=True),
                "```",
                "",
            ]
        )
        if check.recommendations:
            lines.append("**Recommended next actions:**")
            for rec in check.recommendations:
                lines.append(f"- {rec}")
            lines.append("")

    lines.extend(
        [
            "## Safe Recovery Policy",
            "",
            "This agent is safe-by-default. It collects evidence and recommends actions. "
            "It does not delete data, reset git state, rotate secrets, or restart production "
            "services without explicit human approval.",
            "",
            "## Proof-of-Agent Workflow",
            "",
            "1. Agent scans system state using terminal/file tools.",
            "2. Agent classifies health findings into healthy/warning/critical.",
            "3. Agent generates root-cause hypotheses and safe next steps.",
            "4. Operator approves any risky fix before execution.",
            "5. Agent verifies status and writes a post-incident handoff.",
            "",
        ]
    )
    return "\n".join(lines)


def save_report(report: ScanReport, output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    json_path = output_dir / f"scan-{stamp}.json"
    md_path = output_dir / f"incident-{stamp}.md"
    json_path.write_text(json.dumps(report_to_dict(report), indent=2, sort_keys=True) + "\n")
    md_path.write_text(render_markdown(report))
    return json_path, md_path


def print_summary(report: ScanReport) -> None:
    print(f"Status: {report.overall_status()} | Risk: {report.risk_score()}/100")
    for check in report.checks:
        print(f"- {check.name}: {check.status} — {check.summary}")


def notify_telegram(message: str) -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        raise SystemExit("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID first.")
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": message}).encode()
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    req = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(req, timeout=10) as response:
        body = response.read().decode()
    print(body)


def build_demo_incident(incident_dir: Path) -> Path:
    incident_dir.mkdir(parents=True, exist_ok=True)
    path = incident_dir / "demo-disk-pressure.md"
    path.write_text(
        textwrap.dedent(
            """
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
            """
        ).strip()
        + "\n"
    )
    return path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Autonomous VPS Doctor Agent: scan, diagnose, report, notify."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help="JSON config path with ports/services/domains.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="Run read-only health checks and print summary.")
    scan.add_argument("--json", action="store_true", help="Print full JSON report.")

    report_cmd = sub.add_parser("report", help="Run scan and save JSON + Markdown report.")
    report_cmd.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)

    sub.add_parser("demo-incident", help="Create a demo incident note for proof upload.")

    notify = sub.add_parser("notify-telegram", help="Send latest scan summary to Telegram.")
    notify.add_argument("--dry-run", action="store_true", help="Print message only.")

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.command == "scan":
        report = run_scan(args.config)
        if args.json:
            print(json.dumps(report_to_dict(report), indent=2, sort_keys=True))
        else:
            print_summary(report)
        return 0 if report.overall_status() != "critical" else 1

    if args.command == "report":
        report = run_scan(args.config)
        json_path, md_path = save_report(report, args.output_dir)
        print_summary(report)
        print(f"Saved JSON: {json_path}")
        print(f"Saved Markdown: {md_path}")
        return 0 if report.overall_status() != "critical" else 1

    if args.command == "demo-incident":
        path = build_demo_incident(DEFAULT_INCIDENT_DIR)
        print(f"Created demo incident: {path}")
        return 0

    if args.command == "notify-telegram":
        report = run_scan(args.config)
        message = (
            "Autonomous VPS Doctor scan\n"
            f"Host: {report.host}\n"
            f"Status: {report.overall_status()}\n"
            f"Risk: {report.risk_score()}/100\n"
            f"Generated: {report.generated_at}"
        )
        if args.dry_run:
            print(message)
        else:
            notify_telegram(message)
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
