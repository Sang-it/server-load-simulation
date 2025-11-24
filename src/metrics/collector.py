import statistics
from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Optional, Deque, Sequence


class RequestStatus(Enum):
    SUCCESS = "success"
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass
class RequestMetric:
    request_id: int
    arrival_time: float
    start_time: float
    completion_time: float
    status: RequestStatus
    response_time: float
    queue_wait_time: float
    server_id: int

    def __post_init__(self):
        if self.response_time < 0:
            raise ValueError(f"Invalid response_time: {self.response_time}")
        if self.queue_wait_time < 0:
            raise ValueError(f"Invalid queue_wait_time: {self.queue_wait_time}")


@dataclass
class PercentileStats:
    p50: float
    p95: float
    p99: float
    p999: float


@dataclass
class AggregatedMetrics:
    total_requests: int = 0
    successful_requests: int = 0
    timed_out_requests: int = 0
    error_requests: int = 0

    avg_response_time: float = 0.0
    min_response_time: float = 0.0
    max_response_time: float = 0.0
    response_time_stddev: float = 0.0
    response_time_percentiles: Optional[PercentileStats] = None

    avg_queue_time: float = 0.0
    max_queue_time: float = 0.0

    successful_throughput: float = 0.0
    total_throughput: float = 0.0

    avg_server_utilization: float = 0.0
    max_server_utilization: float = 0.0

    simulation_duration: float = 0.0

    def to_dict(self) -> Dict:
        percentiles_dict = None
        if self.response_time_percentiles:
            percentiles_dict = {
                "p50": self.response_time_percentiles.p50,
                "p95": self.response_time_percentiles.p95,
                "p99": self.response_time_percentiles.p99,
                "p999": self.response_time_percentiles.p999,
            }

        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "timed_out_requests": self.timed_out_requests,
            "error_requests": self.error_requests,
            "avg_response_time_ms": self.avg_response_time,
            "min_response_time_ms": self.min_response_time,
            "max_response_time_ms": self.max_response_time,
            "response_time_stddev_ms": self.response_time_stddev,
            "response_time_percentiles_ms": percentiles_dict,
            "avg_queue_time_ms": self.avg_queue_time,
            "max_queue_time_ms": self.max_queue_time,
            "successful_throughput_rps": self.successful_throughput,
            "total_throughput_rps": self.total_throughput,
            "avg_server_utilization": self.avg_server_utilization,
            "max_server_utilization": self.max_server_utilization,
            "simulation_duration_s": self.simulation_duration,
            "success_rate": (
                self.successful_requests / self.total_requests
                if self.total_requests > 0
                else 0.0
            ),
        }


class MetricsCollector:
    MAX_METRICS = 1000000

    P50_PERCENTILE = 0.50
    P95_PERCENTILE = 0.95
    P99_PERCENTILE = 0.99
    P999_PERCENTILE = 0.999

    def __init__(self, max_metrics: int = MAX_METRICS):
        if max_metrics <= 0:
            raise ValueError(f"max_metrics must be positive, got {max_metrics}")

        self.metrics: Deque[RequestMetric] = deque(maxlen=max_metrics)
        self.server_utilization_history: Dict[int, List[float]] = {}
        self.request_counter = 0
        self.max_metrics = max_metrics

    def record_request(
        self,
        arrival_time: float,
        start_time: float,
        completion_time: float,
        status: RequestStatus,
        server_id: int,
    ) -> int:
        self.request_counter += 1
        request_id = self.request_counter

        queue_wait_time = start_time - arrival_time
        response_time = completion_time - arrival_time

        metric = RequestMetric(
            request_id=request_id,
            arrival_time=arrival_time,
            start_time=start_time,
            completion_time=completion_time,
            status=status,
            response_time=response_time,
            queue_wait_time=queue_wait_time,
            server_id=server_id,
        )

        self.metrics.append(metric)
        return request_id

    def record_server_utilization(self, server_id: int, utilization: float) -> None:
        if server_id not in self.server_utilization_history:
            self.server_utilization_history[server_id] = []

        self.server_utilization_history[server_id].append(utilization)

    def aggregate(self, simulation_duration: float) -> AggregatedMetrics:
        return self._calculate_metrics(self.metrics, simulation_duration)

    def _calculate_metrics(
        self, metrics_to_use: Sequence[RequestMetric], duration: float
    ) -> AggregatedMetrics:
        if not metrics_to_use:
            return AggregatedMetrics(simulation_duration=duration)

        result = AggregatedMetrics(
            total_requests=len(metrics_to_use),
            simulation_duration=duration,
        )

        for metric in metrics_to_use:
            if metric.status == RequestStatus.SUCCESS:
                result.successful_requests += 1
            elif metric.status == RequestStatus.TIMEOUT:
                result.timed_out_requests += 1
            elif metric.status == RequestStatus.ERROR:
                result.error_requests += 1

        response_times = [m.response_time for m in metrics_to_use]
        if response_times:
            result.avg_response_time = statistics.mean(response_times)
            result.min_response_time = min(response_times)
            result.max_response_time = max(response_times)

            if len(response_times) > 1:
                result.response_time_stddev = statistics.stdev(response_times)

            sorted_response_times = sorted(response_times)
            result.response_time_percentiles = PercentileStats(
                p50=self._percentile(sorted_response_times, self.P50_PERCENTILE),
                p95=self._percentile(sorted_response_times, self.P95_PERCENTILE),
                p99=self._percentile(sorted_response_times, self.P99_PERCENTILE),
                p999=self._percentile(sorted_response_times, self.P999_PERCENTILE),
            )

        queue_times = [m.queue_wait_time for m in metrics_to_use]
        if queue_times:
            result.avg_queue_time = statistics.mean(queue_times)
            result.max_queue_time = max(queue_times)

        if duration > 0:
            result.successful_throughput = result.successful_requests / duration
            result.total_throughput = result.total_requests / duration

        all_utilizations = []
        for utilizations in self.server_utilization_history.values():
            all_utilizations.extend(utilizations)

        if all_utilizations:
            result.avg_server_utilization = statistics.mean(all_utilizations)
            result.max_server_utilization = max(all_utilizations)

        return result

    @staticmethod
    def _percentile(sorted_data: List[float], percentile: float) -> float:
        if not sorted_data:
            return 0.0

        if len(sorted_data) == 1:
            return float(sorted_data[0])

        if len(sorted_data) == 2:
            if percentile < 0.5:
                return float(sorted_data[0])
            else:
                return float(sorted_data[1])

        index = percentile * (len(sorted_data) - 1)
        lower_index = int(index)
        upper_index = lower_index + 1

        if upper_index >= len(sorted_data):
            return float(sorted_data[lower_index])

        weight = index - lower_index
        return (
            sorted_data[lower_index] * (1 - weight) + sorted_data[upper_index] * weight
        )

    def get_per_server_stats(self) -> Dict[int, Dict]:
        server_stats = {}

        for metric in self.metrics:
            server_id = metric.server_id
            if server_id not in server_stats:
                server_stats[server_id] = {
                    "total_requests": 0,
                    "successful_requests": 0,
                    "failed_requests": 0,
                    "response_times": [],
                }

            server_stats[server_id]["total_requests"] += 1

            if metric.status == RequestStatus.SUCCESS:
                server_stats[server_id]["successful_requests"] += 1
            else:
                server_stats[server_id]["failed_requests"] += 1

            server_stats[server_id]["response_times"].append(metric.response_time)

        for server_id, stats in server_stats.items():
            response_times = stats.pop("response_times")
            if response_times:
                stats["avg_response_time"] = statistics.mean(response_times)
                stats["max_response_time"] = max(response_times)
                stats["min_response_time"] = min(response_times)

        return server_stats

    def snapshot_at_time(
        self, current_time: float, duration: float = 0.0, lookahead: float = 2.0
    ) -> AggregatedMetrics:
        completed_metrics = [
            m for m in self.metrics if m.completion_time <= current_time + lookahead
        ]

        calc_duration = duration or current_time
        return self._calculate_metrics(completed_metrics, calc_duration)

    def clear(self) -> None:
        self.metrics.clear()
        self.server_utilization_history.clear()
        self.request_counter = 0
