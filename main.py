import argparse
import json
import sys
from pathlib import Path

from src.simulation.engine import LoadSimulator
from src.utils.config_loader import ConfigLoader, load_scenarios, list_scenarios
from src.utils.exporters import export_results, export_comparison
from src.utils.comparison import ScenarioComparison


def run_scenarios_from_config(
    config_file: str,
    scenario_name=None,
    time_scale=None,
    export_format="json",
    comparison=False,
    short_output=False,
):
    config_path = Path(config_file)

    if not config_path.exists():
        print("\nError: Configuration file not found", file=sys.stderr)
        print(f"  Expected path: {config_path.absolute()}", file=sys.stderr)
        print(f"  Current directory: {Path.cwd()}", file=sys.stderr)
        sys.exit(1)

    if scenario_name:
        if not short_output:
            print(f"\nLoading scenario '{scenario_name}' from {config_file}...")
        scenario = ConfigLoader.load_scenario_by_name(config_path, scenario_name)
        if not scenario:
            print(
                f"\nError: Scenario '{scenario_name}' not found in {config_file}",
                file=sys.stderr,
            )
            print("\nAvailable scenarios:")
            list_scenarios(config_file)
            sys.exit(1)
        scenarios_to_run = [scenario]
    else:
        if not short_output:
            print(f"\nLoading all scenarios from {config_file}...")
        scenarios_to_run = load_scenarios(config_file)

        if not scenarios_to_run:
            print(
                f"\nError: No scenarios found in {config_file}",
                file=sys.stderr,
            )
            print(
                "Ensure 'scenarios:' list is defined in the configuration file.",
                file=sys.stderr,
            )
            sys.exit(1)

    results_list = []
    output_dir = Path("results")
    output_dir.mkdir(exist_ok=True)

    for scenario in scenarios_to_run:
        if time_scale is not None:
            scenario.time_scale = time_scale

        if not short_output:
            print(f"\n{'=' * 80}")
            print(f"Running scenario: {scenario.name}")
            print(f"  Duration: {scenario.duration}s (simulation time)")
            print(
                f"  Time Scale: {scenario.time_scale}x ({scenario.duration * scenario.time_scale:.1f}s wall-clock)"
            )
            print(f"{'=' * 80}\n")

        try:
            simulator = LoadSimulator(scenario, show_progress=not short_output)
            simulator.run()
            results = simulator.get_results()
            results_list.append(results)

            metrics = results["metrics"]

            if short_output:
                # Single-line condensed output
                results_file = output_dir / f"{scenario.name}.json"
                print(
                    f"{scenario.name}: {metrics['total_requests']} reqs, "
                    f"{metrics['avg_response_time_ms']:.1f}ms avg, "
                    f"{metrics['successful_throughput_rps']:.1f} RPS, "
                    f"{metrics['success_rate'] * 100:.0f}% success"
                )
            else:
                print(f"Results for {scenario.name}:")
                print(f"  - Servers: {scenario.num_servers}")
                print(f"  - Duration: {scenario.duration}s")
                print(f"  - Total Requests: {metrics['total_requests']}")
                print(
                    f"  - Avg Response Time: {metrics['avg_response_time_ms']:.2f} ms"
                )
                print(f"  - Throughput: {metrics['successful_throughput_rps']:.2f} RPS")
                print(f"  - Success Rate: {metrics['success_rate'] * 100:.1f}%")

            if export_format in ["json", "both"]:
                results_file = output_dir / f"{scenario.name}.json"
                with open(results_file, "w") as f:
                    json.dump(results, f, indent=2)
                if not short_output:
                    print(f"  - Results saved to: {results_file}")

            if export_format in ["csv", "both"]:
                csv_file = export_results(
                    results, output_dir, format="csv", basename=scenario.name
                )
                if not short_output:
                    print(f"  - CSV export saved to: {csv_file}")

        except ValueError as e:
            print(
                f"\nError: Invalid scenario configuration for '{scenario.name}':",
                file=sys.stderr,
            )
            print(f"  {e}", file=sys.stderr)
            continue
        except Exception as e:
            print(f"\nError running scenario '{scenario.name}':", file=sys.stderr)
            print(f"  Type: {type(e).__name__}", file=sys.stderr)
            print(f"  Details: {e}", file=sys.stderr)
            continue

    if results_list:
        if short_output:
            print(
                f"Completed {len(results_list)} scenario(s). Results in {output_dir}/"
            )
        else:
            print(f"\n{'=' * 80}")
            print("SIMULATION COMPLETE")
            print(f"{'=' * 80}\n")
            print(f"Results saved to {output_dir}/")
            print(f"Total scenarios executed: {len(results_list)}")

        if len(results_list) > 1 and not short_output:
            if comparison:
                comparison_file = export_comparison(results_list, output_dir)
                print(f"Comparison report saved to: {comparison_file}")

            comparison_analysis = ScenarioComparison.compare_scenarios(results_list)
            ScenarioComparison.print_comparison_summary(comparison_analysis)

            strategy_groups = ScenarioComparison.analyze_strategy_performance(
                results_list, by_strategy=True
            )
            if strategy_groups:
                ScenarioComparison.print_strategy_analysis(
                    strategy_groups, by_strategy=True
                )
    else:
        print("Error: No scenarios completed successfully", file=sys.stderr)
        sys.exit(1)

    return results_list


def validate_config(config_file: str, verbose: bool = False):
    config_path = Path(config_file)

    print(f"\nValidating configuration file: {config_file}")
    print("-" * 80)

    is_valid, errors, warnings = ConfigLoader.validate_config_file(config_path)

    if errors:
        print(f"\nERRORS ({len(errors)}):")
        for error in errors:
            print(f"  • {error}")

    if warnings:
        print(f"\nWARNINGS ({len(warnings)}):")
        for warning in warnings:
            print(f"  • {warning}")

    if is_valid:
        print("\nConfiguration is valid!")
        if verbose:
            scenarios = ConfigLoader.list_available_scenarios(config_path)
            print(f"\nFound {len(scenarios)} scenario(s):")
            for scenario in scenarios:
                print(f"  • {scenario['name']}: {scenario['description']}")
    else:
        print("\nConfiguration has errors. Please fix them before running simulations.")
        sys.exit(1)

    print("-" * 80 + "\n")


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Server Load Dynamics Simulator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--config",
        type=str,
        # required=True,
        help="Path to configuration file (YAML)",
    )

    parser.add_argument(
        "--scenario",
        type=str,
        default=None,
        help="Specific scenario name to run (requires --config)",
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="List available scenarios from config file",
    )

    parser.add_argument(
        "--validate",
        type=str,
        default=None,
        metavar="FILE",
        help="Validate a configuration file without running simulations",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print verbose output",
    )

    parser.add_argument(
        "--time-scale",
        type=float,
        default=None,
        metavar="SCALE",
        help="Wall-clock seconds per simulation second (e.g., 1.0=real-time, 10.0=10x slower)",
    )

    parser.add_argument(
        "--export-format",
        type=str,
        default="json",
        choices=["json", "csv", "both"],
        help="Export format for results (default: json)",
    )

    parser.add_argument(
        "--comparison",
        action="store_true",
        help="Generate comparison CSV when running multiple scenarios",
    )

    parser.add_argument(
        "--short-output",
        action="store_true",
        help="Minimal output: no progress bars, only key metrics",
    )

    return parser.parse_args()


def main():
    args = parse_arguments()
    short_output = getattr(args, "short_output", False)

    if not short_output:
        print("\n" + "=" * 80)
        print("SERVER LOAD DYNAMICS SIMULATOR")
        print("=" * 80)
        print(
            "\nThis simulator models server behavior under different traffic patterns,"
        )
        print("hardware configurations, and load balancing strategies.\n")

    if args.validate:
        validate_config(args.validate, verbose=args.verbose)
        return

    if args.list:
        if not short_output:
            print(f"Loading scenarios from {args.config}...\n")
        list_scenarios(args.config)
    else:
        run_scenarios_from_config(
            args.config,
            args.scenario,
            args.time_scale,
            export_format=args.export_format,
            comparison=args.comparison,
            short_output=short_output,
        )


if __name__ == "__main__":
    main()
