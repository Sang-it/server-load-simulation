# Server Load Dynamics Simulator

A comprehensive Python-based discrete-event simulation framework for modeling and analyzing server behavior under various traffic patterns, hardware configurations, and load balancing strategies.

## Overview

This simulator enables you to:
- Model realistic server behavior with different hardware profiles and programming languages
- Test various load balancing strategies (Round Robin, Least Connections, CPU-Aware, etc.)
- Simulate diverse traffic patterns (Poisson, Bursty, Periodic, Constant, Wave)
- Analyze performance metrics including response times, throughput, and success rates
- Compare scenarios to optimize infrastructure decisions

## Features

### Traffic Simulation
- **Traffic Patterns**:
  - Poisson (random arrival)
  - Bursty (requests in bursts)
  - Periodic (cyclical patterns)
  - Constant (steady rate)
  - Exponential Burst
  - Wave (sinusoidal patterns)
- **Traffic Spikes**: Define sudden traffic surges with configurable start time, duration, and intensity

### Hardware Profiles
- **Entry Level**: 2.0 GHz, 4 GB RAM, 4 cores
- **Standard**: 2.4 GHz, 8 GB RAM, 8 cores
- **High Performance**: 3.5 GHz, 16 GB RAM, 16 cores
- **Enterprise**: 4.0 GHz, 32 GB RAM, 32 cores
- **Custom**: Define your own hardware specifications

### Programming Language Profiles
Simulate performance characteristics of different runtime environments:
- **Python**: efficiency factor 1.8x
- **Node.js**: efficiency factor 3.0x
- **Java**: efficiency factor 4.8x
- **Go**: efficiency factor 10.8x
- **Rust**: efficiency factor 21.0x
- **.NET**: efficiency factor 6.0x

### Load Balancing Strategies
- **Round Robin**: Distributes requests evenly across servers
- **Least Connections**: Routes to server with fewest active connections
- **Least Response Time**: Routes to server with best response time
- **Weighted Round Robin**: Distributes based on server weights
- **Random**: Randomly selects servers
- **CPU-Aware**: Routes based on CPU utilization and queue length

### Advanced Simulation Features
- **CPU Degradation**: Models performance degradation under high CPU load
- **Network Latency**: Simulates network delays with configurable mean and standard deviation
- **Processing Time Distributions**: Normal or Log-normal distributions
- **Request Timeouts**: Configurable timeout handling
- **Time Scaling**: Control simulation speed (real-time, faster, or slower)

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Dependencies
```bash
pip install simpy pyyaml matplotlib numpy
```

### Setup
```bash
git clone <repository-url>
cd server-load-simulation
```

## Usage

### Basic Usage

Run a simulation using a configuration file:
```bash
python main.py --config config.yaml
```

### Command Line Options

```bash
python main.py --config <config_file> [OPTIONS]

Options:
  --config FILE             Path to configuration file (YAML or JSON) [required]
  --scenario NAME           Run a specific scenario by name
  --list                    List all available scenarios
  --validate FILE           Validate configuration file without running
  --time-scale SCALE        Wall-clock seconds per simulation second (e.g., 1.0=real-time)
  --export-format FORMAT    Export format: json, csv, or both (default: json)
  --comparison              Generate comparison CSV for multiple scenarios
  -v, --verbose             Print verbose output
```

### Configuration File Format

Create a YAML or JSON configuration file:

```yaml
scenarios:
  - name: baseline_scenario
    description: Basic single-server test
    duration: 300.0                    # Simulation duration in seconds
    num_servers: 1                     # Number of servers
    hardware: STANDARD                 # Hardware profile
    language: PYTHON                   # Programming language
    base_request_rate: 10.0           # Base requests per second
    traffic_pattern: POISSON          # Traffic pattern
    balancing_strategy: ROUND_ROBIN   # Load balancing strategy
    request_processing_time: 100.0    # Base processing time (ms)
    request_timeout: 30000.0          # Request timeout (ms)
    random_seed: 42                   # Random seed for reproducibility

    # Optional advanced settings
    processing_time_stddev: 30.0      # Standard deviation for processing time
    processing_time_distribution: LOGNORMAL  # NORMAL or LOGNORMAL
    network_latency_mean: 20.0        # Network latency mean (ms)
    network_latency_stddev: 5.0       # Network latency std dev (ms)
    cpu_degradation_enabled: true     # Enable CPU degradation modeling

    # Traffic spikes (optional)
    spikes:
      - start_time: 100.0
        duration: 60.0
        intensity_multiplier: 5.0
```

### Example: Running Multiple Scenarios

```bash
# Run all scenarios in config file
python main.py --config config.yaml

# Run a specific scenario
python main.py --config config.yaml --scenario baseline_scenario

# List available scenarios
python main.py --config config.yaml --list

# Validate configuration
python main.py --validate config.yaml

# Export results as CSV with comparison
python main.py --config config.yaml --export-format csv --comparison
```

## Project Structure

```
server-load-simulation/
├── main.py                    # Main entry point
├── config.yaml               # Example configuration
├── _visualize.py             # Results visualization tool
├── src/
│   ├── simulation/
│   │   ├── engine.py         # Core simulation engine
│   │   └── __init__.py
│   ├── models/
│   │   ├── server.py         # Server model
│   │   ├── hardware.py       # Hardware configurations
│   │   ├── distributions.py  # Statistical distributions
│   │   └── __init__.py
│   ├── traffic/
│   │   ├── generators.py     # Traffic pattern generators
│   │   └── __init__.py
│   ├── load_balancing/
│   │   ├── strategies.py     # Load balancing algorithms
│   │   └── __init__.py
│   ├── metrics/
│   │   ├── collector.py      # Metrics collection
│   │   └── __init__.py
│   └── utils/
│       ├── config_loader.py  # Configuration parsing
│       ├── config.py         # Scenario builder
│       ├── exporters.py      # Result exporters
│       ├── comparison.py     # Scenario comparison tools
│       └── __init__.py
└── results/                  # Output directory
```

## Output and Results

### Metrics Collected

The simulator tracks comprehensive metrics:
- **Request Metrics**:
  - Total, successful, timed-out, and error requests
  - Average, min, max response times
  - Response time percentiles (P50, P95, P99, P99.9)
  - Queue wait times
- **Throughput Metrics**:
  - Successful throughput (requests/second)
  - Total throughput
- **Server Metrics**:
  - CPU utilization (average and max)
  - Per-server request distribution
  - Per-server response times

### Result Files

Results are saved to the `results/` directory:
- `<scenario_name>.json`: Complete results in JSON format
- `<scenario_name>_metrics.csv`: Summary metrics in CSV
- `comparison.csv`: Comparison across multiple scenarios (with --comparison flag)

### Example Output

```
================================================================================
Running scenario: baseline_scenario
  Duration: 300s (simulation time)
  Time Scale: 1.0x (300.0s wall-clock)
================================================================================

[████████████████████████████████████████] 100.0% (300.0s/300.0s)

Results for baseline_scenario:
  - Servers: 1
  - Duration: 300s
  - Total Requests: 3001
  - Avg Response Time: 125.45 ms
  - Throughput: 9.95 RPS
  - Success Rate: 100.0%
  - Results saved to: results/baseline_scenario.json
```

## Visualization

Generate visualizations from simulation results:

```bash
python _visualize.py --results-dir results --output-dir visualizations
```

Generates:
- Response time comparisons
- Throughput charts
- Success rate analysis
- Queue time visualization
- Per-server load distribution
- Comprehensive dashboard

## Advanced Usage

### Custom Hardware Configuration

```yaml
scenarios:
  - name: custom_hardware
    hardware:
      cpu_speed: 3.2
      memory_capacity: 16
      io_latency: 0.5
      processing_power: 8.0
      num_cores: 12
```

### Traffic Pattern-Specific Settings

**Bursty Traffic:**
```yaml
traffic_pattern: BURSTY
traffic_kwargs:
  burst_size_mean: 8.0
  burst_interval: 3.0
```

**Periodic Traffic:**
```yaml
traffic_pattern: PERIODIC
traffic_kwargs:
  period: 3600          # Period in seconds
  amplitude_factor: 0.5 # Amplitude of variation (0-1)
```

**Wave Traffic:**
```yaml
traffic_pattern: WAVE
traffic_kwargs:
  wave_period: 60.0
  amplitude_factor: 0.8
  wave_type: sine       # 'sine' or 'square'
```

## Use Cases

### Performance Testing
- Test infrastructure capacity under various load conditions
- Identify bottlenecks and performance limits
- Validate SLA requirements

### Infrastructure Planning
- Compare hardware configurations
- Determine optimal server count
- Evaluate cost vs. performance trade-offs

### Load Balancing Strategy Selection
- Compare different load balancing algorithms
- Identify best strategy for your traffic patterns
- Optimize resource utilization

### Language/Runtime Comparison
- Compare performance characteristics of different runtimes
- Make informed technology stack decisions
- Understand efficiency trade-offs

## Architecture

### Core Components

**Simulation Engine** (`src/simulation/engine.py`):
- Discrete-event simulation using SimPy
- Manages simulation time and event scheduling
- Coordinates servers, load balancers, and traffic generators

**Server Model** (`src/models/server.py`):
- Worker-based request processing
- Queue management
- CPU degradation modeling
- Timeout handling

**Traffic Generators** (`src/traffic/generators.py`):
- Pluggable traffic pattern implementations
- Spike injection
- Statistical arrival time generation

**Load Balancers** (`src/load_balancing/strategies.py`):
- Multiple strategy implementations
- Server selection algorithms
- Request routing

**Metrics Collector** (`src/metrics/collector.py`):
- Real-time metrics collection
- Statistical aggregation
- Percentile calculations

## Configuration Validation

Validate your configuration before running:

```bash
python main.py --validate config.yaml
```

The validator checks:
- Required fields
- Value ranges and types
- Enum value validity
- Spike configuration
- Provides suggestions for typos

## Performance Considerations

- **Simulation Speed**: Use `--time-scale` to control wall-clock execution time
- **Memory Usage**: Large simulations (>1M requests) may require more memory
- **Determinism**: Use `random_seed` for reproducible results

## Limitations

- Assumes homogeneous servers within a scenario
- Network topology is abstracted
- Does not model disk I/O in detail
- Assumes infinite network bandwidth within the load balancer

## References

- SimPy Documentation: https://simpy.readthedocs.io/
- Queueing Theory fundamentals
- Load Balancing algorithms
