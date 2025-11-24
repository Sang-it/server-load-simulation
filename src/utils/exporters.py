import json
import csv
from pathlib import Path
from typing import Dict, Any, List


class ResultExporter:
    @staticmethod
    def export(results: Dict[str, Any], output_path: Path) -> None:
        raise NotImplementedError


class JSONExporter(ResultExporter):
    @staticmethod
    def export(results: Dict[str, Any], output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)


class CSVExporter(ResultExporter):
    @staticmethod
    def export(results: Dict[str, Any], output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        CSVExporter._export_metrics_summary(results, output_path)

        if "metrics_timeline" in results:
            CSVExporter._export_timeline_metrics(
                results, output_path.parent / f"{output_path.stem}_timeline.csv"
            )

    @staticmethod
    def _export_metrics_summary(results: Dict[str, Any], output_path: Path) -> None:
        metrics_csv_path = output_path.parent / f"{output_path.stem}_metrics.csv"

        metrics = results.get("metrics", {})
        config = results.get("config", {})

        percentiles = metrics.get("response_time_percentiles_ms", {}) or {}
        row = {
            "scenario": results.get("scenario", ""),
            "duration": config.get("duration", ""),
            "num_servers": config.get("num_servers", ""),
            "traffic_pattern": config.get("traffic_pattern", ""),
            "load_balancing_strategy": config.get("load_balancing_strategy", ""),
            "language": config.get("language", ""),
            "hardware_profile": config.get("hardware_profile", ""),
            "total_requests": metrics.get("total_requests", ""),
            "successful_requests": metrics.get("successful_requests", ""),
            "failed_requests": metrics.get("failed_requests", ""),
            "success_rate": f"{metrics.get('success_rate', 0) * 100:.2f}%",
            "avg_response_time_ms": f"{metrics.get('avg_response_time_ms', 0):.2f}",
            "min_response_time_ms": f"{metrics.get('min_response_time_ms', 0):.2f}",
            "max_response_time_ms": f"{metrics.get('max_response_time_ms', 0):.2f}",
            "p50_response_time_ms": f"{percentiles.get('p50', 0):.2f}",
            "p95_response_time_ms": f"{percentiles.get('p95', 0):.2f}",
            "p99_response_time_ms": f"{percentiles.get('p99', 0):.2f}",
            "avg_queue_time_ms": f"{metrics.get('avg_queue_time_ms', 0):.2f}",
            "throughput_rps": f"{metrics.get('successful_throughput_rps', 0):.2f}",
        }

        with open(metrics_csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=row.keys())
            writer.writeheader()
            writer.writerow(row)

    @staticmethod
    def _export_timeline_metrics(results: Dict[str, Any], output_path: Path) -> None:
        timeline = results.get("metrics_timeline", [])

        if not timeline:
            return

        fieldnames = list(timeline[0].keys()) if timeline else []

        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(timeline)


class ComparativeCSVExporter:
    @staticmethod
    def export_comparison(
        results_list: List[Dict[str, Any]],
        output_dir: Path,
        filename: str = "comparison.csv",
    ) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / filename

        rows = []
        for results in results_list:
            metrics = results.get("metrics", {})
            config = results.get("config", {})

            percentiles = metrics.get("response_time_percentiles_ms", {}) or {}
            row = {
                "scenario": results.get("scenario", ""),
                "duration": config.get("duration", ""),
                "num_servers": config.get("num_servers", ""),
                "traffic_pattern": config.get("traffic_pattern", ""),
                "load_balancing_strategy": config.get("load_balancing_strategy", ""),
                "language": config.get("language", ""),
                "total_requests": metrics.get("total_requests", ""),
                "successful_requests": metrics.get("successful_requests", ""),
                "success_rate_pct": f"{metrics.get('success_rate', 0) * 100:.2f}",
                "avg_response_time_ms": f"{metrics.get('avg_response_time_ms', 0):.2f}",
                "p95_response_time_ms": f"{percentiles.get('p95', 0):.2f}",
                "p99_response_time_ms": f"{percentiles.get('p99', 0):.2f}",
                "throughput_rps": f"{metrics.get('successful_throughput_rps', 0):.2f}",
                "avg_queue_time_ms": f"{metrics.get('avg_queue_time_ms', 0):.2f}",
            }
            rows.append(row)

        if not rows:
            return

        fieldnames = list(rows[0].keys())
        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)


def export_results(
    results: Dict[str, Any],
    output_dir: Path,
    basename: str,
    format: str = "json",
) -> str:
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / basename

    if format.lower() == "json":
        json_path = output_path.with_suffix(".json")
        JSONExporter.export(results, json_path)
        return str(json_path)
    elif format.lower() == "csv":
        CSVExporter.export(results, output_path)
        return str(output_path.parent / f"{output_path.stem}_metrics.csv")
    else:
        raise ValueError(f"Unknown export format: {format}")


def export_comparison(
    results_list: List[Dict[str, Any]], output_dir: Path, basename: str = "comparison"
) -> str:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / f"{basename}.csv"
    ComparativeCSVExporter.export_comparison(results_list, output_dir, csv_path.name)
    return str(csv_path)
