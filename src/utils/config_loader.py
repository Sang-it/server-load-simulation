import yaml
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from .config import ScenarioBuilder
from ..models.hardware import (
    HardwareProfile,
    HardwareConfig,
    ProgrammingLanguageProfile,
)
from ..models.distributions import ProcessingTimeDistribution
from ..traffic.generators import TrafficPattern, TrafficSpike
from ..load_balancing.strategies import LoadBalancingStrategy
from ..simulation.engine import SimulationScenario


class ConfigLoader:
    HARDWARE_PROFILES = {
        "ENTRY_LEVEL": HardwareProfile.ENTRY_LEVEL,
        "STANDARD": HardwareProfile.STANDARD,
        "HIGH_PERFORMANCE": HardwareProfile.HIGH_PERFORMANCE,
        "ENTERPRISE": HardwareProfile.ENTERPRISE,
    }

    LANGUAGES = {
        "PYTHON": ProgrammingLanguageProfile.PYTHON,
        "NODEJS": ProgrammingLanguageProfile.NODEJS,
        "JAVA": ProgrammingLanguageProfile.JAVA,
        "GO": ProgrammingLanguageProfile.GO,
        "RUST": ProgrammingLanguageProfile.RUST,
        "DOTNET": ProgrammingLanguageProfile.DOTNET,
    }

    TRAFFIC_PATTERNS = {
        "POISSON": TrafficPattern.POISSON,
        "BURSTY": TrafficPattern.BURSTY,
        "PERIODIC": TrafficPattern.PERIODIC,
        "CONSTANT": TrafficPattern.CONSTANT,
        "EXPONENTIAL_BURST": TrafficPattern.EXPONENTIAL_BURST,
        "WAVE": TrafficPattern.WAVE,
    }

    LOAD_BALANCING_STRATEGIES = {
        "ROUND_ROBIN": LoadBalancingStrategy.ROUND_ROBIN,
        "LEAST_CONNECTIONS": LoadBalancingStrategy.LEAST_CONNECTIONS,
        "WEIGHTED_ROUND_ROBIN": LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN,
        "LEAST_RESPONSE_TIME": LoadBalancingStrategy.LEAST_RESPONSE_TIME,
        "RANDOM": LoadBalancingStrategy.RANDOM,
        "CPU_AWARE": LoadBalancingStrategy.CPU_AWARE,
    }

    @staticmethod
    def _find_closest_match(value: str, valid_options: List[str]) -> Optional[str]:
        if not value or not valid_options:
            return None

        value_lower = value.lower()

        for option in valid_options:
            if option.lower() == value_lower:
                return option

        min_distance = float("inf")
        closest = None
        for option in valid_options:
            distance = sum(
                1 for a, b in zip(value_lower, option.lower()) if a != b
            ) + abs(len(value_lower) - len(option))
            if distance < min_distance:
                min_distance = distance
                closest = option

        return closest if min_distance <= 3 else None

    @staticmethod
    def _is_valid_hardware_config(config: dict) -> bool:
        if not isinstance(config, dict):
            return False
        required_fields = {"cpu_speed", "memory_capacity", "io_latency"}
        return required_fields.issubset(config.keys())

    @staticmethod
    def _parse_hardware(hardware_config: Any) -> tuple:
        if isinstance(hardware_config, str):
            if hardware_config in ConfigLoader.HARDWARE_PROFILES:
                return ConfigLoader.HARDWARE_PROFILES[hardware_config], None
            else:
                return None, f"Unknown hardware profile: {hardware_config}"
        elif isinstance(hardware_config, dict):
            if ConfigLoader._is_valid_hardware_config(hardware_config):
                try:
                    return HardwareConfig.from_dict(hardware_config), None
                except Exception as e:
                    return None, f"Invalid hardware config: {str(e)}"
            else:
                return (
                    None,
                    "Hardware config dict must contain: cpu_speed, memory_capacity, io_latency",
                )
        else:
            return (
                None,
                f"Hardware must be a string (profile name) or dict (custom config), got {type(hardware_config)}",
            )

    @staticmethod
    def load_config_file(file_path: Path) -> Dict[str, Any]:
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")

        file_suffix = file_path.suffix.lower()

        if file_suffix == ".json":
            with open(file_path, "r") as f:
                config = json.load(f)
        elif file_suffix in (".yaml", ".yml"):
            with open(file_path, "r") as f:
                config = yaml.safe_load(f)
        else:
            raise ValueError(
                f"Unsupported configuration file format: {file_suffix}. "
                f"Supported formats: .yaml, .yml, .json"
            )

        return config

    @staticmethod
    def validate_scenario(scenario_dict: Dict[str, Any]) -> tuple:
        errors = []
        warnings = []

        if "name" not in scenario_dict:
            errors.append(
                "Missing required field: 'name' (e.g., 'name: my_test_scenario')"
            )

        duration = scenario_dict.get("duration")
        if duration is not None:
            if not isinstance(duration, (int, float)) or duration <= 0:
                errors.append("'duration' must be a positive number")

        servers = scenario_dict.get("num_servers") or scenario_dict.get("servers")
        if servers is not None:
            if not isinstance(servers, int) or servers < 1:
                errors.append("'num_servers' must be a positive integer")

        base_request_rate = scenario_dict.get("base_request_rate")
        if base_request_rate is not None:
            if not isinstance(base_request_rate, (int, float)) or base_request_rate < 0:
                errors.append("'base_request_rate' must be non-negative")

        request_processing_time = scenario_dict.get("request_processing_time")
        if request_processing_time is not None:
            if (
                not isinstance(request_processing_time, (int, float))
                or request_processing_time <= 0
            ):
                errors.append("'request_processing_time' must be positive")

        request_timeout = scenario_dict.get("request_timeout")
        if request_timeout is not None:
            if not isinstance(request_timeout, (int, float)) or request_timeout <= 0:
                errors.append("'request_timeout' must be positive")

        time_scale = scenario_dict.get("time_scale")
        if time_scale is not None:
            if not isinstance(time_scale, (int, float)) or time_scale <= 0:
                errors.append(
                    "'time_scale' must be positive (e.g., 1.0 for real-time, 10.0 for 10x slower)"
                )

        hardware_config = scenario_dict.get("hardware", "STANDARD")
        if isinstance(hardware_config, str):
            if hardware_config not in ConfigLoader.HARDWARE_PROFILES:
                valid_options = ", ".join(ConfigLoader.HARDWARE_PROFILES.keys())
                errors.append(
                    f"Invalid hardware profile '{hardware_config}'. "
                    f"Valid options: {valid_options} "
                    f"(e.g., 'hardware: STANDARD')"
                )
        elif isinstance(hardware_config, dict):
            if not ConfigLoader._is_valid_hardware_config(hardware_config):
                errors.append(
                    "Hardware config dict must contain: cpu_speed, memory_capacity, io_latency"
                )
        else:
            errors.append(
                f"Hardware must be a string (profile name) or dict (custom config), got {type(hardware_config)}"
            )

        language_str = scenario_dict.get("language", "PYTHON")
        if language_str not in ConfigLoader.LANGUAGES:
            valid_options = list(ConfigLoader.LANGUAGES.keys())
            suggestion = ConfigLoader._find_closest_match(language_str, valid_options)
            error_msg = (
                f"Invalid language '{language_str}'. "
                f"Valid options: {', '.join(valid_options)}"
            )
            if suggestion:
                error_msg += f" (Did you mean '{suggestion}'?)"
            errors.append(error_msg)

        pattern_str = scenario_dict.get("traffic_pattern", "POISSON")
        if pattern_str not in ConfigLoader.TRAFFIC_PATTERNS:
            valid_options = list(ConfigLoader.TRAFFIC_PATTERNS.keys())
            suggestion = ConfigLoader._find_closest_match(pattern_str, valid_options)
            error_msg = (
                f"Invalid traffic pattern '{pattern_str}'. "
                f"Valid options: {', '.join(valid_options)}"
            )
            if suggestion:
                error_msg += f" (Did you mean '{suggestion}'?)"
            errors.append(error_msg)

        strategy_str = scenario_dict.get("balancing_strategy", "ROUND_ROBIN")
        if strategy_str not in ConfigLoader.LOAD_BALANCING_STRATEGIES:
            valid_options = list(ConfigLoader.LOAD_BALANCING_STRATEGIES.keys())
            suggestion = ConfigLoader._find_closest_match(strategy_str, valid_options)
            error_msg = (
                f"Invalid load balancing strategy '{strategy_str}'. "
                f"Valid options: {', '.join(valid_options)}"
            )
            if suggestion:
                error_msg += f" (Did you mean '{suggestion}'?)"
            errors.append(error_msg)

        spikes_data = scenario_dict.get("spikes", [])
        if not isinstance(spikes_data, list):
            errors.append("'spikes' must be a list")
        else:
            for i, spike_dict in enumerate(spikes_data):
                start_time = spike_dict.get("start_time")
                if start_time is not None and (
                    not isinstance(start_time, (int, float)) or start_time < 0
                ):
                    errors.append(f"Spike {i}: 'start_time' must be non-negative")

                duration = spike_dict.get("duration")
                if duration is not None and (
                    not isinstance(duration, (int, float)) or duration <= 0
                ):
                    errors.append(f"Spike {i}: 'duration' must be positive")

                intensity = spike_dict.get("intensity_multiplier")
                if intensity is not None and (
                    not isinstance(intensity, (int, float)) or intensity <= 0
                ):
                    errors.append(f"Spike {i}: 'intensity_multiplier' must be positive")

        if base_request_rate == 0:
            warnings.append("'base_request_rate' is 0 (no traffic will be generated)")

        processing_time_stddev = scenario_dict.get("processing_time_stddev")
        if processing_time_stddev is not None:
            if (
                not isinstance(processing_time_stddev, (int, float))
                or processing_time_stddev < 0
            ):
                errors.append("'processing_time_stddev' must be non-negative")

        processing_time_distribution = scenario_dict.get(
            "processing_time_distribution", "NORMAL"
        )
        valid_names = [e.name for e in ProcessingTimeDistribution]
        if processing_time_distribution.upper() not in valid_names:
            errors.append(
                f"'processing_time_distribution' must be one of {valid_names}, "
                f"got '{processing_time_distribution}'"
            )
        valid_distributions = tuple(
            v.value.upper() for v in ProcessingTimeDistribution
        ) + tuple(v.value for v in ProcessingTimeDistribution)
        if processing_time_distribution.upper() not in valid_distributions:
            errors.append(
                f"'processing_time_distribution' must be 'NORMAL' or 'LOGNORMAL', "
                f"got '{processing_time_distribution}'"
            )

        network_latency_mean = scenario_dict.get("network_latency_mean")
        if network_latency_mean is not None:
            if (
                not isinstance(network_latency_mean, (int, float))
                or network_latency_mean < 0
            ):
                errors.append("'network_latency_mean' must be non-negative")

        network_latency_stddev = scenario_dict.get("network_latency_stddev")
        if network_latency_stddev is not None:
            if (
                not isinstance(network_latency_stddev, (int, float))
                or network_latency_stddev < 0
            ):
                errors.append("'network_latency_stddev' must be non-negative")

        cpu_degradation_enabled = scenario_dict.get("cpu_degradation_enabled")
        if cpu_degradation_enabled is not None:
            if not isinstance(cpu_degradation_enabled, bool):
                errors.append(
                    "'cpu_degradation_enabled' must be a boolean (true/false)"
                )

        is_valid = len(errors) == 0
        return is_valid, errors, warnings

    @staticmethod
    def parse_scenario(scenario_dict: Dict[str, Any]) -> SimulationScenario:
        is_valid, errors, warnings = ConfigLoader.validate_scenario(scenario_dict)

        if not is_valid:
            scenario_name = scenario_dict.get("name", "unknown")
            error_msg = f"Invalid scenario '{scenario_name}':\n"
            for error in errors:
                error_msg += f"  - {error}\n"
            raise ValueError(error_msg)

        if warnings:
            scenario_name = scenario_dict.get("name", "unknown")
            for warning in warnings:
                print(f"Warning for scenario '{scenario_name}': {warning}")

        name = scenario_dict.get("name", "unnamed_scenario")
        duration = scenario_dict.get("duration", 600.0)
        servers = scenario_dict.get("num_servers") or scenario_dict.get("servers", 1)
        base_request_rate = scenario_dict.get("base_request_rate", 10.0)
        request_processing_time = scenario_dict.get("request_processing_time", 100.0)
        request_timeout = scenario_dict.get("request_timeout", 30000.0)
        random_seed = scenario_dict.get("random_seed", None)
        time_scale = scenario_dict.get("time_scale", 1.0)

        processing_time_stddev = scenario_dict.get("processing_time_stddev", 0.0)
        processing_time_dist_str = scenario_dict.get(
            "processing_time_distribution", "NORMAL"
        )
        try:
            processing_time_distribution = ProcessingTimeDistribution[
                processing_time_dist_str.upper()
            ]
        except KeyError:
            raise ValueError(
                f"Invalid processing_time_distribution: {processing_time_dist_str}"
            )
        network_latency_mean = scenario_dict.get("network_latency_mean", 0.0)
        network_latency_stddev = scenario_dict.get("network_latency_stddev", 0.0)
        cpu_degradation_enabled = scenario_dict.get("cpu_degradation_enabled", True)

        hardware_input = scenario_dict.get("hardware", "STANDARD")
        hardware_obj, error = ConfigLoader._parse_hardware(hardware_input)
        if error:
            raise ValueError(error)

        language_str = scenario_dict.get("language", "PYTHON")
        language = ConfigLoader.LANGUAGES.get(language_str)
        if not language:
            raise ValueError(f"Unknown language: {language_str}")

        pattern_str = scenario_dict.get("traffic_pattern", "POISSON")
        traffic_pattern = ConfigLoader.TRAFFIC_PATTERNS.get(pattern_str)
        if not traffic_pattern:
            raise ValueError(f"Unknown traffic pattern: {pattern_str}")

        strategy_str = scenario_dict.get("balancing_strategy", "ROUND_ROBIN")
        strategy = ConfigLoader.LOAD_BALANCING_STRATEGIES.get(strategy_str)
        if not strategy:
            raise ValueError(f"Unknown load balancing strategy: {strategy_str}")

        spikes = []
        spikes_data = scenario_dict.get("spikes", [])
        for spike_dict in spikes_data:
            spike = TrafficSpike(
                start_time=spike_dict.get("start_time", 0),
                duration=spike_dict.get("duration", 60),
                intensity_multiplier=spike_dict.get("intensity_multiplier", 2.0),
            )
            spikes.append(spike)

        traffic_kwargs = scenario_dict.get("traffic_kwargs", {})

        builder = ScenarioBuilder(name, duration)
        builder.with_servers(servers)

        if isinstance(hardware_input, str):
            builder.with_hardware_profile(hardware_obj)
        else:
            builder.with_hardware(hardware_obj)

        builder.with_language(language)
        builder.with_request_rate(base_request_rate)
        builder.with_traffic_pattern(traffic_pattern)
        builder.with_balancing_strategy(strategy)
        builder.with_request_processing_time(request_processing_time)
        builder.with_request_timeout(request_timeout)
        builder.with_time_scale(time_scale)

        if processing_time_stddev > 0:
            builder.with_processing_time_stddev(processing_time_stddev)
        if processing_time_distribution != "normal":
            builder.with_processing_time_distribution(processing_time_distribution)
        if network_latency_mean > 0:
            builder.with_network_latency(network_latency_mean, network_latency_stddev)
        if cpu_degradation_enabled:
            builder.with_cpu_degradation(True)

        if spikes:
            builder.with_spikes(spikes)

        if random_seed:
            builder.with_random_seed(random_seed)

        if traffic_kwargs:
            builder.with_traffic_kwargs(**traffic_kwargs)

        return builder.build()

    @staticmethod
    def validate_config_file(file_path: Path) -> tuple:
        errors = []
        warnings = []

        try:
            config = ConfigLoader.load_config_file(file_path)
        except FileNotFoundError as e:
            errors.append(str(e))
            return False, errors, warnings
        except Exception as e:
            errors.append(f"Error parsing YAML file: {e}")
            return False, errors, warnings

        if "scenarios" not in config:
            errors.append("Missing required 'scenarios' key in configuration")
            return False, errors, warnings

        scenarios_data = config.get("scenarios", [])

        if not isinstance(scenarios_data, list):
            errors.append("'scenarios' must be a list")
            return False, errors, warnings

        if len(scenarios_data) == 0:
            warnings.append("No scenarios defined in configuration")

        seen_names = set()
        for i, scenario_dict in enumerate(scenarios_data):
            scenario_name = scenario_dict.get("name", f"scenario_{i}")

            if scenario_name in seen_names:
                errors.append(f"Duplicate scenario name: '{scenario_name}'")
            seen_names.add(scenario_name)

            is_valid, scenario_errors, scenario_warnings = (
                ConfigLoader.validate_scenario(scenario_dict)
            )
            for error in scenario_errors:
                errors.append(f"Scenario '{scenario_name}': {error}")
            for warning in scenario_warnings:
                warnings.append(f"Scenario '{scenario_name}': {warning}")

        is_valid = len(errors) == 0
        return is_valid, errors, warnings

    @staticmethod
    def load_scenarios_from_file(file_path: Path) -> List[SimulationScenario]:
        config = ConfigLoader.load_config_file(file_path)

        scenarios = []
        scenarios_data = config.get("scenarios", [])

        for scenario_dict in scenarios_data:
            try:
                scenario = ConfigLoader.parse_scenario(scenario_dict)
                scenarios.append(scenario)
            except Exception as e:
                scenario_name = scenario_dict.get("name", "unknown")
                print(f"Warning: Failed to parse scenario '{scenario_name}': {e}")
                continue

        return scenarios

    @staticmethod
    def load_scenario_by_name(
        file_path: Path, name: str
    ) -> Optional[SimulationScenario]:
        config = ConfigLoader.load_config_file(file_path)
        scenarios_data = config.get("scenarios", [])

        for scenario_dict in scenarios_data:
            if scenario_dict.get("name") == name:
                return ConfigLoader.parse_scenario(scenario_dict)

        return None

    @staticmethod
    def list_available_scenarios(file_path: Path) -> List[Dict[str, Any]]:
        config = ConfigLoader.load_config_file(file_path)
        scenarios_data = config.get("scenarios", [])

        scenario_info = []
        for scenario_dict in scenarios_data:
            info = {
                "name": scenario_dict.get("name", "unnamed"),
                "description": scenario_dict.get("description", "No description"),
                "servers": scenario_dict.get("num_servers")
                or scenario_dict.get("servers", 1),
                "duration": scenario_dict.get("duration", 600.0),
                "language": scenario_dict.get("language", "PYTHON"),
                "traffic_pattern": scenario_dict.get("traffic_pattern", "POISSON"),
                "balancing_strategy": scenario_dict.get(
                    "balancing_strategy", "ROUND_ROBIN"
                ),
            }
            scenario_info.append(info)

        return scenario_info

    @staticmethod
    def create_default_config(output_path: Path, format: str = "yaml") -> None:
        default_config = {
            "scenarios": [
                {
                    "name": "baseline",
                    "description": "Baseline scenario with single server",
                    "duration": 300.0,
                    "num_servers": 1,
                    "hardware": "STANDARD",
                    "language": "PYTHON",
                    "base_request_rate": 10.0,
                    "traffic_pattern": "POISSON",
                    "balancing_strategy": "ROUND_ROBIN",
                    "request_processing_time": 100.0,
                    "request_timeout": 30000.0,
                    "random_seed": 42,
                    "traffic_kwargs": {},
                }
            ]
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format == "auto" or format is None:
            format = "json" if output_path.suffix.lower() == ".json" else "yaml"

        if format.lower() == "json":
            with open(output_path, "w") as f:
                json.dump(default_config, f, indent=2)
        elif format.lower() in ("yaml", "yml"):
            with open(output_path, "w") as f:
                yaml.dump(default_config, f, default_flow_style=False, sort_keys=False)
        else:
            raise ValueError(
                f"Unsupported format: {format}. Supported formats: yaml, json"
            )

        print(f"Default configuration created at: {output_path}")


def load_scenarios(
    config_file: str = "config/default_scenarios.yaml",
) -> List[SimulationScenario]:
    config_path = Path(config_file)
    return ConfigLoader.load_scenarios_from_file(config_path)


def list_scenarios(config_file: str = "config/default_scenarios.yaml") -> None:
    config_path = Path(config_file)
    scenarios = ConfigLoader.list_available_scenarios(config_path)

    print("\n" + "=" * 80)
    print("AVAILABLE SCENARIOS")
    print("=" * 80 + "\n")

    for i, scenario in enumerate(scenarios, 1):
        print(f"{i}. {scenario['name']}")
        print(f"   Description: {scenario['description']}")
        print(f"   Servers: {scenario['servers']} | Duration: {scenario['duration']}s")
        print(
            f"   Hardware: {scenario.get('hardware', 'N/A')} | Language: {scenario['language']}"
        )
        print(
            f"   Traffic: {scenario['traffic_pattern']} | Balancing: {scenario['balancing_strategy']}"
        )
        print()

    print("=" * 80 + "\n")
