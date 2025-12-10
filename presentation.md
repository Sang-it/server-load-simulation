---
title: Server Load Dynamics Simulator
sub_title: Discrete-Event Simulation for Capacity Planning
author: Sangit Manandhar
---

<!-- alignment: center -->

Agenda
===

- **Problem**: Why simulate server load?
- **Approach**: SimPy discrete-event simulation
- **Alternatives**: Other approaches considered
- **Parameters**: Inputs and tracked variables
- **Live Demo**: Simulation in action
- **Results**: Analysis and interpretation
- **Limitations**: Model constraints and challenges
- **Future Work**: What's next?

<!-- end_slide -->

<!-- alignment: center -->

Problem: Why Simulation?
===

## The Challenge

- **Capacity Planning**: How many servers do we need?
- **Performance Prediction**: Will our system handle peak traffic?
- **Cost Optimization**: Avoid over-provisioning expensive hardware

## Why Simulation & Modeling?

| Real Load Testing | Simulation |
|-------------------|------------|
| Expensive infrastructure | Zero infrastructure cost |
| Risk of downtime | Safe experimentation |
| Limited scenarios | Unlimited "what-if" scenarios |
| Time-consuming | Fast iteration |

## Use Cases

- Compare **load balancing strategies** before deployment
- Test **traffic spike** handling without real users
- Evaluate **hardware upgrades** ROI
- Benchmark **programming language** efficiency

<!-- end_slide -->

<!-- alignment: center -->

Approach: SimPy Framework
===

## Core Technology

- **SimPy**: Python discrete-event simulation library
- **Event-driven**: Processes requests as discrete events
- **Realistic modeling**: Queues, timeouts, CPU degradation

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Traffic   │ --> │    Load      │ --> │   Server    │
│  Generator  │     │  Balancer    │     │   Pool      │
└─────────────┘     └──────────────┘     └─────────────┘
                                               │
                                               v
                                    ┌─────────────────────┐
                                    │  Metrics Collector  │
                                    └─────────────────────┘
```

## Key Features

- **6 Traffic Patterns**: Poisson, Bursty, Periodic, Wave, etc.
- **6 Load Balancing**: Round Robin, Least Connections, CPU-Aware
- **4 Hardware Profiles**: Entry-level to Enterprise
- **6 Language Profiles**: Python, Node.js, Java, Go, Rust, .NET

<!-- end_slide -->

<!-- alignment: center -->

Alternatives Considered
===

## Option 1: Real Load Testing (Locust, Hyperfine)

- **Pro**: Real-world accuracy
- **Con**: Requires actual infrastructure, expensive

## Option 2: Network Simulators (ns-3, OMNeT++)

- **Pro**: Detailed network modeling
- **Con**: Overkill for application-level simulation

## Why SimPy?

- **Open source** and free
- **Python ecosystem**: Easy integration with data analysis tools
- **Process-based**: Natural way to model server workers
- **Mature**: Well-documented, active community
- **Lightweight**: No complex setup required

<!-- end_slide -->

<!-- alignment: center -->
Parameters & Variables
===

## Input Parameters (Independent Variables)

| Category | Parameters |
|----------|------------|
| **Infrastructure** | num_servers, hardware_profile, language |
| **Traffic** | base_request_rate, traffic_pattern, spikes |
| **Processing** | request_processing_time, timeout, distribution |
| **Balancing** | strategy (Round Robin, Least Connections, etc.) |
| **Advanced** | CPU degradation, network latency, random seed |

## Dependent Variables (Outcomes Tracked)

| Metric | Description |
|--------|-------------|
| **Response Time** | Avg, p50, p95, p99, p99.9 percentiles |
| **Throughput** | Successful requests per second |
| **Success Rate** | % requests completed vs timed out |
| **Queue Time** | Time waiting before processing |
| **Utilization** | Server CPU usage over time |

## Iterations

- Configurable simulation duration (seconds)
- Multiple scenarios run sequentially for comparison
- Random seed for reproducibility

<!-- end_slide -->

<!-- alignment: center -->
Live Demo
===

## Demo Scenarios

We'll compare **3 programming languages** under identical conditions:

| Parameter | Value |
|-----------|-------|
| Servers | 2 |
| Hardware | HIGH_PERFORMANCE |
| Traffic | POISSON (10 req/s) |
| Duration | 60 seconds |
| Balancing | LEAST_CONNECTIONS |

## Languages Tested

1. **Python** (efficiency: 1.8x)
2. **Node.js** (efficiency: 3.0x)
3. **Go** (efficiency: 10.8x)

<!-- end_slide -->

<!-- alignment: center -->
## Running the Simulation

```bash +exec
python main.py --config config.yaml --time-scale=0.01 --short-output
```

```bash +exec
python _visualize.py --short-output
```
<!-- end_slide -->

Results Analysis
===

<!-- column_layout: [3, 7] -->

<!-- column: 0 -->
## Key Metrics to Compare

### Response Time
- Lower is better
- Watch p99 for worst-case latency

### Throughput
- Higher is better
- Measures system capacity

### Success Rate
- Target: 100%
- Timeouts indicate capacity issues

<!-- column: 1 -->
![](visualizations/06_dashboard.png)

<!-- reset_layout -->

<!-- end_slide -->

<!-- alignment: center -->
Limitations & Challenges
===

## Model Limitations

1. **Simplified CPU Model**
   - Real CPUs have complex caching, context switching
   - Our model uses exponential degradation approximation

2. **No Memory Modeling**
   - Memory pressure and garbage collection not simulated
   - Could affect language comparison accuracy

3. **Network Simplification**
   - Latency modeled as normal distribution
   - Real networks have packet loss, retries, congestion

4. **Single Machine Focus**
   - No distributed system effects
   - No inter-server communication overhead

## Stumbling Blocks

- **Calibrating efficiency factors**: Language benchmarks vary widely
- **Choosing distributions**: Lognormal vs Normal for processing time
- **Balancing realism vs complexity**: More detail = slower simulation
- **Validation**: No real-world data to compare against

<!-- end_slide -->

<!-- alignment: center -->
Surprises & Future Work
===

## Surprising Findings

- **Load balancer choice matters more than expected**
  - CPU-Aware significantly outperforms Round Robin under high load

- **Traffic pattern impact**
  - Bursty traffic causes 3-5x worse p99 latency vs Poisson

- **Diminishing returns on hardware**
  - Enterprise hardware doesn't always justify 4x cost

## Future Work

| Enhancement | Benefit |
|-------------|---------|
| **Database/cache tier** | More realistic architectures |
| **Real-world validation** | Calibrate against actual benchmarks |
| **Cost modeling** | $/request optimization |
| **Geographic distribution** | Multi-region simulation |
| **Failure injection** | Chaos engineering scenarios |

## Questions?

Thank you for your attention!

<!-- end_slide -->

<!-- jump_to_middle -->

The end
---
