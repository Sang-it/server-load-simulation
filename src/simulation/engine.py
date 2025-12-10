import logging
import sys
from typing import Any, Callable, Dict, List, Optional

import simpy
from ..models.server import Server, Request
from ..models.hardware import HardwareConfig, ProgrammingLanguageProfile
from ..models.distributions import ProcessingTimeDistribution
from ..load_balancing.strategies import LoadBalancingStrategy, BalancerFactory
from ..traffic.generators import (
    TrafficPattern,
    create_traffic_generator,
    TrafficSpike,
)
from ..metrics.collector import MetricsCollector, AggregatedMetrics


class SimulationScenario:
    MIN_DURATION = 0.01
    MAX_DURATION = 86400.0
    MIN_SERVERS = 1
    MAX_SERVERS = 1000
    MIN_REQUEST_RATE = 0.0
    MAX_REQUEST_RATE = 100000.0
    MIN_TIMEOUT = 100.0
    MAX_TIMEOUT = 3600000.0

    def __init__(
        self,
        name: str,
        duration: float,
        num_servers: int,
        hardware: HardwareConfig,
        language: ProgrammingLanguageProfile,
        base_request_rate: float,
        traffic_pattern: TrafficPattern,
        balancing_strategy: LoadBalancingStrategy,
        traffic_spikes: Optional[List[TrafficSpike]] = None,
        request_processing_time: float = 100.0,
        request_timeout: float = 30000.0,
        random_seed: Optional[int] = None,
        time_scale: float = 1.0,
        processing_time_stddev: float = 0.0,
        processing_time_distribution: ProcessingTimeDistribution = ProcessingTimeDistribution.NORMAL,
        network_latency_mean: float = 0.0,
        network_latency_stddev: float = 0.0,
        cpu_degradation_enabled: bool = True,
        **traffic_kwargs,
    ):
        self._validate_parameters(
            name,
            duration,
            num_servers,
            base_request_rate,
            request_processing_time,
            request_timeout,
            time_scale,
        )

        self.name = name
        self.duration = duration
        self.num_servers = num_servers
        self.hardware = hardware
        self.language = language
        self.base_request_rate = base_request_rate
        self.traffic_pattern = traffic_pattern
        self.balancing_strategy = balancing_strategy
        self.traffic_spikes = traffic_spikes or []
        self.request_processing_time = request_processing_time
        self.request_timeout = request_timeout
        self.random_seed = random_seed
        self.time_scale = time_scale
        self.processing_time_stddev = processing_time_stddev
        self.processing_time_distribution = processing_time_distribution
        self.network_latency_mean = network_latency_mean
        self.network_latency_stddev = network_latency_stddev
        self.cpu_degradation_enabled = cpu_degradation_enabled
        self.traffic_kwargs = traffic_kwargs

    @staticmethod
    def _validate_parameters(
        name: str,
        duration: float,
        num_servers: int,
        base_request_rate: float,
        request_processing_time: float,
        request_timeout: float,
        time_scale: float,
    ) -> None:
        errors = []

        if not name or not isinstance(name, str):
            errors.append("Scenario name must be a non-empty string")

        if not isinstance(duration, (int, float)):
            errors.append("Duration must be a number")
        elif duration < SimulationScenario.MIN_DURATION:
            errors.append(
                f"Duration must be >= {SimulationScenario.MIN_DURATION}s "
                f"(got {duration}s)"
            )
        elif duration > SimulationScenario.MAX_DURATION:
            errors.append(
                f"Duration must be <= {SimulationScenario.MAX_DURATION}s "
                f"(got {duration}s)"
            )

        if not isinstance(num_servers, int):
            errors.append("Number of servers must be an integer")
        elif num_servers < SimulationScenario.MIN_SERVERS:
            errors.append(
                f"Must have at least {SimulationScenario.MIN_SERVERS} server "
                f"(got {num_servers})"
            )
        elif num_servers > SimulationScenario.MAX_SERVERS:
            errors.append(
                f"Cannot have more than {SimulationScenario.MAX_SERVERS} servers "
                f"(got {num_servers})"
            )

        if not isinstance(base_request_rate, (int, float)):
            errors.append("Base request rate must be a number")
        elif base_request_rate < SimulationScenario.MIN_REQUEST_RATE:
            errors.append(f"Request rate cannot be negative (got {base_request_rate})")
        elif base_request_rate > SimulationScenario.MAX_REQUEST_RATE:
            errors.append(
                f"Request rate too high (max: {SimulationScenario.MAX_REQUEST_RATE}, "
                f"got {base_request_rate})"
            )

        if not isinstance(request_timeout, (int, float)):
            errors.append("Request timeout must be a number")
        elif request_timeout < SimulationScenario.MIN_TIMEOUT:
            errors.append(
                f"Request timeout must be >= {SimulationScenario.MIN_TIMEOUT}ms "
                f"(got {request_timeout}ms)"
            )
        elif request_timeout > SimulationScenario.MAX_TIMEOUT:
            errors.append(
                f"Request timeout must be <= {SimulationScenario.MAX_TIMEOUT}ms "
                f"(got {request_timeout}ms)"
            )

        if not isinstance(request_processing_time, (int, float)):
            errors.append("Request processing time must be a number")
        elif request_processing_time <= 0:
            errors.append(
                f"Request processing time must be positive (got {request_processing_time}ms)"
            )

        if not isinstance(time_scale, (int, float)):
            errors.append("Time scale must be a number")
        elif time_scale <= 0:
            errors.append(f"Time scale must be positive (got {time_scale})")

        if errors:
            raise ValueError("Invalid scenario parameters:\n  " + "\n  ".join(errors))


class LoadSimulator:
    DEFAULT_NUM_WORKERS = 1
    METRICS_UPDATE_INTERVAL_S = 1.0
    PROGRESS_UPDATE_INTERVAL_S = 0.1

    def __init__(self, scenario: SimulationScenario, show_progress: bool = True):
        self.scenario = scenario
        self.env = simpy.Environment()
        self.metrics_collector = MetricsCollector()
        self.show_progress = show_progress

        self.servers: List[Server] = []
        self.request_counter = 0

        self.metrics_callbacks: List[Callable[[AggregatedMetrics, float], None]] = []
        self.update_interval = self.METRICS_UPDATE_INTERVAL_S
        self.last_update_count = 0

    def setup(self) -> None:
        for i in range(self.scenario.num_servers):
            server = Server(
                server_id=i,
                env=self.env,
                hardware=self.scenario.hardware,
                language=self.scenario.language,
                num_workers=self.scenario.hardware.num_cores,
                request_timeout=self.scenario.request_timeout,
                metrics_collector=self.metrics_collector,
                processing_time_stddev=self.scenario.processing_time_stddev,
                network_latency_mean=self.scenario.network_latency_mean,
                network_latency_stddev=self.scenario.network_latency_stddev,
                processing_time_distribution=self.scenario.processing_time_distribution,
                cpu_degradation_enabled=self.scenario.cpu_degradation_enabled,
                random_seed=self.scenario.random_seed,
            )
            self.servers.append(server)

        self.load_balancer = BalancerFactory.create_balancer(
            self.scenario.balancing_strategy,
            self.servers,
        )

        self.traffic_generator = create_traffic_generator(
            pattern=self.scenario.traffic_pattern,
            base_rate=self.scenario.base_request_rate,
            spikes=self.scenario.traffic_spikes,
            random_seed=self.scenario.random_seed,
            **self.scenario.traffic_kwargs,
        )

        self.env.process(self._request_arrival_process())

        self.env.process(self._metrics_update_process())

    def _request_arrival_process(self) -> Any:
        current_time = 0.0

        while current_time < self.scenario.duration:
            inter_arrival = self.traffic_generator.next_arrival_time(current_time)

            yield self.env.timeout(inter_arrival)
            current_time = self.env.now

            if current_time >= self.scenario.duration:
                break

            self.request_counter += 1
            request = Request(
                request_id=self.request_counter,
                arrival_time=current_time,
                processing_time=self.scenario.request_processing_time,
            )

            server = self.load_balancer.select_server()
            if server:
                server.submit_request(request)
                self.load_balancer.record_request()

    def run(self) -> None:
        import time
        import threading

        self.setup()

        start_time = time.time()

        time_scale = self.scenario.time_scale if self.scenario.time_scale > 0 else 1.0
        target_duration = self.scenario.duration * time_scale

        if self.show_progress:
            progress_thread = threading.Thread(
                target=self._display_progress,
                args=(start_time, target_duration),
                daemon=True,
            )
            progress_thread.start()

        self.env.run()

        elapsed = time.time() - start_time

        remaining_time = target_duration - elapsed
        if remaining_time > 0:
            time.sleep(remaining_time)

        if self.show_progress:
            progress_bar = "█" * 40
            sys.stdout.write(
                f"\r[{progress_bar}] 100.0% ({self.scenario.duration:.1f}s/{self.scenario.duration:.1f}s)\n"
            )
            sys.stdout.flush()

    def _display_progress(self, start_time: float, target_duration: float) -> None:
        import time

        while True:
            elapsed = time.time() - start_time

            if target_duration > 0:
                progress = min(100.0, (elapsed / target_duration) * 100)
                sim_time = progress / 100 * self.scenario.duration
            else:
                progress = 100.0
                sim_time = self.scenario.duration

            bar_length = 40
            filled = int(bar_length * progress / 100)
            bar = "█" * filled + "░" * (bar_length - filled)
            sys.stdout.write(
                f"\r[{bar}] {progress:5.1f}% ({sim_time:.1f}s/{self.scenario.duration:.1f}s)"
            )
            sys.stdout.flush()

            if progress >= 100.0:
                break

            time.sleep(self.PROGRESS_UPDATE_INTERVAL_S)

    def get_results(self) -> Dict[str, Any]:
        metrics = self.metrics_collector.aggregate(self.scenario.duration)

        return {
            "scenario": self.scenario.name,
            "duration_s": self.scenario.duration,
            "num_servers": self.scenario.num_servers,
            "hardware": {
                "cpu_speed_ghz": self.scenario.hardware.cpu_speed,
                "memory_gb": self.scenario.hardware.memory_capacity,
                "io_latency_ms": self.scenario.hardware.io_latency,
            },
            "language": self.scenario.language.name,
            "traffic_pattern": self.scenario.traffic_pattern.value,
            "balancing_strategy": self.scenario.balancing_strategy.value,
            "base_request_rate_rps": self.scenario.base_request_rate,
            "metrics": metrics.to_dict(),
            "per_server_stats": self.metrics_collector.get_per_server_stats(),
        }

    def get_detailed_results(self) -> Dict[str, Any]:
        results = self.get_results()

        server_details = []
        for server in self.servers:
            server_details.append(server.get_statistics())

        results["server_details"] = server_details

        return results

    def register_metrics_callback(
        self,
        callback: Callable[[AggregatedMetrics, float], None],
        interval: float = 1.0,
    ) -> None:
        self.metrics_callbacks.append(callback)
        self.update_interval = interval

    def _metrics_update_process(self) -> Any:
        current_time = 0.0

        while current_time < self.scenario.duration:
            yield self.env.timeout(self.update_interval)
            current_time = self.env.now

            if current_time > self.scenario.duration:
                break

            for server in self.servers:
                utilization = server._get_current_cpu_utilization()
                self.metrics_collector.record_server_utilization(
                    server.server_id, utilization
                )

            if self.metrics_collector.metrics:
                metrics = self.metrics_collector.aggregate(current_time)
            else:
                metrics = AggregatedMetrics(simulation_duration=current_time)

            for callback in self.metrics_callbacks:
                try:
                    callback(metrics, current_time)
                except Exception as e:
                    logging.warning(
                        f"Metrics callback failed at simulation time {current_time:.2f}s: {e}",
                        exc_info=True,
                    )
