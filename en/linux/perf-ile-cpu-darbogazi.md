---
title: Finding CPU bottlenecks with perf on Linux
permalink: /en/linux/perf-ile-cpu-darbogazi/
status: duzenlendi
reviewed: 2026-11-03
scope: CPU sampling, call graphs and Brendan Gregg Flame Graph analysis with perf
  on Linux 6.x.
lang: en
translation_key: guide-linux-perf-ile-cpu-darbogazi
translation_of: /linux/perf-ile-cpu-darbogazi/
translated: '2026-11-03'
---

# Finding CPU bottlenecks with perf on Linux

The Linux `perf` tool uses hardware Performance Monitoring Unit (PMU) counters and kernel tracepoints to investigate which functions consume CPU time.

A properly configured profile can reveal expensive loops, excessive memory accesses, L1/L3 cache misses and call-stack costs in an interactive **flame graph**.

## 1. Kernel permissions and system settings

For security, Linux restricts access to performance counters for users without `root` privileges by default.

### `kernel.perf_event_paranoid`

This setting controls the permitted profiling level:

- `2`: userspace profiling only; kernel profiling is restricted, as on many distributions by default.
- `1`: permits kernel and userspace CPU profiling.
- `-1`: removes restrictions, including access to raw tracepoints.

Temporarily grant access in a development environment:

```bash
sudo sysctl -w kernel.perf_event_paranoid=1
```

To persist the setting, put it in `/etc/sysctl.d/99-perf.conf`:

```bash
echo "kernel.perf_event_paranoid = 1" | sudo tee /etc/sysctl.d/99-perf.conf
```

### `kernel.kptr_restrict`

If kernel symbols appear masked as `[k] 0x00000000` in `perf report`, adjust kernel-address masking:

```bash
sudo sysctl -w kernel.kptr_restrict=0
```

## 2. Build flags: why retain frame pointers?

Profiling unoptimised code (`-O0`) can hide the bottlenecks present in the optimised application because it behaves very differently.

Profile a **RelWithDebInfo** build with optimisation (`-O2` or `-O3`) and debugging symbols (`-g`). Optimised builds may omit the frame pointer (`%rbp`) through `-fomit-frame-pointer`, preventing reliable frame-pointer stack unwinding.

Build with **`-fno-omit-frame-pointer`**:

```bash
g++ -O2 -g -fno-omit-frame-pointer -o hesaplayici main.cpp
```

## 3. Recording a profile with perf record

Run the application with `perf record` to collect CPU samples:

```bash
perf record -F 99 -g -- ./hesaplayici
```

### Options

- `-F 99`: sample at 99 Hz. Choosing 99 rather than 100 helps avoid aliasing with periodic kernel timer activity at frequencies such as 100, 250 or 1000 Hz.
- `-g`: record call graphs.

### Call-graph methods: fp vs dwarf vs lbr

| Method | Option | Overhead | Accuracy and limitations |
| :--- | :--- | :--- | :--- |
| **Frame pointer** | `-g` or `--call-graph fp` | **1–2%, lowest in this comparison** | Requires `-fno-omit-frame-pointer`; a convenient production-profiling method. |
| **DWARF** | `--call-graph dwarf,8192` | **15–30%, higher** | Copies stack memory; `perf.data` can grow to gigabytes, but works without frame pointers. |
| **Last Branch Record** | `--call-graph lbr` | **Hardware-assisted, approximately 0% in this comparison** | Uses supported Intel/AMD hardware; depth is limited and availability in VMs is restricted. |

## 4. Reports and analysis: perf report and perf annotate

The recording produces `perf.data`. Inspect it in the terminal:

```bash
perf report --stdio --hierarchy -g graph,0.5,caller
```

Or open the interactive TUI:

```bash
perf report
```

### Report terminology

- **Self:** the percentage of samples with the instruction pointer inside the function itself.
- **Children:** the aggregate CPU time attributed to the function and its descendants.

### Inspecting machine code with perf annotate

Select a CPU-intensive function and press `a`, or run `perf annotate <fonksiyon_adi>`, to inspect its assembly:

```text
       │    Disassembly of section .text:
       │    00000000000011a0 <KarmasikHesapla>:
  0.03 │        push   %rbp
  1.20 │        mov    %rsp,%rbp
 42.50 │ 11b0:  mov    (%rdi,%rax,4),%edx     <-- %42.5 CPU burada bekliyor (Bellek erişimi / Cache miss)
 51.10 │        add    %edx,%ecx
  4.20 │        inc    %rax
  0.97 │        cmp    %rsi,%rax
       │        jne    11b0
```

In this example, 42% of CPU cycles are attributed to reading an array element from RAM.

## 5. Generating a flame graph

Brendan Gregg’s FlameGraph tools turn thousands of lines of profile text into one interactive SVG.

### Download the tools

```bash
git clone https://github.com/brendangregg/FlameGraph.git /tmp/FlameGraph
```

### Generate the SVG

```bash
perf script | /tmp/FlameGraph/stackcollapse-perf.pl | /tmp/FlameGraph/flamegraph.pl > flamegraph.svg
```

### Reading a flame graph

- **Horizontal axis / width:** functions are arranged by stack ordering; this is **not a timeline**. A box’s width represents its share of total CPU samples.
- **Vertical axis / height:** call depth. `main()` is near the bottom; its descendants appear above it.
- **Plateaus:** wide, flat boxes without children are functions consuming CPU directly. Start optimisation investigations there.
- **Search:** use the browser view’s “Search” button or `Ctrl+F`; matching boxes are highlighted in pink.

## Sources and verification environment

- [Brendan Gregg — Linux perf Examples](https://www.brendangregg.com/perf.html)
- [Linux perf wiki](https://perf.wiki.kernel.org/)
- [FlameGraph repository](https://github.com/brendangregg/FlameGraph)

This guide was tested by profiling a real C++ workload on Ubuntu 24.04 LTS (Linux 6.8 x86_64) with `linux-tools-generic` 6.8.0 and FlameGraph.
