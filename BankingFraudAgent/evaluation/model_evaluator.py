import json
import time
from pathlib import Path

import requests

from agents.orchestrator import investigate_transaction
from evaluation.evaluation_cases import EVALUATION_CASES


OLLAMA_URL = "http://localhost:11434/api/chat"

MODELS = [
    "qwen3:4b",
    "llama3.2:3b",
    "gemma3:4b",
]

RESULTS_FILE = Path("evaluation/evaluation_results.json")
SUMMARY_FILE = Path("evaluation/evaluation_summary.json")


SYSTEM_PROMPT = """
You are evaluating a banking fraud investigation case.

You are NOT making a final banking decision.
You are producing a structured assessment for comparison with a deterministic
rule-based reference system.

Use only the information provided in the case.

Return ONLY valid JSON with exactly these fields:

{
  "risk_level": "LOW|MEDIUM|HIGH",
  "human_review_required": true,
  "route": "PRIORITY_INVESTIGATION|STANDARD_INVESTIGATION|EVIDENCE_VERIFICATION|STANDARD_REVIEW|MANUAL_REVIEW",
  "priority": "URGENT|NORMAL|HIGH|ROUTINE"
}

Do not add markdown.
Do not add explanations.
Do not add extra fields.
"""


def call_model(model: str, case: dict) -> dict:
    """Send one case to one Ollama model."""

    user_prompt = f"""
Evaluate this synthetic fraud investigation case:

Amount: {case["amount"]}
Channel: {case["channel"]}
Location: {case["location"]}
Device: {case["device"]}
Failed logins: {case["failed_logins"]}
"""

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0,
        },
    }

    start_time = time.perf_counter()

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=180,
    )

    response.raise_for_status()

    elapsed = time.perf_counter() - start_time

    response_data = response.json()

    raw_output = response_data["message"]["content"]

    parsed_output = json.loads(raw_output)

    return {
        "output": parsed_output,
        "raw_output": raw_output,
        "latency_seconds": round(elapsed, 3),
    }


def get_reference(case: dict) -> dict:
    """Run the existing deterministic system as the reference."""

    result = investigate_transaction(
        amount=case["amount"],
        channel=case["channel"],
        location=case["location"],
        device=case["device"],
        failed_logins=case["failed_logins"],
    )

    return {
        "risk_level": result["risk_assessment"]["risk_level"],
        "human_review_required": result["human_review_required"],
        "route": result["routing"]["route"],
        "priority": result["routing"]["priority"],
    }


def compare_outputs(reference: dict, model_output: dict) -> dict:
    """Compare model output against the rule-based reference."""

    return {
        "risk_level_match": (
            model_output.get("risk_level")
            == reference.get("risk_level")
        ),
        "human_review_match": (
            model_output.get("human_review_required")
            == reference.get("human_review_required")
        ),
        "route_match": (
            model_output.get("route")
            == reference.get("route")
        ),
        "priority_match": (
            model_output.get("priority")
            == reference.get("priority")
        ),
    }


def calculate_percentage(matches: int, total: int) -> float:
    """Calculate a percentage safely."""

    if total == 0:
        return 0.0

    return round((matches / total) * 100, 2)


def calculate_summary(results: list) -> dict:
    """Calculate model-level evaluation metrics."""

    summary = {}

    for model in MODELS:

        model_results = [
            result
            for result in results
            if result.get("model") == model
        ]

        successful_results = [
            result
            for result in model_results
            if "comparison" in result
        ]

        completed_cases = len(successful_results)
        total_cases = len(EVALUATION_CASES)

        risk_matches = sum(
            result["comparison"]["risk_level_match"]
            for result in successful_results
        )

        human_review_matches = sum(
            result["comparison"]["human_review_match"]
            for result in successful_results
        )

        route_matches = sum(
            result["comparison"]["route_match"]
            for result in successful_results
        )

        priority_matches = sum(
            result["comparison"]["priority_match"]
            for result in successful_results
        )

        latencies = [
            result["latency_seconds"]
            for result in successful_results
            if isinstance(
                result.get("latency_seconds"),
                (int, float),
            )
        ]

        average_latency = (
            round(sum(latencies) / len(latencies), 2)
            if latencies
            else None
        )

        all_fields_correct = sum(
            all(result["comparison"].values())
            for result in successful_results
        )

        structured_output_count = sum(
            "model_output" in result
            for result in successful_results
        )

        summary[model] = {
            "total_cases": total_cases,
            "completed_cases": completed_cases,
            "failed_cases": total_cases - completed_cases,
            "completion_rate_percent": calculate_percentage(
                completed_cases,
                total_cases,
            ),
            "risk_level_match_percent": calculate_percentage(
                risk_matches,
                completed_cases,
            ),
            "human_review_match_percent": calculate_percentage(
                human_review_matches,
                completed_cases,
            ),
            "route_match_percent": calculate_percentage(
                route_matches,
                completed_cases,
            ),
            "priority_match_percent": calculate_percentage(
                priority_matches,
                completed_cases,
            ),
            "all_fields_match_percent": calculate_percentage(
                all_fields_correct,
                completed_cases,
            ),
            "structured_output_rate_percent": calculate_percentage(
                structured_output_count,
                completed_cases,
            ),
            "average_latency_seconds": average_latency,
        }

    return summary


def print_summary(summary: dict):
    """Print a concise evaluation summary."""

    print("\n")
    print("=" * 100)
    print("THREE-MODEL EVALUATION SUMMARY")
    print("=" * 100)

    print(
        f"{'Model':<18}"
        f"{'Cases':<10}"
        f"{'Risk %':<10}"
        f"{'Review %':<12}"
        f"{'Route %':<10}"
        f"{'Priority %':<12}"
        f"{'All Match %':<13}"
        f"{'Avg Latency':<12}"
    )

    print("-" * 100)

    for model, metrics in summary.items():

        print(
            f"{model:<18}"
            f"{metrics['completed_cases']}/{metrics['total_cases']:<8}"
            f"{metrics['risk_level_match_percent']:<10}"
            f"{metrics['human_review_match_percent']:<12}"
            f"{metrics['route_match_percent']:<10}"
            f"{metrics['priority_match_percent']:<12}"
            f"{metrics['all_fields_match_percent']:<13}"
            f"{str(metrics['average_latency_seconds']) + 's':<12}"
        )

    print("=" * 100)


def main():

    results = []

    print("=" * 70)
    print("GOVERNED AGENTIC AI - THREE MODEL EVALUATION")
    print("=" * 70)

    for case in EVALUATION_CASES:

        print(f"\nCase: {case['case_id']}")

        reference = get_reference(case)

        print("Reference:", reference)

        for model in MODELS:

            print(f"  Running {model}...")

            try:

                model_result = call_model(
                    model,
                    case,
                )

                comparison = compare_outputs(
                    reference,
                    model_result["output"],
                )

                result = {
                    "case_id": case["case_id"],
                    "model": model,
                    "input": case,
                    "reference": reference,
                    "model_output": model_result["output"],
                    "raw_output": model_result["raw_output"],
                    "latency_seconds": model_result[
                        "latency_seconds"
                    ],
                    "comparison": comparison,
                }

                results.append(result)

                print(
                    f"  Result: {model_result['output']} "
                    f"| Latency: "
                    f"{model_result['latency_seconds']}s"
                )

            except Exception as error:

                print(f"  ERROR: {error}")

                results.append(
                    {
                        "case_id": case["case_id"],
                        "model": model,
                        "input": case,
                        "reference": reference,
                        "error": str(error),
                    }
                )

    with open(
        RESULTS_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            results,
            file,
            indent=2,
            ensure_ascii=False,
        )

    summary = calculate_summary(results)

    with open(
        SUMMARY_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            summary,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print_summary(summary)

    print("\n")
    print("=" * 70)
    print("Evaluation completed.")
    print(f"Detailed results: {RESULTS_FILE}")
    print(f"Summary metrics:  {SUMMARY_FILE}")
    print("=" * 70)


if __name__ == "__main__":
    main()