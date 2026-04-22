"""Quick end-to-end /advise check via the live backend."""

from __future__ import annotations

import json
import sys

import httpx


def main(base_url: str = "http://localhost:8001") -> int:
    payload = {
        "answers": {
            "gender": "男",
            "age": 45,
            "height_cm": 172,
            "current_weight_kg": 92,
        },
        "coach_level": "new",
    }
    print(f"POST {base_url}/advise ...")
    try:
        with httpx.Client(timeout=120) as c:
            r = c.post(f"{base_url}/advise", json=payload)
    except Exception as exc:
        print(f"[HTTP ERROR] {type(exc).__name__}: {exc}")
        return 2

    print(f"Status: {r.status_code}")
    try:
        body = r.json()
    except Exception:
        print("Body (non-JSON):", r.text[:800])
        return 1

    if r.status_code == 200:
        print("[OK] Got AdviceResponse")
        print("  key_risks       :", body["summary"]["key_risks"])
        print("  overall_level   :", body["summary"]["overall_level"])
        print("  products (SKUs) :", [p["sku"] for p in body["recommended_products"]])
        print("  scripts scenarios:", [s["scenario"] for s in body["sales_scripts"]])
        print("  next_actions    :", [a["action"] for a in body["next_actions"]])
        return 0
    else:
        print("Body:", json.dumps(body, ensure_ascii=False, indent=2)[:800])
        return 1


if __name__ == "__main__":
    sys.exit(main())
