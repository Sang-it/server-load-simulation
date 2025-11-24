from typing import Dict, List, Any


class ScenarioComparison:
    @staticmethod
    def compare_scenarios(results_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not results_list:
            return {}

        scenario_metrics = []
        for results in results_list:
            metrics = results.get("metrics", {})
            config = results.get("config", {})
            scenario_name = results.get("scenario", "unknown")

            scenario_data = {
                "name": scenario_name,
                "num_servers": results.get("num_servers", config.get("num_servers", 1)),
                "traffic_pattern": results.get(
                    "traffic_pattern", config.get("traffic_pattern", "")
                ),
                "load_balancing_strategy": results.get(
                    "balancing_strategy", config.get("load_balancing_strategy", "")
                ),
                "language": results.get("language", config.get("language", "")),
                "avg_response_time_ms": metrics.get("avg_response_time_ms", 0),
                "success_rate": metrics.get("success_rate", 0),
                "throughput_rps": metrics.get("successful_throughput_rps", 0),
                "total_requests": metrics.get("total_requests", 0),
                "successful_requests": metrics.get("successful_requests", 0),
            }
            scenario_metrics.append(scenario_data)

        best_response_time = min(
            scenario_metrics, key=lambda x: x["avg_response_time_ms"]
        )
        best_throughput = max(scenario_metrics, key=lambda x: x["throughput_rps"])
        best_success_rate = max(scenario_metrics, key=lambda x: x["success_rate"])

        base_response_time = best_response_time["avg_response_time_ms"]
        base_throughput = best_throughput["throughput_rps"]

        for scenario in scenario_metrics:
            scenario["response_time_vs_best_pct"] = (
                (scenario["avg_response_time_ms"] - base_response_time)
                / base_response_time
                * 100
                if base_response_time > 0
                else 0
            )
            scenario["throughput_vs_best_pct"] = (
                (scenario["throughput_rps"] - base_throughput) / base_throughput * 100
                if base_throughput > 0
                else 0
            )

        return {
            "scenarios": scenario_metrics,
            "best_response_time_scenario": best_response_time["name"],
            "best_throughput_scenario": best_throughput["name"],
            "best_success_rate_scenario": best_success_rate["name"],
            "num_scenarios": len(scenario_metrics),
        }

    @staticmethod
    def print_comparison_summary(comparison: Dict[str, Any]) -> None:
        scenarios = comparison.get("scenarios", [])
        if not scenarios:
            print("No scenarios to compare")
            return

        print("\n" + "=" * 100)
        print("SCENARIO COMPARISON SUMMARY")
        print("=" * 100 + "\n")

        print(
            f"{'Scenario':<25} {'Avg RT (ms)':<12} {'Throughput':<12} {'Success %':<12}"
        )
        print("-" * 100)

        for scenario in scenarios:
            name = scenario["name"][:24]
            avg_rt = f"{scenario['avg_response_time_ms']:.2f}"
            throughput = f"{scenario['throughput_rps']:.2f}"
            success = f"{scenario['success_rate'] * 100:.1f}%"

            print(f"{name:<25} {avg_rt:<12} {throughput:<12} {success:<12}")

        print("-" * 100)

        print("\nWINNERS:")
        print(f"  Best Response Time: {comparison['best_response_time_scenario']}")
        print(f"  Best Throughput: {comparison['best_throughput_scenario']}")
        print(f"  Best Success Rate: {comparison['best_success_rate_scenario']}")
        print("\n" + "=" * 100 + "\n")

    @staticmethod
    def analyze_strategy_performance(
        results_list: List[Dict[str, Any]], by_strategy: bool = True
    ) -> Dict[str, Any]:
        groups = {}

        for results in results_list:
            metrics = results.get("metrics", {})
            config = results.get("config", {})

            if by_strategy:
                group_key = results.get(
                    "balancing_strategy",
                    config.get("load_balancing_strategy", "unknown"),
                )
            else:
                group_key = results.get("language", config.get("language", "unknown"))

            if group_key not in groups:
                groups[group_key] = {
                    "scenarios": [],
                    "avg_response_times": [],
                    "success_rates": [],
                    "throughputs": [],
                }

            groups[group_key]["scenarios"].append(results.get("scenario", ""))
            groups[group_key]["avg_response_times"].append(
                metrics.get("avg_response_time_ms", 0)
            )
            groups[group_key]["success_rates"].append(metrics.get("success_rate", 0))
            groups[group_key]["throughputs"].append(
                metrics.get("successful_throughput_rps", 0)
            )

        for group_key in groups:
            group = groups[group_key]
            if group["avg_response_times"]:
                group["mean_response_time"] = sum(group["avg_response_times"]) / len(
                    group["avg_response_times"]
                )
                group["mean_success_rate"] = sum(group["success_rates"]) / len(
                    group["success_rates"]
                )
                group["mean_throughput"] = sum(group["throughputs"]) / len(
                    group["throughputs"]
                )

        return groups

    @staticmethod
    def print_strategy_analysis(groups: Dict[str, Any], by_strategy: bool = True):
        label = "LOAD BALANCING STRATEGY" if by_strategy else "PROGRAMMING LANGUAGE"

        print("\n" + "=" * 80)
        print(f"PERFORMANCE BY {label}")
        print("=" * 80 + "\n")

        print(
            f"{'Strategy':<30} {'Avg RT (ms)':<15} {'Throughput':<15} {'Avg Success':<15}"
        )
        print("-" * 80)

        for group_key in sorted(groups.keys()):
            group = groups[group_key]
            if "mean_response_time" in group:
                name = group_key[:29]
                avg_rt = f"{group['mean_response_time']:.2f}"
                throughput = f"{group['mean_throughput']:.2f}"
                success = f"{group['mean_success_rate'] * 100:.1f}%"

                print(f"{name:<30} {avg_rt:<15} {throughput:<15} {success:<15}")

        print("=" * 80 + "\n")
