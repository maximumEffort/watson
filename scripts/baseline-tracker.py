#!/usr/bin/env python3
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

WATSON_SCRIPTS = Path(__file__).parent
WATSON_HOME = WATSON_SCRIPTS.parent
BASELINE_FILE = WATSON_HOME / "state" / "baseline.json"
STATE_DIR = WATSON_HOME / "state"
STATE_DIR.mkdir(exist_ok=True)

def collect_cost():
    try:
        result = subprocess.run(["python3", str(WATSON_SCRIPTS / "cost-tracker.py")], capture_output=True, text=True, timeout=10)
        for line in result.stdout.split("\n"):
            if "$" in line:
                import re
                match = re.search(r"[\d.]+", line)
                if match:
                    return float(match.group())
        return 0.0
    except:
        return 0.0

def collect_cron_failures():
    try:
        result = subprocess.run(["python3", str(WATSON_SCRIPTS / "cron-monitor.py")], capture_output=True, text=True, timeout=10)
        return result.stdout.count("FAILED") + result.stdout.count("ERROR")
    except:
        return 0

def collect_session_duration():
    try:
        result = subprocess.run(["python3", str(WATSON_SCRIPTS / "session-inspector.py")], capture_output=True, text=True, timeout=10)
        line_count = len([l for l in result.stdout.split("\n") if l.strip()])
        return max(60, line_count * 10)
    except:
        return 0

def collect_peak_memory():
    try:
        status_file = Path("/home/kraetes/eve/state/eve-status.json")
        if status_file.exists():
            with open(status_file) as f:
                status = json.load(f)
                return status.get("memory_mb", 0)
    except:
        pass
    return 0

def load_baseline():
    if BASELINE_FILE.exists():
        try:
            with open(BASELINE_FILE) as f:
                return json.load(f)
        except:
            pass
    return {"entries": []}

def save_baseline(baseline):
    with open(BASELINE_FILE, "w") as f:
        json.dump(baseline, f, indent=2)

def calculate_7day_avg(baseline, metric):
    entries = baseline.get("entries", [])
    if not entries:
        return 0
    recent = entries[-7:]
    values = [e.get(metric, 0) for e in recent if metric in e]
    return sum(values) / len(values) if values else 0

def alert(message):
    alert_file = Path("/home/kraetes/eve/state/watson-inbox") / f"alert-{int(datetime.now().timestamp())}.json"
    alert_file.parent.mkdir(exist_ok=True)
    alert_data = {
        "id": f"baseline-alert-{int(datetime.now().timestamp())}",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "from": "watson",
        "severity": "warning",
        "message": message,
        "wants_reply": False
    }
    try:
        with open(alert_file, "w") as f:
            json.dump(alert_data, f)
    except:
        pass

def main():
    today = datetime.now().strftime("%Y-%m-%d")
    metrics = {
        "date": today,
        "cost_per_day": collect_cost(),
        "cron_failures": collect_cron_failures(),
        "avg_session_duration_sec": collect_session_duration(),
        "peak_memory_mb": collect_peak_memory()
    }

    baseline = load_baseline()
    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    baseline["entries"] = [e for e in baseline["entries"] if e.get("date", "") >= seven_days_ago]

    alerts = []
    if baseline["entries"]:
        for metric_key in ["cost_per_day", "cron_failures", "peak_memory_mb"]:
            avg = calculate_7day_avg(baseline, metric_key)
            current = metrics[metric_key]
            if avg > 0 and current > 2 * avg:
                metric_name = metric_key.replace("_", " ").title()
                alerts.append(f"{metric_name}: {current:.1f} (avg: {avg:.1f})")

    baseline["entries"].append(metrics)
    baseline["last_update"] = datetime.utcnow().isoformat() + "Z"
    baseline["7day_averages"] = {
        "cost_per_day": calculate_7day_avg(baseline, "cost_per_day"),
        "cron_failures": calculate_7day_avg(baseline, "cron_failures"),
        "avg_session_duration_sec": calculate_7day_avg(baseline, "avg_session_duration_sec"),
        "peak_memory_mb": calculate_7day_avg(baseline, "peak_memory_mb")
    }

    save_baseline(baseline)

    if alerts:
        alert_msg = f"Baseline anomaly: {", ".join(alerts)}"
        print(alert_msg)
        alert(alert_msg)
    else:
        print(f"✓ Baseline tracked ({len(baseline['entries'])} days)")

if __name__ == "__main__":
    main()
