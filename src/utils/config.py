from typing import List, Optional, Dict, Any

from ..models.hardware import (
    HardwareConfig,
    HardwareProfile,
    ProgrammingLanguageProfile,
)
from ..models.distributions import ProcessingTimeDistribution
from ..traffic.generators import TrafficPattern, TrafficSpike
from ..load_balancing.strategies import LoadBalancingStrategy
from ..simulation.engine import SimulationScenario


class ScenarioBuilder:
    def __init__(self, name: str, duration: float = 3600.0):
        self.name = name
        self.duration = duration

        self.num_servers = 1
        self.hardware = HardwareConfig.from_profile(HardwareProfile.STANDARD)
        self.language = ProgrammingLanguageProfile.PYTHON
        self.base_request_rate = 10.0
        self.traffic_pattern = TrafficPattern.POISSON
        self.balancing_strategy = LoadBalancingStrategy.ROUND_ROBIN
        self.traffic_spikes: List[TrafficSpike] = []
        self.request_processing_time = 250.0
        self.request_timeout = 30000.0
        self.random_seed: Optional[int] = None
        self.time_scale: float = 1.0
        self.traffic_kwargs: Dict[str, Any] = {}

        self.processing_time_stddev: float = 0.0
        self.processing_time_distribution: ProcessingTimeDistribution = (
            ProcessingTimeDistribution.NORMAL
        )
        self.network_latency_mean: float = 0.0
        self.network_latency_stddev: float = 0.0
        self.cpu_degradation_enabled: bool = True

    def with_servers(self, count: int) -> "ScenarioBuilder":
        self.num_servers = count
        return self

    def with_hardware(self, hardware: HardwareConfig) -> "ScenarioBuilder":
        self.hardware = hardware
        return self

    def with_hardware_profile(self, profile: HardwareProfile) -> "ScenarioBuilder":
        self.hardware = HardwareConfig.from_profile(profile)
        return self

    def with_language(self, language: ProgrammingLanguageProfile) -> "ScenarioBuilder":
        self.language = language
        return self

    def with_request_rate(self, rate: float) -> "ScenarioBuilder":
        self.base_request_rate = rate
        return self

    def with_traffic_pattern(self, pattern: TrafficPattern) -> "ScenarioBuilder":
        self.traffic_pattern = pattern
        return self

    def with_balancing_strategy(
        self, strategy: LoadBalancingStrategy
    ) -> "ScenarioBuilder":
        self.balancing_strategy = strategy
        return self

    def with_spike(self, spike: TrafficSpike) -> "ScenarioBuilder":
        self.traffic_spikes.append(spike)
        return self

    def with_spikes(self, spikes: List[TrafficSpike]) -> "ScenarioBuilder":
        self.traffic_spikes = spikes
        return self

    def with_request_processing_time(self, time_ms: float) -> "ScenarioBuilder":
        self.request_processing_time = time_ms
        return self

    def with_request_timeout(self, timeout_ms: float) -> "ScenarioBuilder":
        self.request_timeout = timeout_ms
        return self

    def with_random_seed(self, seed: int) -> "ScenarioBuilder":
        self.random_seed = seed
        return self

    def with_traffic_kwargs(self, **kwargs) -> "ScenarioBuilder":
        self.traffic_kwargs.update(kwargs)
        return self

    def with_time_scale(self, time_scale: float) -> "ScenarioBuilder":
        self.time_scale = time_scale
        return self

    def with_processing_time_stddev(self, stddev: float) -> "ScenarioBuilder":
        self.processing_time_stddev = stddev
        return self

    def with_processing_time_distribution(
        self, distribution: ProcessingTimeDistribution
    ) -> "ScenarioBuilder":
        self.processing_time_distribution = distribution
        return self

    def with_network_latency(
        self, mean: float = 0.0, stddev: float = 0.0
    ) -> "ScenarioBuilder":
        self.network_latency_mean = mean
        self.network_latency_stddev = stddev
        return self

    def with_cpu_degradation(self, enabled: bool = True) -> "ScenarioBuilder":
        self.cpu_degradation_enabled = enabled
        return self

    def build(self) -> SimulationScenario:
        return SimulationScenario(
            name=self.name,
            duration=self.duration,
            num_servers=self.num_servers,
            hardware=self.hardware,
            language=self.language,
            base_request_rate=self.base_request_rate,
            traffic_pattern=self.traffic_pattern,
            balancing_strategy=self.balancing_strategy,
            traffic_spikes=self.traffic_spikes,
            request_processing_time=self.request_processing_time,
            request_timeout=self.request_timeout,
            random_seed=self.random_seed,
            time_scale=self.time_scale,
            processing_time_stddev=self.processing_time_stddev,
            processing_time_distribution=self.processing_time_distribution,
            network_latency_mean=self.network_latency_mean,
            network_latency_stddev=self.network_latency_stddev,
            cpu_degradation_enabled=self.cpu_degradation_enabled,
            **self.traffic_kwargs,
        )


class PredefinedScenarios:
    @staticmethod
    def baseline() -> SimulationScenario:
        return (
            ScenarioBuilder("baseline", duration=600.0)
            .with_servers(1)
            .with_hardware_profile(HardwareProfile.STANDARD)
            .with_language(ProgrammingLanguageProfile.PYTHON)
            .with_request_rate(10.0)
            .with_traffic_pattern(TrafficPattern.CONSTANT)
            .with_balancing_strategy(LoadBalancingStrategy.ROUND_ROBIN)
            .with_random_seed(42)
            .build()
        )

    @staticmethod
    def steady_state_poisson() -> SimulationScenario:
        return (
            ScenarioBuilder("steady_state_poisson", duration=1800.0)
            .with_servers(4)
            .with_hardware_profile(HardwareProfile.STANDARD)
            .with_language(ProgrammingLanguageProfile.NODEJS)
            .with_request_rate(20.0)
            .with_traffic_pattern(TrafficPattern.POISSON)
            .with_balancing_strategy(LoadBalancingStrategy.LEAST_CONNECTIONS)
            .with_random_seed(42)
            .build()
        )

    @staticmethod
    def traffic_spike() -> SimulationScenario:
        spike = TrafficSpike(
            start_time=300.0,
            duration=60.0,
            intensity_multiplier=5.0,
        )

        return (
            ScenarioBuilder("traffic_spike", duration=600.0)
            .with_servers(3)
            .with_hardware_profile(HardwareProfile.HIGH_PERFORMANCE)
            .with_language(ProgrammingLanguageProfile.GO)
            .with_request_rate(15.0)
            .with_traffic_pattern(TrafficPattern.POISSON)
            .with_balancing_strategy(LoadBalancingStrategy.LEAST_CONNECTIONS)
            .with_spike(spike)
            .with_random_seed(42)
            .build()
        )

    @staticmethod
    def bursty_traffic() -> SimulationScenario:
        return (
            ScenarioBuilder("bursty_traffic", duration=1200.0)
            .with_servers(2)
            .with_hardware_profile(HardwareProfile.STANDARD)
            .with_language(ProgrammingLanguageProfile.JAVA)
            .with_request_rate(10.0)
            .with_traffic_pattern(TrafficPattern.BURSTY)
            .with_balancing_strategy(LoadBalancingStrategy.LEAST_CONNECTIONS)
            .with_traffic_kwargs(burst_size_mean=8.0, burst_interval=3.0)
            .with_random_seed(42)
            .build()
        )

    @staticmethod
    def language_comparison() -> List[SimulationScenario]:
        languages = [
            ProgrammingLanguageProfile.PYTHON,
            ProgrammingLanguageProfile.NODEJS,
            ProgrammingLanguageProfile.JAVA,
            ProgrammingLanguageProfile.GO,
            ProgrammingLanguageProfile.RUST,
        ]

        scenarios = []
        for i, lang in enumerate(languages):
            scenario = (
                ScenarioBuilder(
                    f"language_comparison_{lang.name.lower()}", duration=600.0
                )
                .with_servers(2)
                .with_hardware_profile(HardwareProfile.STANDARD)
                .with_language(lang)
                .with_request_rate(20.0)
                .with_traffic_pattern(TrafficPattern.POISSON)
                .with_balancing_strategy(LoadBalancingStrategy.LEAST_CONNECTIONS)
                .with_random_seed(42 + i)
                .build()
            )
            scenarios.append(scenario)

        return scenarios

    @staticmethod
    def hardware_comparison() -> List[SimulationScenario]:
        profiles = [
            HardwareProfile.ENTRY_LEVEL,
            HardwareProfile.STANDARD,
            HardwareProfile.HIGH_PERFORMANCE,
            HardwareProfile.ENTERPRISE,
        ]

        scenarios = []
        for i, profile in enumerate(profiles):
            scenario = (
                ScenarioBuilder(f"hardware_comparison_{profile.value}", duration=600.0)
                .with_servers(2)
                .with_hardware_profile(profile)
                .with_language(ProgrammingLanguageProfile.NODEJS)
                .with_request_rate(20.0)
                .with_traffic_pattern(TrafficPattern.POISSON)
                .with_balancing_strategy(LoadBalancingStrategy.LEAST_CONNECTIONS)
                .with_random_seed(42 + i)
                .build()
            )
            scenarios.append(scenario)

        return scenarios

    @staticmethod
    def balancing_strategy_comparison() -> List[SimulationScenario]:
        strategies = [
            LoadBalancingStrategy.ROUND_ROBIN,
            LoadBalancingStrategy.LEAST_CONNECTIONS,
            LoadBalancingStrategy.LEAST_RESPONSE_TIME,
        ]

        scenarios = []
        for i, strategy in enumerate(strategies):
            scenario = (
                ScenarioBuilder(
                    f"balancing_comparison_{strategy.value}", duration=600.0
                )
                .with_servers(3)
                .with_hardware_profile(HardwareProfile.STANDARD)
                .with_language(ProgrammingLanguageProfile.NODEJS)
                .with_request_rate(25.0)
                .with_traffic_pattern(TrafficPattern.POISSON)
                .with_balancing_strategy(strategy)
                .with_random_seed(42 + i)
                .build()
            )
            scenarios.append(scenario)

        return scenarios
