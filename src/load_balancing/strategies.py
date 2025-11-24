import random
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Optional
from ..models.server import Server


class LoadBalancingStrategy(Enum):
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_RESPONSE_TIME = "least_response_time"
    RANDOM = "random"
    CPU_AWARE = "cpu_aware"


class BalancerBase(ABC):
    def __init__(self, servers: List[Server]) -> None:
        self.servers: List[Server] = servers
        self.request_count: int = 0

    @abstractmethod
    def select_server(self) -> Optional[Server]:
        pass

    def record_request(self) -> None:
        self.request_count += 1


class RoundRobinBalancer(BalancerBase):
    def __init__(self, servers: List[Server]):
        super().__init__(servers)
        self.current_index = 0

    def select_server(self, **_) -> Optional[Server]:
        if not self.servers:
            return None

        attempts = 0
        max_attempts = len(self.servers)

        while attempts < max_attempts:
            server = self.servers[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.servers)

            if server.is_available():
                return server

            attempts += 1

        return None


class LeastConnectionsBalancer(BalancerBase):
    def select_server(self, **_) -> Optional[Server]:
        if not self.servers:
            return None

        available_servers = [s for s in self.servers if s.is_available()]

        if not available_servers:
            return None

        return min(available_servers, key=lambda s: s.get_queue_length())


class WeightedRoundRobinBalancer(BalancerBase):
    def __init__(
        self, servers: List[Server], weights: Optional[Dict[int, float]] = None
    ):
        super().__init__(servers)
        self.weights = weights or {i: 1.0 for i in range(len(servers))}
        self.current_index = 0

    def select_server(self) -> Optional[Server]:
        if not self.servers:
            return None

        available_servers = [s for s in self.servers if s.is_available()]

        if not available_servers:
            return None

        weighted_servers = []
        for i, server in enumerate(self.servers):
            if server.is_available():
                weight = self.weights.get(i, 1.0)
                count = max(1, int(round(weight * 10)))
                weighted_servers.extend([server] * count)

        return random.choice(weighted_servers) if weighted_servers else None


class LeastResponseTimeBalancer(BalancerBase):
    def select_server(self) -> Optional[Server]:
        if not self.servers:
            return None

        available_servers = [s for s in self.servers if s.is_available()]

        if not available_servers:
            return None

        def score_server(server: Server) -> float:
            avg_response = server.get_average_response_time()
            queue_length = server.get_queue_length()

            if avg_response == 0:
                return float(queue_length)

            return queue_length * avg_response

        return min(available_servers, key=score_server)


class RandomBalancer(BalancerBase):
    def select_server(self) -> Optional[Server]:
        if not self.servers:
            return None

        available_servers = [s for s in self.servers if s.is_available()]

        if not available_servers:
            return None

        return random.choice(available_servers)


class CPUAwareBalancer(BalancerBase):
    def select_server(self) -> Optional[Server]:
        if not self.servers:
            return None

        available_servers = [s for s in self.servers if s.is_available()]

        if not available_servers:
            return None

        def score_server(server: Server) -> float:
            queue_length = server.get_queue_length()
            avg_response = server.get_average_response_time() / 100.0

            return queue_length + avg_response

        return min(available_servers, key=score_server)


class BalancerFactory:
    @staticmethod
    def create_balancer(
        strategy: LoadBalancingStrategy, servers: List[Server], **kwargs
    ) -> BalancerBase:
        if strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return RoundRobinBalancer(servers)
        elif strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return LeastConnectionsBalancer(servers)
        elif strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
            weights = kwargs.get("weights")
            return WeightedRoundRobinBalancer(servers, weights)
        elif strategy == LoadBalancingStrategy.LEAST_RESPONSE_TIME:
            return LeastResponseTimeBalancer(servers)
        elif strategy == LoadBalancingStrategy.RANDOM:
            return RandomBalancer(servers)
        elif strategy == LoadBalancingStrategy.CPU_AWARE:
            return CPUAwareBalancer(servers)
        else:
            raise ValueError(f"Unknown load balancing strategy: {strategy}")
