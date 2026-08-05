"""
Preview-run the enrich -> score -> draft pipeline over a CSV of prospects.

Read-only: does not call /log, nothing gets persisted. Prints a summary per company.

Usage:
    python scripts/run_batch.py [csv_path] [--base-url http://localhost:8000]
"""

import argparse
import csv
import sys

import requests

DEFAULT_CSV_PATH = "data/prospect-batch-1.csv"
DEFAULT_BASE_URL = "http://localhost:8000"
REQUEST_TIMEOUT = 60


def build_lead_payload(row: dict, enrich_result: dict) -> dict:
    return {
        "name": row["founder_name"],
        "company": row["company_name"],
        "title": row["founder_title"] or None,
        "company_size": enrich_result.get("company_size"),
        "industry": enrich_result.get("industry"),
        "linkedin_active_recently": None,
        "estimated_monthly_leads": None,
        "has_dedicated_sales_role": None,
        "recent_signal": row["notes"] or None,
        "location": row["location"] or None,
    }


def run_row(base_url: str, row: dict) -> None:
    company_name = row["company_name"]

    enrich_resp = requests.post(
        f"{base_url}/enrich",
        json={"company_name": company_name, "website_url": row["website_url"]},
        timeout=REQUEST_TIMEOUT,
    )
    enrich_resp.raise_for_status()
    enrich_result = enrich_resp.json()

    lead_payload = build_lead_payload(row, enrich_result)

    score_resp = requests.post(f"{base_url}/score", json=lead_payload, timeout=REQUEST_TIMEOUT)
    score_resp.raise_for_status()
    score_result = score_resp.json()

    draft_payload = {
        **lead_payload,
        "score": score_result["score"],
        "confidence": score_result["confidence"],
        "reason": score_result["reason"],
    }
    draft_resp = requests.post(f"{base_url}/draft", json=draft_payload, timeout=REQUEST_TIMEOUT)
    draft_resp.raise_for_status()
    draft_result = draft_resp.json()

    print(f"Company:    {company_name}")
    print(f"Score:      {score_result['score']}/10")
    print(f"Confidence: {score_result['confidence']}")
    print(f"Reason:     {score_result['reason']}")
    print(f"Drafted:    {draft_result['drafted']}")
    if draft_result["drafted"]:
        print(f"Message:    {draft_result['message']}")
    else:
        print(f"Skip reason: {draft_result['message']}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path", nargs="?", default=DEFAULT_CSV_PATH)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    args = parser.parse_args()

    with open(args.csv_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    total = len(rows)
    for i, row in enumerate(rows, start=1):
        print(f"[{i}/{total}] {row['company_name']}...")
        try:
            run_row(args.base_url, row)
        except requests.HTTPError as exc:
            detail = exc.response.text if exc.response is not None else str(exc)
            print(f"ERROR: {row['company_name']} failed: {detail}")
        except requests.RequestException as exc:
            print(f"ERROR: {row['company_name']} failed: {exc}")
        print("-" * 60)


if __name__ == "__main__":
    main()
