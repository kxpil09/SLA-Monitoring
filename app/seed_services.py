"""
seed_services.py — Populate SLA Monitor with real + intentionally broken test services.

Usage (run from project root, Docker must be running):
    python seed_services.py

The script waits up to 30s for the API to be ready, then seeds all services.
Safe to re-run — skips any URL already registered.
"""

import urllib.request
import urllib.error
import json
import sys
import time

API_BASE = "http://localhost:8000/api/v1"

# ── Services to seed ──────────────────────────────────────────────────────────
SERVICES = [
    # ── Real services (expect UP) ─────────────────────────────────────────
    {"name": "Google",          "url": "https://www.google.com"},
    {"name": "Gmail",           "url": "https://mail.google.com"},
    {"name": "GitHub",          "url": "https://github.com"},
    {"name": "Cloudflare",      "url": "https://www.cloudflare.com"},
    {"name": "Reddit",          "url": "https://www.reddit.com"},
    {"name": "Wikipedia",       "url": "https://www.wikipedia.org"},
    {"name": "NPM Registry",    "url": "https://registry.npmjs.org"},
    {"name": "PyPI",            "url": "https://pypi.org"},

    # ── Intentionally broken (expect DOWN) ───────────────────────────────
    {"name": "Always 404",      "url": "https://httpstat.us/404"},
    {"name": "Always 500",      "url": "https://httpstat.us/500"},
    {"name": "Timeout (6s)",    "url": "https://httpstat.us/200?sleep=6000"},
    {"name": "Dead Domain",     "url": "https://this-domain-xyz404dead.com"},
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def api_get(path):
    try:
        with urllib.request.urlopen(f"{API_BASE}{path}", timeout=5) as r:
            return json.loads(r.read()), r.status
    except urllib.error.HTTPError as e:
        return json.loads(e.read() or b"{}"), e.code
    except Exception:
        return None, 0

def api_post(path, payload):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{API_BASE}{path}", data=data,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read()), r.status
    except urllib.error.HTTPError as e:
        return json.loads(e.read() or b"{}"), e.code
    except Exception as ex:
        return {"detail": str(ex)}, 0

# ── Wait for API ──────────────────────────────────────────────────────────────

def wait_for_api(timeout=30):
    print(f"⏳  Waiting for API at {API_BASE} ", end="", flush=True)
    deadline = time.time() + timeout
    while time.time() < deadline:
        result, status = api_get("/services")
        if result is not None:
            print(" ready!\n")
            return True
        print(".", end="", flush=True)
        time.sleep(2)
    print(" timed out.\n")
    return False

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("\n🚀  SLA Monitor — Service Seeder")
    print("─" * 48)

    if not wait_for_api():
        print("❌  API not reachable. Make sure Docker is running:")
        print("    docker compose up -d\n")
        sys.exit(1)

    existing_list, _ = api_get("/services")
    existing_urls = {s["url"].rstrip("/") for s in (existing_list or [])}
    print(f"   {len(existing_urls)} service(s) already registered.\n")

    added = skipped = failed = 0

    for svc in SERVICES:
        url_key = svc["url"].rstrip("/")
        if url_key in existing_urls:
            print(f"  ⏭   Skip     {svc['name']}")
            skipped += 1
            continue

        result, status = api_post("/services", svc)
        if status == 201:
            print(f"  ✅  Added    {svc['name']:28s} {svc['url']}")
            added += 1
        else:
            detail = result.get("detail", result)
            print(f"  ❌  Failed   {svc['name']:28s} → {detail}")
            failed += 1

    print(f"\n{'─' * 48}")
    print(f"  ✅ Added: {added}  ⏭ Skipped: {skipped}  ❌ Failed: {failed}")
    print()
    print("  ⚡ Each new service gets an immediate health check.")
    print("     Results should appear in the UI within ~5 seconds.")
    print(f"  🌐 Open http://localhost:5173\n")

if __name__ == "__main__":
    main()