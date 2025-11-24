import math
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class TrafficPattern(Enum):
    POISSON = "poisson"
    BURSTY = "bursty"
    PERIODIC = "periodic"
    CONSTANT = "constant"
    EXPONENTIAL_BURST = "exponential_burst"
    WAVE = "wave"


@dataclass
class TrafficSpike:
    start_time: float
    duration: float
    intensity_multiplier: float


class TrafficGenerator(ABC):
    def __init__(self, base_rate: float, random_seed: Optional[int] = None):
        self.base_rate = base_rate
        self.random_seed = random_seed
        self.rng = random.Random(random_seed)

    @abstractmethod
    def next_arrival_time(self, current_time: float) -> float:
        pass

    @abstractmethod
    def get_request_rate(self, current_time: float) -> float:
        pass

    def _apply_spikes(
        self, base_rate: float, current_time: float, spikes: List[TrafficSpike]
    ) -> float:
        for spike in spikes:
            if spike.start_time <= current_time < spike.start_time + spike.duration:
                return base_rate * spike.intensity_multiplier

        return base_rate


class PoissonTrafficGenerator(TrafficGenerator):
    def __init__(
        self,
        base_rate: float,
        spikes: Optional[List[TrafficSpike]] = None,
        random_seed: Optional[int] = None,
    ):
        super().__init__(base_rate, random_seed)
        self.spikes = spikes or []
        self.spikes.sort(key=lambda s: s.start_time)

    def next_arrival_time(self, current_time: float) -> float:
        current_rate = self.get_request_rate(current_time)
        if current_rate <= 0:
            return float("inf")

        u = self.rng.random()
        return -math.log(u) / current_rate

    def get_request_rate(self, current_time: float) -> float:
        return self._apply_spikes(self.base_rate, current_time, self.spikes)


class BurstyTrafficGenerator(TrafficGenerator):
    DEFAULT_BURST_SIZE_MEAN = 5.0
    DEFAULT_BURST_INTERVAL = 2.0

    def __init__(
        self,
        base_rate: float,
        burst_size_mean: float = DEFAULT_BURST_SIZE_MEAN,
        burst_interval: float = DEFAULT_BURST_INTERVAL,
        spikes: Optional[List[TrafficSpike]] = None,
        random_seed: Optional[int] = None,
    ):
        super().__init__(base_rate, random_seed)
        self.burst_size_mean = burst_size_mean
        self.burst_interval = burst_interval
        self.spikes = spikes or []
        self.spikes.sort(key=lambda s: s.start_time)

        self._burst_queue: List[float] = []
        self._next_burst_time = self._generate_next_burst_time()

    def _generate_next_burst_time(self) -> float:
        u = self.rng.random()
        return -math.log(u) / (1.0 / self.burst_interval)

    def _generate_burst_size(self) -> int:
        mean = self.burst_size_mean
        count = 0
        prob = math.exp(-mean)
        cumsum = prob
        u = self.rng.random()

        while u > cumsum:
            count += 1
            prob *= mean / count
            cumsum += prob

        return max(1, count)

    def next_arrival_time(self, current_time: float) -> float:
        if not self._burst_queue:
            burst_delay = self._next_burst_time

            burst_size = self._generate_burst_size()
            current_rate = self.get_request_rate(current_time)

            for _ in range(burst_size):
                if current_rate > 0:
                    u = self.rng.random()
                    inter_arrival = -math.log(u) / current_rate
                    self._burst_queue.append(inter_arrival)

            self._next_burst_time = self._generate_next_burst_time()
            return burst_delay

        return self._burst_queue.pop(0)

    def get_request_rate(self, current_time: float) -> float:
        return self._apply_spikes(self.base_rate, current_time, self.spikes)


class PeriodicTrafficGenerator(TrafficGenerator):
    DEFAULT_AMPLITUDE_FACTOR = 0.5

    def __init__(
        self,
        base_rate: float,
        period: float,
        amplitude_factor: float = DEFAULT_AMPLITUDE_FACTOR,
        spikes: Optional[List[TrafficSpike]] = None,
        random_seed: Optional[int] = None,
    ):
        super().__init__(base_rate, random_seed)
        self.period = period
        self.amplitude_factor = amplitude_factor
        self.spikes = spikes or []
        self.spikes.sort(key=lambda s: s.start_time)

    def next_arrival_time(self, current_time: float) -> float:
        current_rate = self.get_request_rate(current_time)
        if current_rate <= 0:
            return float("inf")

        u = self.rng.random()
        return -math.log(u) / current_rate

    def get_request_rate(self, current_time: float) -> float:
        periodic_component = math.cos(2 * math.pi * current_time / self.period)
        rate = self.base_rate * (1 + self.amplitude_factor * periodic_component)

        rate = self._apply_spikes(rate, current_time, self.spikes)

        return max(0, rate)


class ConstantTrafficGenerator(TrafficGenerator):
    def __init__(
        self,
        base_rate: float,
        spikes: Optional[List[TrafficSpike]] = None,
        random_seed: Optional[int] = None,
    ):
        super().__init__(base_rate, random_seed)
        self.spikes = spikes or []
        self.spikes.sort(key=lambda s: s.start_time)

    def next_arrival_time(self, current_time: float) -> float:
        current_rate = self.get_request_rate(current_time)
        if current_rate <= 0:
            return float("inf")
        return 1.0 / current_rate

    def get_request_rate(self, current_time: float) -> float:
        return self._apply_spikes(self.base_rate, current_time, self.spikes)


class ExponentialBurstTrafficGenerator(TrafficGenerator):
    DEFAULT_BURST_RATE = 0.5
    DEFAULT_MEAN_BURST_SIZE = 8.0

    def __init__(
        self,
        base_rate: float,
        burst_rate: float = DEFAULT_BURST_RATE,
        mean_burst_size: float = DEFAULT_MEAN_BURST_SIZE,
        spikes: Optional[List[TrafficSpike]] = None,
        random_seed: Optional[int] = None,
    ):
        super().__init__(base_rate, random_seed)
        self.burst_rate = burst_rate
        self.mean_burst_size = mean_burst_size
        self.spikes = spikes or []
        self.spikes.sort(key=lambda s: s.start_time)

        self._burst_queue: List[float] = []
        self._next_burst_time = self._generate_next_burst_time()

    def _generate_next_burst_time(self) -> float:
        if self.burst_rate <= 0:
            return float("inf")

        u = self.rng.random()
        u = max(1e-10, min(u, 1.0 - 1e-10))

        result = -math.log(u) / self.burst_rate

        return min(result, 1e10)

    def _generate_burst_size(self) -> int:
        mean = self.mean_burst_size
        u = self.rng.random()
        u = max(1e-10, min(u, 1.0 - 1e-10))

        size = max(1, int(-mean * math.log(u)))
        return size

    def next_arrival_time(self, current_time: float) -> float:
        if not self._burst_queue:
            burst_delay = self._next_burst_time

            burst_size = self._generate_burst_size()
            current_rate = self.get_request_rate(current_time)

            for _ in range(burst_size):
                if current_rate > 0:
                    u = self.rng.random()
                    u = max(1e-10, min(u, 1.0 - 1e-10))
                    inter_arrival = -math.log(u) / current_rate
                    self._burst_queue.append(inter_arrival)

            self._next_burst_time = self._generate_next_burst_time()
            return burst_delay

        return self._burst_queue.pop(0)

    def get_request_rate(self, current_time: float) -> float:
        return self._apply_spikes(self.base_rate, current_time, self.spikes)


class WaveTrafficGenerator(TrafficGenerator):
    DEFAULT_WAVE_PERIOD = 60.0
    DEFAULT_AMPLITUDE_FACTOR = 0.8
    DEFAULT_WAVE_TYPE = "sine"

    def __init__(
        self,
        base_rate: float,
        wave_period: float = DEFAULT_WAVE_PERIOD,
        amplitude_factor: float = DEFAULT_AMPLITUDE_FACTOR,
        wave_type: str = DEFAULT_WAVE_TYPE,
        spikes: Optional[List[TrafficSpike]] = None,
        random_seed: Optional[int] = None,
    ):
        super().__init__(base_rate, random_seed)
        self.wave_period = wave_period
        self.amplitude_factor = amplitude_factor
        self.wave_type = wave_type.lower()
        self.spikes = spikes or []
        self.spikes.sort(key=lambda s: s.start_time)

    def next_arrival_time(self, current_time: float) -> float:
        current_rate = self.get_request_rate(current_time)
        if current_rate <= 0:
            return float("inf")

        u = self.rng.random()
        return -math.log(u) / current_rate

    def get_request_rate(self, current_time: float) -> float:
        phase = 2 * math.pi * current_time / self.wave_period

        if self.wave_type == "square":
            wave_component = 1.0 if math.sin(phase) >= 0 else -1.0
        else:
            wave_component = math.sin(phase)

        rate = self.base_rate * (1 + self.amplitude_factor * wave_component)

        rate = self._apply_spikes(rate, current_time, self.spikes)

        return max(0, rate)


def create_traffic_generator(
    pattern: TrafficPattern,
    base_rate: float,
    spikes: Optional[List[TrafficSpike]] = None,
    **kwargs,
) -> TrafficGenerator:
    common_args = {
        "base_rate": base_rate,
        "spikes": spikes,
        "random_seed": kwargs.get("random_seed"),
    }

    if pattern == TrafficPattern.POISSON:
        return PoissonTrafficGenerator(**common_args)
    elif pattern == TrafficPattern.BURSTY:
        return BurstyTrafficGenerator(
            burst_size_mean=kwargs.get("burst_size_mean", 5.0),
            burst_interval=kwargs.get("burst_interval", 2.0),
            **common_args,
        )
    elif pattern == TrafficPattern.PERIODIC:
        return PeriodicTrafficGenerator(
            period=kwargs.get("period", 3600),
            amplitude_factor=kwargs.get("amplitude_factor", 0.5),
            **common_args,
        )
    elif pattern == TrafficPattern.CONSTANT:
        return ConstantTrafficGenerator(**common_args)
    elif pattern == TrafficPattern.EXPONENTIAL_BURST:
        return ExponentialBurstTrafficGenerator(
            burst_rate=kwargs.get("burst_rate", 0.5),
            mean_burst_size=kwargs.get("mean_burst_size", 8.0),
            **common_args,
        )
    elif pattern == TrafficPattern.WAVE:
        return WaveTrafficGenerator(
            wave_period=kwargs.get("wave_period", 60.0),
            amplitude_factor=kwargs.get("amplitude_factor", 0.8),
            wave_type=kwargs.get("wave_type", "sine"),
            **common_args,
        )
    else:
        raise ValueError(f"Unknown traffic pattern: {pattern}")
