"""
Incident simulation script.

Triggers a duplicate clock-in against the running backend to produce a
structured error log entry. The full request_id trace appears in stdout.

Usage:
    cd backend
    source venv/bin/activate
    python scripts/simulate_incident.py [--base-url http://localhost:8000]
"""

import argparse
import json
import sys
import urllib.request
import urllib.error

BASE_URL = "http://localhost:8000"
LOGIN_PATH = "/api/v1/auth/login"
CLOCK_IN_PATH = "/api/v1/time-entries/clock-in"


def _post(url: str, payload: dict, token: str | None = None) -> tuple[int, dict]:
    data = json.dumps(payload).encode()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        body = exc.read()
        try:
            detail = json.loads(body)
        except Exception:
            detail = {"raw": body.decode(errors="replace")}
        return exc.code, detail


def main():
    parser = argparse.ArgumentParser(description="Simulate a duplicate clock-in incident")
    parser.add_argument("--base-url", default=BASE_URL)
    parser.add_argument("--email", default="employee@bbsi.demo")
    parser.add_argument("--password", default="Employee1234!")
    args = parser.parse_args()

    base = args.base_url.rstrip("/")
    print(f"\n{'='*60}")
    print("BBSI Workforce — Incident Simulation")
    print(f"Target: {base}")
    print(f"{'='*60}\n")

    # Step 1: Login
    print("[1/4] Authenticating…")
    status, body = _post(f"{base}{LOGIN_PATH}", {"email": args.email, "password": args.password})
    if status != 200:
        print(f"  ✗ Login failed ({status}): {body}")
        sys.exit(1)
    token = body["access_token"]
    print(f"  ✓ Logged in as {args.email}")

    # Step 2: First clock-in (should succeed)
    print("\n[2/4] First clock-in attempt (expected: 201)…")
    status, body = _post(f"{base}{CLOCK_IN_PATH}", {}, token=token)
    if status == 201:
        entry_id = body.get("id")
        print(f"  ✓ Clock-in succeeded — entry_id={entry_id}")
    elif status == 409:
        print("  ⚠  Already clocked in (existing open entry). Proceeding to duplicate attempt.")
    else:
        print(f"  ✗ Unexpected status {status}: {body}")

    # Step 3: Duplicate clock-in (should return 409 Conflict)
    print("\n[3/4] Second (duplicate) clock-in attempt (expected: 409 Conflict)…")
    status, body = _post(f"{base}{CLOCK_IN_PATH}", {}, token=token)
    print(f"  HTTP {status} → {json.dumps(body, indent=2)}")

    if status == 409:
        print("\n  ✓ EXPECTED INCIDENT: duplicate clock-in correctly rejected with 409.")
        print("    Check backend stdout for a structured log line with:")
        print('      "status": 409, "path": "/api/v1/time-entries/clock-in"')
    else:
        print(f"\n  ✗ Unexpected response {status}")

    # Step 4: Report
    print(f"\n[4/4] Simulation complete.")
    print("  → Open backend terminal to see X-Request-ID in response headers")
    print("  → Check structured log lines for the full request trace\n")


if __name__ == "__main__":
    main()
