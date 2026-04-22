"""
Synergy Questionnaire AI POC - E2E Verification Script

Usage:
  uv run python scripts/e2e_verify.py --scenario male_45_overweight --base-url http://localhost:8000
  uv run python scripts/e2e_verify.py --all
  uv run python scripts/e2e_verify.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parents[1]
FIXTURES_DIR = PROJECT_ROOT / "backend" / "tests" / "fixtures" / "scenarios"
SCHEMA_FILE = PROJECT_ROOT / "data" / "schemas" / "questionnaire.json"

SCENARIOS = ["male_45_overweight", "female_35_sleep_issue", "senior_62_chronic"]

# ---------------------------------------------------------------------------
# HTTP helper (uses httpx if available, falls back to urllib)
# ---------------------------------------------------------------------------
try:
    import httpx

    def http_get(url: str, timeout: int = 10) -> tuple[int, Any]:
        with httpx.Client(timeout=timeout) as client:
            r = client.get(url)
            return r.status_code, r.json()

    def http_post(url: str, body: dict, timeout: int = 60) -> tuple[int, Any]:
        with httpx.Client(timeout=timeout) as client:
            r = client.post(url, json=body)
            return r.status_code, r.json()

except ImportError:
    import urllib.request
    import urllib.error

    def http_get(url: str, timeout: int = 10) -> tuple[int, Any]:  # type: ignore[misc]
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read())

    def http_post(url: str, body: dict, timeout: int = 60) -> tuple[int, Any]:  # type: ignore[misc]
        data = json.dumps(body).encode()
        req = urllib.request.Request(
            url, data=data, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read())


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def ok(msg: str) -> None:
    print(f"  [OK]  {msg}")


def fail(msg: str) -> None:
    print(f"  [FAIL] {msg}")


def info(msg: str) -> None:
    print(f"        {msg}")


def load_schema_field_ids() -> set[str]:
    data = json.loads(SCHEMA_FILE.read_text(encoding="utf-8"))
    ids: set[str] = set()
    for section in data["sections"]:
        for field in section["fields"]:
            ids.add(field["field_id"])
    return ids


def load_fixture(scenario: str) -> dict:
    path = FIXTURES_DIR / f"{scenario}.json"
    if not path.exists():
        raise FileNotFoundError(f"Fixture not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Step checks
# ---------------------------------------------------------------------------
def check_health(base_url: str) -> bool:
    print("\n[Step 1] Health check ...")
    try:
        status, body = http_get(f"{base_url}/health")
        if status == 200:
            ok(f"GET /health => {status}  body={body}")
            return True
        fail(f"GET /health => {status}")
        return False
    except Exception as exc:
        fail(f"GET /health raised: {exc}")
        return False


def check_schema_endpoint(base_url: str) -> tuple[bool, set[str]]:
    print("\n[Step 2] Questionnaire schema ...")
    try:
        status, body = http_get(f"{base_url}/questionnaire/schema")
        if status != 200:
            fail(f"GET /questionnaire/schema => {status}")
            return False, set()

        if "sections" not in body:
            fail("Response missing 'sections' key")
            return False, set()

        sections = body["sections"]
        if not isinstance(sections, list) or len(sections) == 0:
            fail("'sections' is empty or not a list")
            return False, set()

        api_field_ids: set[str] = set()
        for section in sections:
            for field in section.get("fields", []):
                api_field_ids.add(field["field_id"])

        ok(f"GET /questionnaire/schema => {status}  sections={len(sections)}  fields={len(api_field_ids)}")
        return True, api_field_ids
    except Exception as exc:
        fail(f"GET /questionnaire/schema raised: {exc}")
        return False, set()


def verify_fixture_fields(scenario: str, api_field_ids: set[str]) -> bool:
    print(f"\n[Step 3a] Validate fixture field_ids for '{scenario}' ...")
    try:
        fixture = load_fixture(scenario)
        used_ids = set(fixture["answers"].keys())
        invalid = used_ids - api_field_ids
        if invalid:
            fail(f"Fixture uses unknown field_ids: {sorted(invalid)}")
            return False
        ok(f"All {len(used_ids)} fixture field_ids exist in schema")
        return True
    except FileNotFoundError as exc:
        fail(str(exc))
        return False


def call_advise(base_url: str, scenario: str) -> bool:
    print(f"\n[Step 3b] POST /advise for '{scenario}' ...")
    try:
        fixture = load_fixture(scenario)
        status, body = http_post(f"{base_url}/advise", {"answers": fixture["answers"]}, timeout=90)

        if status != 200:
            fail(f"POST /advise => {status}  body={str(body)[:200]}")
            return False
        ok(f"POST /advise => {status}")

        # Structural checks
        missing_keys = []
        for key in ("summary", "recommended_products", "sales_scripts", "next_actions"):
            if key not in body:
                missing_keys.append(key)

        if missing_keys:
            fail(f"Response missing keys: {missing_keys}")
            return False

        ok("Response structure valid (summary / recommended_products / sales_scripts / next_actions)")

        # Print summary
        summary = body.get("summary", {})
        narrative = summary.get("narrative", "")
        first_sentence = narrative.split("。")[0] + "。" if "。" in narrative else narrative[:120]
        info(f"narrative[0]: {first_sentence}")

        products = body.get("recommended_products", [])
        skus = [p.get("sku", p.get("product_id", "?")) for p in products]
        info(f"products SKUs: {skus}")

        scripts = body.get("sales_scripts", [])
        script_scenarios = [s.get("scenario", "?") for s in scripts]
        info(f"script scenarios: {script_scenarios}")

        actions = body.get("next_actions", [])
        action_types = [a.get("action", a.get("type", "?")) for a in actions]
        info(f"next_actions: {action_types}")

        return True

    except Exception as exc:
        fail(f"POST /advise raised: {exc}")
        return False


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------
def run_scenario(
    scenario: str,
    base_url: str,
    dry_run: bool,
    api_field_ids: set[str],
) -> bool:
    print(f"\n{'='*60}")
    print(f"  Scenario: {scenario}")
    print(f"{'='*60}")

    if not verify_fixture_fields(scenario, api_field_ids):
        return False

    if dry_run:
        info("dry-run: skipping POST /advise")
        return True

    return call_advise(base_url, scenario)


def main() -> None:
    parser = argparse.ArgumentParser(description="Synergy E2E verification script")
    parser.add_argument("--scenario", choices=SCENARIOS, help="Run a single scenario")
    parser.add_argument("--all", action="store_true", help="Run all scenarios")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip POST /advise, only verify health + schema + fixture integrity",
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Backend base URL (default: http://localhost:8000)",
    )
    args = parser.parse_args()

    if not args.scenario and not args.all and not args.dry_run:
        parser.print_help()
        sys.exit(1)

    scenarios_to_run = SCENARIOS if (args.all or args.dry_run) else [args.scenario]

    print("\nSynergy POC - E2E Verification")
    print(f"Base URL : {args.base_url}")
    print(f"Dry run  : {args.dry_run}")
    print(f"Scenarios: {scenarios_to_run}")

    t_start = time.monotonic()

    # Step 1 – health
    if not check_health(args.base_url):
        print("\n[ABORT] Backend is not reachable.")
        sys.exit(1)

    # Step 2 – schema
    schema_ok, api_field_ids = check_schema_endpoint(args.base_url)
    if not schema_ok:
        print("\n[ABORT] Schema endpoint failed.")
        sys.exit(1)

    # Also cross-check with local schema file for consistency
    if SCHEMA_FILE.exists():
        local_ids = load_schema_field_ids()
        diff = local_ids.symmetric_difference(api_field_ids)
        if diff:
            print(f"\n  [WARN] Local schema vs API schema differ: {sorted(diff)}")
        else:
            ok("Local schema file matches API schema field_ids")

    # Step 3 – per-scenario
    results: dict[str, bool] = {}
    for scenario in scenarios_to_run:
        results[scenario] = run_scenario(scenario, args.base_url, args.dry_run, api_field_ids)

    # Final report
    elapsed = time.monotonic() - t_start
    print(f"\n{'='*60}")
    print("  FINAL REPORT")
    print(f"{'='*60}")
    passed = [s for s, ok_flag in results.items() if ok_flag]
    failed = [s for s, ok_flag in results.items() if not ok_flag]
    for s in passed:
        print(f"  PASS  {s}")
    for s in failed:
        print(f"  FAIL  {s}")
    print(f"\n  Total: {len(results)}  Passed: {len(passed)}  Failed: {len(failed)}")
    print(f"  Elapsed: {elapsed:.1f}s")

    sys.exit(0 if not failed else 1)


if __name__ == "__main__":
    main()
