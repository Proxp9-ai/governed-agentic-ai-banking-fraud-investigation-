import json
from pathlib import Path

RESULTS_FILE = Path("evaluation/evaluation_results.json")
SUMMARY_FILE = Path("evaluation/evaluation_summary.json")

MODELS = [
    "qwen3:4b",
    "llama3.2:3b",
    "gemma3:4b",
]


def percentage(value, total):
    if total == 0:
        return 0.0
    return round((value / total) * 100, 2)


def main():

    with open(
        RESULTS_FILE,
        "r",
        encoding="utf-8",
    ) as file:
        results = json.load(file)

    total_cases = len(
        {
            result["case_id"]
            for result in results
        }
    )

    summary = {}

    for model in MODELS:

        model_results = [
            result
            for result in results
            if result.get("model") == model
        ]

        successful = [
            result
            for result in model_results
            if "comparison" in result
        ]

        completed = len(successful)

        risk_matches = sum(
            result["comparison"]["risk_level_match"]
            for result in successful
        )

        review_matches = sum(
            result["comparison"]["human_review_match"]
            for result in successful
        )

        route_matches = sum(
            result["comparison"]["route_match"]
            for result in successful
        )

        priority_matches = sum(
            result["comparison"]["priority_match"]
            for result in successful
        )

        all_matches = sum(
            all(result["comparison"].values())
            for result in successful
        )

        structured_outputs = sum(
            "model_output" in result
            for result in successful
        )

        latencies = [
            result["latency_seconds"]
            for result in successful
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

        summary[model] = {
            "total_cases": total_cases,
            "completed_cases": completed,
            "failed_cases": total_cases - completed,
            "completion_rate_percent": percentage(
                completed,
                total_cases,
            ),
            "risk_level_match_percent": percentage(
                risk_matches,
                completed,
            ),
            "human_review_match_percent": percentage(
                review_matches,
                completed,
            ),
            "route_match_percent": percentage(
                route_matches,
                completed,
            ),
            "priority_match_percent": percentage(
                priority_matches,
                completed,
            ),
            "all_fields_match_percent": percentage(
                all_matches,
                completed,
            ),
            "structured_output_rate_percent": percentage(
                structured_outputs,
                completed,
            ),
            "average_latency_seconds": average_latency,
        }

    with open(
        SUMMARY_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            summary,
            file,
            indent=2,
        )

    print()
    print("=" * 100)
    print("FINAL THREE-MODEL EVALUATION SUMMARY")
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
    print()
    print(f"Summary saved to: {SUMMARY_FILE}")


if __name__ == "__main__":
    main()