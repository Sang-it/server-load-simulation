import simpy
import random
import math
from dataclasses import dataclass
from typing import List, Optional, Generator, Any

from .hardware import HardwareConfig, ProgrammingLanguageProfile
from .distributions import ProcessingTimeDistribution
from ..metrics.collector import MetricsCollector, RequestStatus


@dataclass
class Request:
    request_id: int
    arrival_time: float
    processing_time: float
    network_latency: float = 0.0


class Server:
    DEFAULT_NUM_WORKERS = 1
    DEFAULT_REQUEST_TIMEOUT_MS = 30000.0

    def __init__(
        self,
        server_id: int,
        env: Any,
        hardware: HardwareConfig,
        language: ProgrammingLanguageProfile,
        num_workers: int = DEFAULT_NUM_WORKERS,
        request_timeout: float = DEFAULT_REQUEST_TIMEOUT_MS,
        metrics_collector: Optional[MetricsCollector] = None,
        processing_time_stddev: float = 0.0,
        network_latency_mean: float = 0.0,
        network_latency_stddev: float = 0.0,
        processing_time_distribution: ProcessingTimeDistribution = ProcessingTimeDistribution.NORMAL,
        cpu_degradation_enabled: bool = True,
        random_seed: Optional[int] = None,
    ):
        if num_workers < 1:
            raise ValueError("num_workers must be >= 1")
        if request_timeout < 0:
            raise ValueError("request_timeout must be >= 0")
        if processing_time_stddev < 0:
            raise ValueError("processing_time_stddev must be >= 0")
        if network_latency_mean < 0:
            raise ValueError("network_latency_mean must be >= 0")
        if network_latency_stddev < 0:
            raise ValueError("network_latency_stddev must be >= 0")

        self.server_id = server_id
        self.env = env
        self.hardware = hardware
        self.language = language
        self.num_workers = num_workers
        self.request_timeout = request_timeout
        self.metrics_collector = metrics_collector
        self.processing_time_stddev = processing_time_stddev
        self.network_latency_mean = network_latency_mean
        self.network_latency_stddev = network_latency_stddev
        self.processing_time_distribution = processing_time_distribution
        self.cpu_degradation_enabled = cpu_degradation_enabled
        self.random_seed = random_seed

        self.request_store = simpy.Store(env)
        self.active_requests: dict = {}

        self.total_requests_processed = 0
        self.total_successful_requests = 0
        self.total_timed_out_requests = 0
        self.total_error_requests = 0
        self.response_times: List[float] = []
        self.completion_time: float = 0.0

        self.cpu_utilization_history: List[float] = []

        self.rng = random.Random(random_seed)

        for worker_id in range(num_workers):
            self.env.process(self._worker_process(worker_id))

    def _get_current_cpu_utilization(self) -> float:
        if self.num_workers == 0:
            return 0.0
        return min(1.0, len(self.active_requests) / self.num_workers)

    def _apply_cpu_degradation(self, processing_time: float) -> float:
        if not self.cpu_degradation_enabled:
            return processing_time

        cpu_util = self._get_current_cpu_utilization()

        if cpu_util <= 0.5:
            degradation_factor = 1.0
        else:
            excess_util = (cpu_util - 0.5) / 0.5
            degradation_factor = 1.0 + (math.exp(excess_util * 2) - 1) * 1.0

        return processing_time * degradation_factor

    def _sample_processing_time(self, base_time: float) -> float:
        if self.processing_time_stddev <= 0:
            return base_time

        if self.processing_time_distribution == ProcessingTimeDistribution.LOGNORMAL:
            mean = base_time
            sigma = self.processing_time_stddev
            mu = math.log(mean / math.sqrt(1 + (sigma / mean) ** 2))
            s = math.sqrt(math.log(1 + (sigma / mean) ** 2))
            return max(0.1, self.rng.lognormvariate(mu, s))
        else:
            return max(0.1, self.rng.gauss(base_time, self.processing_time_stddev))

    def _sample_network_latency(self) -> float:
        if self.network_latency_mean <= 0:
            return 0.0

        return max(
            0.0, self.rng.gauss(self.network_latency_mean, self.network_latency_stddev)
        )

    def _worker_process(self, _: int) -> Generator[Any, Any, Any]:
        while True:
            request = yield self.request_store.get()
            yield self.env.process(self._process_request(request))

    def _process_request(self, request: Request) -> Generator[Any, Any, Any]:
        start_time = self.env.now
        queue_wait_time = start_time - request.arrival_time

        base_processing_time = self.hardware.estimate_request_time(
            request.processing_time / self.language.efficiency_factor
        )

        distributed_processing_time = self._sample_processing_time(base_processing_time)

        processing_time = self._apply_cpu_degradation(distributed_processing_time)

        network_latency = self._sample_network_latency()

        self.active_requests[request.request_id] = (start_time, processing_time)

        remaining_timeout = self.request_timeout - queue_wait_time

        if remaining_timeout <= 0:
            self.active_requests.pop(request.request_id, None)
            self.total_timed_out_requests += 1
            self.total_requests_processed += 1

            if self.metrics_collector:
                self.metrics_collector.record_request(
                    arrival_time=request.arrival_time,
                    start_time=start_time,
                    completion_time=self.env.now,
                    status=RequestStatus.TIMEOUT,
                    server_id=self.server_id,
                )
            return

        try:
            timeout_event = self.env.timeout(remaining_timeout)
            processing_event = self.env.timeout(processing_time + network_latency)

            result = yield processing_event | timeout_event

            completion_time = self.env.now
            response_time = completion_time - start_time

            if timeout_event in result:
                status = RequestStatus.TIMEOUT
                self.total_timed_out_requests += 1
            else:
                status = RequestStatus.SUCCESS
                self.total_successful_requests += 1

        except Exception:
            completion_time = self.env.now
            response_time = completion_time - start_time
            status = RequestStatus.ERROR
            self.total_error_requests += 1

        self.active_requests.pop(request.request_id, None)
        self.total_requests_processed += 1
        self.response_times.append(response_time)
        self.cpu_utilization_history.append(self._get_current_cpu_utilization())

        if self.metrics_collector:
            self.metrics_collector.record_request(
                arrival_time=request.arrival_time,
                start_time=start_time,
                completion_time=completion_time,
                status=status,
                server_id=self.server_id,
            )

    def submit_request(self, request: Request) -> bool:
        self.request_store.put(request)
        return True

    def is_available(self) -> bool:
        return True

    def get_queue_length(self) -> int:
        return len(self.request_store.items) + len(self.active_requests)

    def get_average_response_time(self) -> float:
        if not self.response_times:
            return 0.0

        return sum(self.response_times) / len(self.response_times)

    def get_utilization(self) -> float:
        active_count = len(self.active_requests)
        return min(1.0, active_count / self.num_workers)

    def get_statistics(self) -> dict:
        return {
            "server_id": self.server_id,
            "total_requests": self.total_requests_processed,
            "successful_requests": self.total_successful_requests,
            "timed_out_requests": self.total_timed_out_requests,
            "avg_response_time": self.get_average_response_time(),
            "current_utilization": self.get_utilization(),
            "queue_length": self.get_queue_length(),
        }
