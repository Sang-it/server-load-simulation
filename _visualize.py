import json
import sys
from pathlib import Path

from typing import List, Optional
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import numpy as np


class ResultsVisualizer:
    def __init__(
        self,
        results_dir: str = "results",
        output_dir: Optional[str] = None,
        short_output: bool = False,
    ):
        self.results_dir = Path(results_dir)
        self.output_dir = Path(output_dir) if output_dir else self.results_dir
        self.results = {}
        self.short_output = short_output
        self.load_results()
        self.create_output_dir()

    def load_results(self) -> None:
        if not self.results_dir.exists():
            print(f"Error: Results directory not found: {self.results_dir}")
            sys.exit(1)

        json_files = list(self.results_dir.glob("*.json"))
        if not json_files:
            print(f"Error: No JSON files found in {self.results_dir}")
            sys.exit(1)

        for json_file in json_files:
            try:
                with open(json_file) as f:
                    data = json.load(f)
                    scenario_name = data.get("scenario", json_file.stem)
                    self.results[scenario_name] = data
            except json.JSONDecodeError as e:
                print(f"Warning: Failed to parse {json_file}: {e}")

    def create_output_dir(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)

        if not self.short_output:
            print(f"Loaded {len(self.results)} simulation results")

    def create_all_visualizations(self) -> int:
        """Create all visualizations and return count of visualizations created."""
        count = 0
        count += self.visualize_response_times()
        count += self.visualize_throughput()
        count += self.visualize_success_rates()
        count += self.visualize_queue_times()
        count += self.visualize_per_server_distribution()
        count += self.visualize_comparative_dashboard()

        if not self.short_output:
            print("\nAll visualizations created successfully!")
            print("   Open the PNG files to view the results")

        return count

    def visualize_response_times(self) -> int:
        _, ax = plt.subplots(figsize=(12, 6))

        scenarios = list(self.results.keys())
        response_times = [
            self.results[s]["metrics"]["avg_response_time_ms"] for s in scenarios
        ]

        colors = self._get_scenario_colors(scenarios)
        bars = ax.bar(
            scenarios, response_times, color=colors, edgecolor="black", linewidth=1.5
        )

        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                height,
                f"{height:.1f}ms",
                ha="center",
                va="bottom",
                fontsize=9,
                fontweight="bold",
            )

        ax.set_xlabel("Scenario", fontsize=12, fontweight="bold")
        ax.set_ylabel("Average Response Time (ms)", fontsize=12, fontweight="bold")
        ax.set_title(
            "Response Time Comparison Across Scenarios", fontsize=14, fontweight="bold"
        )
        ax.grid(axis="y", alpha=0.3, linestyle="--")

        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.savefig(
            self.output_dir / "01_response_times.png", dpi=300, bbox_inches="tight"
        )
        if not self.short_output:
            print("Created: 01_response_times.png")
        plt.close()
        return 1

    def visualize_throughput(self) -> int:
        fig, ax = plt.subplots(figsize=(12, 6))

        scenarios = list(self.results.keys())
        throughput = [
            self.results[s]["metrics"]["successful_throughput_rps"] for s in scenarios
        ]

        colors = self._get_scenario_colors(scenarios)
        bars = ax.bar(
            scenarios, throughput, color=colors, edgecolor="black", linewidth=1.5
        )

        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                height,
                f"{height:.2f}",
                ha="center",
                va="bottom",
                fontsize=9,
                fontweight="bold",
            )

        ax.set_xlabel("Scenario", fontsize=12, fontweight="bold")
        ax.set_ylabel(
            "Throughput (Requests Per Second)", fontsize=12, fontweight="bold"
        )
        ax.set_title(
            "Throughput Comparison Across Scenarios", fontsize=14, fontweight="bold"
        )
        ax.grid(axis="y", alpha=0.3, linestyle="--")

        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.savefig(self.output_dir / "02_throughput.png", dpi=300, bbox_inches="tight")
        if not self.short_output:
            print("Created: 02_throughput.png")
        plt.close()
        return 1

    def visualize_success_rates(self) -> int:
        fig, ax = plt.subplots(figsize=(12, 6))

        scenarios = list(self.results.keys())
        success_rates = []
        timeout_rates = []

        for scenario in scenarios:
            metrics = self.results[scenario]["metrics"]
            total = metrics["total_requests"]
            successful = metrics["successful_requests"]
            timed_out = metrics["timed_out_requests"]

            success_rates.append((successful / total) * 100 if total > 0 else 0)
            timeout_rates.append((timed_out / total) * 100 if total > 0 else 0)

        x = np.arange(len(scenarios))
        width = 0.35

        bars1 = ax.bar(
            x - width / 2,
            success_rates,
            width,
            label="Success",
            color="#2ecc71",
            edgecolor="black",
            linewidth=1.5,
        )
        bars2 = ax.bar(
            x + width / 2,
            timeout_rates,
            width,
            label="Timeout",
            color="#e74c3c",
            edgecolor="black",
            linewidth=1.5,
        )

        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        height,
                        f"{height:.1f}%",
                        ha="center",
                        va="bottom",
                        fontsize=8,
                    )

        ax.set_xlabel("Scenario", fontsize=12, fontweight="bold")
        ax.set_ylabel("Percentage (%)", fontsize=12, fontweight="bold")
        ax.set_title("Success Rate vs Timeout Rate", fontsize=14, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels(scenarios, rotation=45, ha="right")
        ax.legend(loc="upper right", fontsize=11)
        ax.set_ylim(0, 110)
        ax.grid(axis="y", alpha=0.3, linestyle="--")

        plt.tight_layout()
        plt.savefig(
            self.output_dir / "03_success_rates.png", dpi=300, bbox_inches="tight"
        )
        if not self.short_output:
            print("Created: 03_success_rates.png")
        plt.close()
        return 1

    def visualize_queue_times(self) -> int:
        fig, ax = plt.subplots(figsize=(12, 6))

        scenarios = list(self.results.keys())
        avg_queue = [self.results[s]["metrics"]["avg_queue_time_ms"] for s in scenarios]
        max_queue = [self.results[s]["metrics"]["max_queue_time_ms"] for s in scenarios]

        x = np.arange(len(scenarios))
        width = 0.35

        bars1 = ax.bar(
            x - width / 2,
            avg_queue,
            width,
            label="Avg Queue Time",
            color="#3498db",
            edgecolor="black",
            linewidth=1.5,
        )
        bars2 = ax.bar(
            x + width / 2,
            max_queue,
            width,
            label="Max Queue Time",
            color="#9b59b6",
            edgecolor="black",
            linewidth=1.5,
        )

        ax.set_xlabel("Scenario", fontsize=12, fontweight="bold")
        ax.set_ylabel("Queue Time (ms)", fontsize=12, fontweight="bold")
        ax.set_title("Average vs Maximum Queue Times", fontsize=14, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels(scenarios, rotation=45, ha="right")
        ax.legend(loc="upper left", fontsize=11)
        ax.grid(axis="y", alpha=0.3, linestyle="--")

        plt.tight_layout()
        plt.savefig(
            self.output_dir / "04_queue_times.png", dpi=300, bbox_inches="tight"
        )
        if not self.short_output:
            print("Created: 04_queue_times.png")
        plt.close()
        return 1

    def visualize_per_server_distribution(self) -> int:
        multi_server_scenarios = {
            name: data
            for name, data in self.results.items()
            if data.get("num_servers", 1) > 1
        }

        if not multi_server_scenarios:
            if not self.short_output:
                print("  (Skipped: No multi-server scenarios)")
            return 0

        num_scenarios = len(multi_server_scenarios)
        fig, axes = plt.subplots(1, num_scenarios, figsize=(6 * num_scenarios, 5))

        if num_scenarios == 1:
            axes = [axes]

        for idx, (scenario_name, data) in enumerate(multi_server_scenarios.items()):
            per_server = data["per_server_stats"]
            server_ids = sorted(per_server.keys(), key=int)
            requests = [per_server[sid]["total_requests"] for sid in server_ids]
            successful = [per_server[sid]["successful_requests"] for sid in server_ids]

            ax = axes[idx]
            x = np.arange(len(server_ids))
            width = 0.35

            bars1 = ax.bar(
                x - width / 2,
                requests,
                width,
                label="Total",
                color="#3498db",
                edgecolor="black",
                linewidth=1.5,
            )
            bars2 = ax.bar(
                x + width / 2,
                successful,
                width,
                label="Successful",
                color="#2ecc71",
                edgecolor="black",
                linewidth=1.5,
            )

            for bars in [bars1, bars2]:
                for bar in bars:
                    height = bar.get_height()
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        height,
                        f"{int(height)}",
                        ha="center",
                        va="bottom",
                        fontsize=9,
                    )

            ax.set_xlabel("Server ID", fontsize=11, fontweight="bold")
            ax.set_ylabel("Number of Requests", fontsize=11, fontweight="bold")
            ax.set_title(
                f"{scenario_name}\n({data['num_servers']} servers)",
                fontsize=12,
                fontweight="bold",
            )
            ax.set_xticks(x)
            ax.set_xticklabels(server_ids)
            ax.legend(fontsize=10)
            ax.grid(axis="y", alpha=0.3, linestyle="--")

        plt.tight_layout()
        plt.savefig(
            self.output_dir / "05_per_server_distribution.png",
            dpi=300,
            bbox_inches="tight",
        )
        if not self.short_output:
            print("Created: 05_per_server_distribution.png")
        plt.close()
        return 1

    def visualize_comparative_dashboard(self) -> int:
        fig = plt.figure(figsize=(16, 12))
        gs = GridSpec(3, 3, figure=fig, hspace=0.3, wspace=0.3)

        scenarios = list(self.results.keys())
        colors = self._get_scenario_colors(scenarios)

        ax1 = fig.add_subplot(gs[0, 0])
        response_times = [
            self.results[s]["metrics"]["avg_response_time_ms"] for s in scenarios
        ]
        ax1.barh(scenarios, response_times, color=colors, edgecolor="black")
        ax1.set_xlabel("Time (ms)", fontsize=10, fontweight="bold")
        ax1.set_title("Response Time", fontsize=11, fontweight="bold")
        ax1.grid(axis="x", alpha=0.3)

        ax2 = fig.add_subplot(gs[0, 1])
        throughput = [
            self.results[s]["metrics"]["successful_throughput_rps"] for s in scenarios
        ]
        ax2.barh(scenarios, throughput, color=colors, edgecolor="black")
        ax2.set_xlabel("RPS", fontsize=10, fontweight="bold")
        ax2.set_title("Throughput", fontsize=11, fontweight="bold")
        ax2.grid(axis="x", alpha=0.3)

        ax3 = fig.add_subplot(gs[0, 2])
        success_rates = [
            (
                self.results[s]["metrics"]["successful_requests"]
                / self.results[s]["metrics"]["total_requests"]
            )
            * 100
            for s in scenarios
        ]
        ax3.barh(scenarios, success_rates, color=colors, edgecolor="black")
        ax3.set_xlabel("Percentage (%)", fontsize=10, fontweight="bold")
        ax3.set_title("Success Rate", fontsize=11, fontweight="bold")
        ax3.set_xlim(0, 105)
        ax3.grid(axis="x", alpha=0.3)

        ax4 = fig.add_subplot(gs[1, 0])
        queue_times = [
            self.results[s]["metrics"]["avg_queue_time_ms"] for s in scenarios
        ]
        ax4.barh(scenarios, queue_times, color=colors, edgecolor="black")
        ax4.set_xlabel("Time (ms)", fontsize=10, fontweight="bold")
        ax4.set_title("Avg Queue Time", fontsize=11, fontweight="bold")
        ax4.grid(axis="x", alpha=0.3)

        ax5 = fig.add_subplot(gs[1, 1])
        total_requests = [
            self.results[s]["metrics"]["total_requests"] for s in scenarios
        ]
        ax5.barh(scenarios, total_requests, color=colors, edgecolor="black")
        ax5.set_xlabel("Count", fontsize=10, fontweight="bold")
        ax5.set_title("Total Requests", fontsize=11, fontweight="bold")
        ax5.grid(axis="x", alpha=0.3)

        ax6 = fig.add_subplot(gs[1, 2])
        num_servers = [self.results[s].get("num_servers", 1) for s in scenarios]
        ax6.barh(scenarios, num_servers, color=colors, edgecolor="black")
        ax6.set_xlabel("Count", fontsize=10, fontweight="bold")
        ax6.set_title("Number of Servers", fontsize=11, fontweight="bold")
        ax6.grid(axis="x", alpha=0.3)

        ax7 = fig.add_subplot(gs[2, :])
        successful = [
            self.results[s]["metrics"]["successful_requests"] for s in scenarios
        ]
        timed_out = [
            self.results[s]["metrics"]["timed_out_requests"] for s in scenarios
        ]
        errors = [self.results[s]["metrics"]["error_requests"] for s in scenarios]

        x = np.arange(len(scenarios))
        width = 0.6

        p1 = ax7.bar(
            x, successful, width, label="Successful", color="#2ecc71", edgecolor="black"
        )
        p2 = ax7.bar(
            x,
            timed_out,
            width,
            bottom=successful,
            label="Timeout",
            color="#e74c3c",
            edgecolor="black",
        )
        p3 = ax7.bar(
            x,
            errors,
            width,
            bottom=np.array(successful) + np.array(timed_out),
            label="Errors",
            color="#34495e",
            edgecolor="black",
        )

        ax7.set_ylabel("Count", fontsize=10, fontweight="bold")
        ax7.set_title("Request Status Breakdown", fontsize=11, fontweight="bold")
        ax7.set_xticks(x)
        ax7.set_xticklabels(scenarios, rotation=45, ha="right")
        ax7.legend(loc="upper left", ncol=3, fontsize=10)
        ax7.grid(axis="y", alpha=0.3)

        fig.suptitle(
            "Simulation Results - Comprehensive Dashboard",
            fontsize=16,
            fontweight="bold",
            y=0.995,
        )
        plt.savefig(self.output_dir / "06_dashboard.png", dpi=300, bbox_inches="tight")
        if not self.short_output:
            print("Created: 06_dashboard.png")
        plt.close()
        return 1

    @staticmethod
    def _get_scenario_colors(scenarios: List[str]) -> List[str]:
        color_map = {
            "multi_server_test": "#3498db",
            "high_performance_hw": "#2ecc71",
            "enterprise_hw": "#27ae60",
            "nodejs_test": "#f39c12",
            "go_test": "#e74c3c",
            "low_load": "#9b59b6",
            "heavy_load": "#c0392b",
            "least_connections_test": "#16a085",
            "constant_traffic": "#8e44ad",
            "different_seed": "#2980b9",
        }

        colors = []
        for i, scenario in enumerate(scenarios):
            if scenario in color_map:
                colors.append(color_map[scenario])
            else:
                colors.append(plt.cm.tab20(i % 20))

        return colors


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Visualize server load simulation results"
    )
    parser.add_argument(
        "--results-dir",
        type=str,
        default="results",
        help="Path to results directory (default: results)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="visualizations",
        help="Output directory for visualizations (default: same as results-dir)",
    )
    parser.add_argument(
        "--short-output",
        action="store_true",
        help="Minimal output: only final summary",
    )

    args = parser.parse_args()
    short_output = getattr(args, "short_output", False)

    if not short_output:
        print("\n" + "=" * 80)
        print("SERVER LOAD SIMULATION - RESULTS VISUALIZER")
        print("=" * 80 + "\n")

    visualizer = ResultsVisualizer(
        args.results_dir, args.output_dir, short_output=short_output
    )

    if not short_output:
        print(
            f"\nGenerating visualizations from {len(visualizer.results)} scenarios...\n"
        )

    num_visualizations = visualizer.create_all_visualizations()

    if short_output:
        print(
            f"Generated {num_visualizations} visualizations from {len(visualizer.results)} scenarios in {visualizer.output_dir}/"
        )
    else:
        print("\n" + "=" * 80)
        print("VISUALIZATION COMPLETE")
        print("=" * 80)
        print(f"\nGenerated PNG files in: {visualizer.output_dir}/")
        print("\nVisualization files created:")
        print("  01_response_times.png       - Response time comparison")
        print("  02_throughput.png           - Throughput comparison")
        print("  03_success_rates.png        - Success vs timeout rates")
        print("  04_queue_times.png          - Queue time analysis")
        print("  05_per_server_distribution.png - Server load distribution")
        print("  06_dashboard.png            - Comprehensive metrics dashboard")
        print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    main()
