from dataclasses import dataclass
from enum import Enum
from typing import ClassVar


class HardwareProfile(Enum):
    ENTRY_LEVEL = "entry_level"
    STANDARD = "standard"
    HIGH_PERFORMANCE = "high_performance"
    ENTERPRISE = "enterprise"


@dataclass
class HardwareConfig:
    cpu_speed: float
    memory_capacity: int
    io_latency: float
    processing_power: float = 1.0
    num_cores: int = 8

    @classmethod
    def from_profile(cls, profile: HardwareProfile) -> "HardwareConfig":
        configs = {
            HardwareProfile.ENTRY_LEVEL: cls(
                cpu_speed=2.0,
                memory_capacity=4,
                io_latency=2.0,
                processing_power=1.5,
                num_cores=4,
            ),
            HardwareProfile.STANDARD: cls(
                cpu_speed=2.4,
                memory_capacity=8,
                io_latency=1.0,
                processing_power=5.0,
                num_cores=8,
            ),
            HardwareProfile.HIGH_PERFORMANCE: cls(
                cpu_speed=3.5,
                memory_capacity=16,
                io_latency=0.4,
                processing_power=12.5,
                num_cores=16,
            ),
            HardwareProfile.ENTERPRISE: cls(
                cpu_speed=4.0,
                memory_capacity=32,
                io_latency=0.2,
                processing_power=30.0,
                num_cores=32,
            ),
        }
        return configs[profile]

    @classmethod
    def from_dict(cls, config_dict: dict) -> "HardwareConfig":
        return cls(
            cpu_speed=config_dict.get("cpu_speed", 2.4),
            memory_capacity=config_dict.get("memory_capacity", 8),
            io_latency=config_dict.get("io_latency", 5.0),
            processing_power=config_dict.get("processing_power", 1.0),
            num_cores=config_dict.get("num_cores", 8),
        )

    def estimate_request_time(self, base_time: float) -> float:
        return (base_time / self.processing_power) + (self.io_latency * 0.25)


@dataclass
class ProgrammingLanguageProfile:
    name: str
    efficiency_factor: float
    memory_overhead: float
    startup_time: float

    PYTHON: ClassVar["ProgrammingLanguageProfile"]
    NODEJS: ClassVar["ProgrammingLanguageProfile"]
    JAVA: ClassVar["ProgrammingLanguageProfile"]
    GO: ClassVar["ProgrammingLanguageProfile"]
    RUST: ClassVar["ProgrammingLanguageProfile"]
    DOTNET: ClassVar["ProgrammingLanguageProfile"]


ProgrammingLanguageProfile.PYTHON = ProgrammingLanguageProfile(
    name="Python",
    efficiency_factor=2.0,
    memory_overhead=150,
    startup_time=450,
)

ProgrammingLanguageProfile.NODEJS = ProgrammingLanguageProfile(
    name="Node.js",
    efficiency_factor=4.0,
    memory_overhead=120,
    startup_time=300,
)

ProgrammingLanguageProfile.JAVA = ProgrammingLanguageProfile(
    name="Java",
    efficiency_factor=8.0,
    memory_overhead=220,
    startup_time=800,
)

ProgrammingLanguageProfile.GO = ProgrammingLanguageProfile(
    name="Go",
    efficiency_factor=15.0,
    memory_overhead=70,
    startup_time=150,
)

ProgrammingLanguageProfile.RUST = ProgrammingLanguageProfile(
    name="Rust",
    efficiency_factor=22.0,
    memory_overhead=50,
    startup_time=80,
)

ProgrammingLanguageProfile.DOTNET = ProgrammingLanguageProfile(
    name=".NET",
    efficiency_factor=7.0,
    memory_overhead=180,
    startup_time=600,
)
