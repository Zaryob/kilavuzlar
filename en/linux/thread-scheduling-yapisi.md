---
title: "Linux thread scheduling architecture and internals"
permalink: /en/linux/thread-scheduling-yapisi/
status: duzenlendi
reviewed: 2026-11-19
lang: en
translation_key: guide-linux-thread-scheduling-yapisi
translation_of: /linux/thread-scheduling-yapisi/
translated: '2026-11-19'
scope: Thread representation in the Linux kernel, scheduling classes (CFS, EEVDF, Real-Time, Deadline), vruntime mechanics, context switching, and SMP load balancing.
---

# Linux thread scheduling architecture and internals

The Linux kernel distributes CPU hardware resources among processes and threads when executing
multitasking workloads. However, the Linux architecture differs fundamentally from traditional
operating systems: **there is no distinct "thread" data structure inside the kernel.**

Whether it is a single execution stream or a massive server application spawning hundreds of
worker threads, every schedulable unit in the Linux kernel is represented by a `task_struct` object.
The scheduler balances fairness, latency, and throughput when dispatching these tasks across
CPU cores.

This guide explains how threads are represented in modern Linux 6.x kernels, the modular scheduling
classes (`sched_class`), the CFS and Linux 6.6+ EEVDF algorithms, the hardware-level cost of
context switches, and the SMP multiprocessor load-balancing principles using diagrams.

---

## 1. Thread model in the Linux kernel (1:1 NPTL and `task_struct`)

In standard POSIX terminology, a process (an address-space owner) and a thread (an execution flow)
are conceptually separate entities. Linux implements a **1:1 Threading Model** via NPTL (Native
POSIX Thread Library), where each userspace `pthread` corresponds directly to exactly one kernel
`task_struct`.

### The `clone()` system call and resource sharing

In Linux, a process is created using [`fork(2)`](https://zaryob.github.io/syscall/call/fork/), while a thread is created using the [`clone(2)`](https://zaryob.github.io/syscall/call/clone/) (or modern [`clone3(2)`](https://zaryob.github.io/syscall/call/clone3/)) system
call. In fact, `fork()` and [`vfork(2)`](https://zaryob.github.io/syscall/call/vfork/) are simply wrapper calls to the kernel's internal `kernel_clone()`
function; their only difference lies in the `clone_flags` passed:

- `CLONE_VM`: Shares the virtual memory address space (`mm_struct`).
- `CLONE_FS`: Shares file system root and working directory information (`fs_struct`).
- `CLONE_FILES`: Shares open file descriptors (`files_struct`).
- `CLONE_SIGHAND`: Shares signal handlers.
- `CLONE_THREAD`: Places the task in the caller's Thread Group.

```text
+-----------------------------------------------------------------------------------+
|                        PROCESS AND THREAD ARCHITECTURE                            |
+-----------------------------------------------------------------------------------+

     Userspace
     +-------------------------------------------------------------------------+
     | Process (PID: 4100)                                                     |
     |                                                                         |
     |  +--------------------+   +--------------------+   +-----------------+  |
     |  | Main Thread (TID 1)|   | Worker Thread(TID2)|   | I/O Thread (TID)|  |
     |  | User Stack         |   | User Stack         |   | User Stack      |  |
     |  +---------+----------+   +---------+----------+   +--------+--------+  |
     +------------|------------------------|-----------------------|-----------+
                  | clone(CLONE_VM|...)    |                       |
     Kernel       |                        |                       |
     Space        v                        v                       v
     +------------------------+  +--------------------+  +--------------------+
     | task_struct (Leader)   |  | task_struct        |  | task_struct        |
     |  pid: 4100 (TID)       |  |  pid: 4101 (TID)   |  |  pid: 4102 (TID)   |
     |  tgid: 4100 (PID)      |  |  tgid: 4100 (PID)  |  |  tgid: 4100 (PID)  |
     |  se: sched_entity      |  |  se: sched_entity  |  |  se: sched_entity  |
     |  thread_info / stack   |  |  thread_info/stack |  |  thread_info/stack |
     +-----------+------------+  +---------+----------+  +---------+----------+
                 |                         |                       |
                 +------------+------------+-----------------------+
                              |
                              +---> mm_struct     ──► [Shared Page Tables / Memory]
                              +---> files_struct  ──► [Shared File Descriptors]
                              +---> signal_struct ──► [Shared Signal Handlers]
```

### PID, TID and TGID terminology

There is a distinction in terminology between userspace and the kernel:

| Concept | Userspace (POSIX API) | Kernel Internal (`task_struct`) | Description |
| :--- | :--- | :--- | :--- |
| **Process ID** | [`getpid(2)`](https://zaryob.github.io/syscall/call/getpid/) | `p->tgid` (Thread Group ID) | The identifier of the thread group leader. |
| **Thread ID** | [`gettid(2)`](https://zaryob.github.io/syscall/call/gettid/) / `pthread_self()` | `p->pid` (Process ID) | The unique identifier assigned by the kernel to each individual `task_struct`. |

The scheduler does not inspect `tgid` when dispatching; it directly enqueues the `sched_entity`
embedded inside the `task_struct`.

---

## 2. Scheduling classes and priority hierarchy (`sched_class`)

The Linux kernel utilizes an object-oriented style function table (`struct sched_class`) to provide
a modular scheduler. Each scheduling class defines its own rules for queueing (`enqueue_task`),
dequeueing (`dequeue_task`), and selecting the next task to run (`pick_next_task`).

When a CPU selects the next thread to execute (`pick_next_task()`), the kernel iterates through
the classes in strict order from highest to lowest priority.

```text
+-----------------------------------------------------------------------------------+
|               SCHEDULING CLASSES AND PRIORITY HIERARCHY                           |
+-----------------------------------------------------------------------------------+

   Priority    Scheduling Class       Policy                     Use Case
  ===================================================================================
     0         stop_sched_class       (Kernel Private)         CPU Hotplug, RCU, Migration
     |
     v         dl_sched_class         SCHED_DEADLINE           Hard Real-Time (EDF/CBS)
               ----------------------------------------------------------------------
     1-99      rt_sched_class         SCHED_FIFO, SCHED_RR     Soft Real-Time (Audio, Motor)
               ----------------------------------------------------------------------
    100-139    fair_sched_class       SCHED_NORMAL (OTHER)     Standard User Processes
    (Nice                             SCHED_BATCH              Batch Processing (Background)
    -20..+19)                         SCHED_IDLE               Low-Priority Tasks
               ----------------------------------------------------------------------
    140        idle_sched_class       SCHED_IDLE (swapper)     Power-Saving Idle Loop
```

### 1. `stop_sched_class`
The highest priority class. Regular user or kernel processes cannot join this class. It is used
internally by the kernel to take CPUs offline (CPU hotplug) or handle emergency kernel syncs
(`stop_machine`), preempting all other execution instantly.

### 2. `dl_sched_class` (`SCHED_DEADLINE`)
Based on Earliest Deadline First (EDF) and the Constant Bandwidth Server (CBS). Each task specifies
three parameters:
- **Runtime**: Expected execution duration required per period.
- **Deadline**: Maximum allowable duration before completion.
- **Period**: Recurrence interval.

If the system can guarantee that the aggregate `Runtime / Period` ratio does not exceed CPU capacity
(Admission Control), deadline threads preempt RT and CFS tasks with deterministic scheduling.

### 3. `rt_sched_class` (`SCHED_FIFO`, `SCHED_RR`)
Handles POSIX real-time threads, configured with static priorities ranging from 1 to 99:
- `SCHED_FIFO` (First-In, First-Out): Runs uninterrupted until it blocks on I/O, yields voluntarily
  ([`sched_yield(2)`](https://zaryob.github.io/syscall/call/sched_yield/)), or is preempted by a higher-priority RT task.
- `SCHED_RR` (Round-Robin): Similar to `SCHED_FIFO`, but shares CPU time among tasks of identical
  priority using a fixed timeslice (commonly 100 ms).

> [!WARNING]
> An unbounded `SCHED_FIFO` thread spinning in an infinite loop can freeze the entire desktop
> or system. To prevent this, the kernel reserves 50 ms out of every second for non-realtime
> tasks by default (`/proc/sys/kernel/sched_rt_runtime_us = 950000`).

### 4. `fair_sched_class` (`SCHED_NORMAL` / `SCHED_OTHER`)
The default class serving over 99% of workloads on a typical Linux system. Nice levels (-20 to +19)
operate within this class. It used **CFS** (Completely Fair Scheduler) from Linux 2.6.23 through
Linux 6.5, and transitioned to **EEVDF** (Earliest Eligible Virtual Deadline First) in Linux 6.6+.

### 5. `idle_sched_class`
Invoked only when no runnable tasks remain in any higher queues. Represented by the per-CPU
`swapper/X` task (PID 0), which places idle cores into low-power states (C-states via `hlt`/`mwait`).

---

## 3. Kernel data structures: Per-CPU Runqueues (`struct rq`)

A single global runqueue in a multi-core processor introduces extreme lock contention: every core
must acquire the same global spinlock before dispatching a thread, destroying scalability.

Linux eliminates this bottleneck by maintaining an independent **`struct rq` (Runqueue)** for
every logical CPU core.

```text
+-----------------------------------------------------------------------------------+
|                        PER-CPU RUNQUEUE (struct rq)                               |
+-----------------------------------------------------------------------------------+

     CPU 0                                              CPU 1
  +---------------------------------------+          +---------------------------+
  | struct rq                             |          | struct rq                 |
  |  raw_spinlock_t lock                  |          |  ...                      |
  |  struct task_struct *curr ──► (Running)|          |                           |
  |                                       |          |                           |
  |  +---------------------------------+  |          |                           |
  |  | dl_rq (SCHED_DEADLINE)          |  |          |                           |
  |  |   rb_root_cached (Deadline EDF) |  |          |                           |
  |  +---------------------------------+  |          |                           |
  |                                       |          |                           |
  |  +---------------------------------+  |          |                           |
  |  | rt_rq (SCHED_FIFO / SCHED_RR)   |  |          |                           |
  |  |   prio_array (100 priorities)   |  |          |                           |
  |  |   [0..99] bitmap + queues       |  |          |                           |
  |  +---------------------------------+  |          |                           |
  |                                       |          |                           |
  |  +---------------------------------+  |          |                           |
  |  | cfs_rq (SCHED_NORMAL / EEVDF)   |  |          |                           |
  |  |   rb_root_cached (Red-Black)    |  |          |                           |
  |  |   min_vruntime = 14205820 ns    |  |          |                           |
  |  +---------------------------------+  |          |                           |
  +---------------------------------------+          +---------------------------+
```

### Sub-queues inside `struct rq`

1. **`dl_rq`**: Red-black tree ordered strictly by deadline timestamps.
2. **`rt_rq`**: 100-entry array (`struct rt_prio_array`) paired with a priority bitmap. The kernel
   uses hardware bit-scan instructions (`bsfl`/`clz`) via `sched_find_first_bit()` to identify the
   highest active priority queue in $O(1)$ time.
3. **`cfs_rq`**: Red-black tree tracking normal tasks by virtual runtime (`vruntime`) or EEVDF
   eligibility criteria.

---

## 4. Fair scheduling mechanics: From CFS to EEVDF and `vruntime`

For standard tasks in `fair_sched_class`, the primary goal is dividing CPU execution time
proportionally to task weights derived from nice values.

### Nice values and the weight matrix

The nice scale spans `-20` (highest priority) to `+19` (lowest priority), defaulting to `0`.
The kernel converts nice values into relative execution weights via `sched_prio_to_weight`:

```c
const int sched_prio_to_weight[40] = {
    /* -20 */ 88761, 71755, 56483, ...
    /*   0 */ 1024,
    /* +19 */ 15
};
```

Each 1-point decrease or increase in nice changes CPU allocation weight by roughly **10%**.
For instance, a task with nice -5 gets approximately 3 times more CPU capacity than a nice 0 task.

### Calculating Virtual Runtime (`vruntime`)

When a thread runs on a physical CPU for an interval $\Delta \text{exec}$, the kernel increments
its virtual runtime (`vruntime`) using this normalization formula:

$$\text{vruntime}_{\text{new}} = \text{vruntime}_{\text{old}} + \Delta \text{exec} \times \left( \frac{\text{NICE\_0\_LOAD}}{\text{weight}} \right)$$

- **Nice 0 Task (Weight = 1024)**: The scaling factor is $1024 / 1024 = 1.0$. Virtual time advances
  in 1:1 lockstep with wall-clock time.
- **Low-Priority Task (Nice +10, Weight = 110)**: The factor is $1024 / 110 \approx 9.3$. Running
  for 1 ms advances its `vruntime` by 9.3 ms, pushing it quickly to the right of the queue.
- **High-Priority Task (Nice -5, Weight = 3121)**: The factor is $1024 / 3121 \approx 0.32$. Running
  for 3 ms advances its `vruntime` by only 1 ms, keeping it near the front of the queue.

### Red-Black Tree organization

Tasks are organized inside a self-balancing binary search tree (Red-Black Tree) indexed by `vruntime`:

```text
+-----------------------------------------------------------------------------------+
|               RED-BLACK TREE AND VIRTUAL RUNTIME (vruntime) ORDER                 |
+-----------------------------------------------------------------------------------+

                           [ Node B ]
                         vruntime = 120 ms
                           /           \
                          /             \
               [ Node A ]                [ Node C ]
             vruntime = 95 ms          vruntime = 160 ms
               /
              /
     [ rb_leftmost ]
     vruntime = 80 ms  <-- SCHEDULER PICKS THIS NEXT (O(1) CACHED LOOKUP)
     (Least CPU time consumed,
      highest claim to CPU)
```

The scheduler caches a pointer to the leftmost leaf (`rb_leftmost`), allowing next-task selection
in $O(1)$ time, while tree insertions and deletions remain $O(\log N)$.

### The Shift in Linux 6.6: CFS to EEVDF

While CFS was effective for throughput, it struggled with **latency guarantees**. CFS only guaranteed
fair aggregate CPU shares; it could not guarantee how quickly an interactive thread (such as an audio
buffer, UI event, or network packet) would wake up and gain CPU execution. Heuristics like
`sched_latency` and `min_granularity` were brittle under mixed workloads.

Linux 6.6 adopted **EEVDF (Earliest Eligible Virtual Deadline First)** by Peter Zijlstra.

```text
+-----------------------------------------------------------------------------------+
|                           EEVDF SCHEDULING MECHANICS                              |
+-----------------------------------------------------------------------------------+

   1. Eligibility Check:
      Lag_i = V (Average Virtual Time) - vruntime_i
      * If Lag_i >= 0 (task consumed less than its fair share): ELIGIBLE
      * If Lag_i < 0 (task consumed more than its fair share): INELIGIBLE

   2. Virtual Deadline Calculation:
      d_i = vruntime_i + (Requested Slice q_i / Weight w_i)

   3. Selection Rule:
      The scheduler picks the task with the EARLIEST virtual deadline (d_i)
      strictly among ELIGIBLE candidates (Lag >= 0).
```

EEVDF allows interactive tasks to request smaller timeslices ($q_i$), yielding earlier virtual
deadlines ($d_i$) and enabling immediate preemption of long-running batch compute tasks without
disrupting long-term fairness.

---

## 5. Anatomy of a context switch

Once the scheduler selects the next `task_struct`, it must swap the currently running thread with
the new one on the CPU. This is executed by `context_switch()`.

```text
+-----------------------------------------------------------------------------------+
|                         CONTEXT SWITCH EXECUTION FLOW                             |
+-----------------------------------------------------------------------------------+

                        [ __schedule() Invoked ]
                                    |
                                    v
                         [ pick_next_task() ]
                                    |
                                    v
                        [ context_switch(prev, next) ]
                                    |
        +---------------------------+---------------------------+
        |                                                       |
        v                                                       v
  1. Memory Context Switch                                2. Register Context Switch
     (switch_mm_irqs_off)                                    (switch_to)
        |                                                       |
  +-----+------------------------------+                  +-----+----------------------+
  | prev->mm == next->mm ?             |                  | %rsp (Stack Pointer)       |
  |                                    |                  | %rip (Instruction Pointer) |
  | [YES] -> THREADS OF SAME PROCESS   |                  | General Registers (%rbx..) |
  |   * CR3 register NOT touched!      |                  | FS_BASE / GS_BASE (TLS)    |
  |   * TLB NOT flushed!               |                  | FPU/AVX (XSAVE/XRSTOR)     |
  |   * NEAR ZERO MEMORY PENALTY       |                  +----------------------------+
  |                                    |                                |
  | [NO]  -> DIFFERENT PROCESSES       |                                v
  |   * CR3 reloaded (Page Tables)     |                    [ New Task Resumes ]
  |   * TLB flushed (or PCID tagged)   |
  +------------------------------------+
```

### 1. Memory context switch (`switch_mm_irqs_off`)

When switching between two threads within the same process (`prev->mm == next->mm`), they share
the exact same virtual address space:
- The page table base register (such as `CR3` on x86_64) **is not reloaded**.
- The processor's Translation Lookaside Buffer (TLB) **remains entirely valid**.

This is the primary reason why thread context switches are substantially faster than process
switches. Reloading `CR3` invalidates address translations, triggering a burst of TLB misses and
memory stall cycles.

### 2. Architecture register context switch (`switch_to`)

Hardware state is transferred from the old thread to the new thread:
1. Architectural stack pointer (`%rsp`) and instruction pointer (`%rip`) are swapped.
2. Callee-saved general-purpose registers (`%rbx`, `%rbp`, `%r12` - `%r15`) are saved to and restored
   from the kernel stack.
3. Thread-Local Storage base registers (`FS_BASE` / `GS_BASE`) are redirected.
4. Floating-point and SIMD vector registers (SSE, AVX-512) are saved and restored using optimized
   `XSAVE` / `XRSTOR` instruction sequences.

### Voluntary vs involuntary context switches

- **Voluntary Context Switch**: The thread voluntarily releases the CPU by blocking on I/O,
  waiting on a mutex, or calling `sleep()`.
- **Involuntary (Preemptive) Context Switch**: Triggered when the timer tick (`scheduler_tick`)
  expires a timeslice or a higher-priority task wakes up. The kernel flags `TIF_NEED_RESCHED`,
  and preemption is enforced upon return to userspace.

---

## 6. Multiprocessor (SMP / NUMA) load balancing

Leaving one core idle while another has 50 queued threads hurts system responsiveness. Linux balances
workloads using a tree of **Scheduling Domains (`sched_domain`)**.

```text
+-----------------------------------------------------------------------------------+
|               NUMA AND SCHEDULING DOMAIN (sched_domain) TOPOLOGY                  |
+-----------------------------------------------------------------------------------+

  NUMA Node 0 (Memory Bank 0)                 NUMA Node 1 (Memory Bank 1)
  +---------------------------------------+   +---------------------------------------+
  | Socket 0                              |   | Socket 1                              |
  |  Shared L3 Cache (LLC Domain)         |   |  Shared L3 Cache (LLC Domain)         |
  |                                       |   |                                       |
  |  Core 0 (MC)         Core 1 (MC)      |   |  Core 2 (MC)         Core 3 (MC)      |
  |  +----------------+  +--------------+ |   |  +----------------+  +--------------+ |
  |  | SMT 0  | SMT 1 |  | SMT 2 | SMT 3| |   |  | SMT 4  | SMT 5 |  | SMT 6 | SMT 7| |
  |  | CPU 0  | CPU 1 |  | CPU 2 | CPU 3| |   |  | CPU 4  | CPU 5 |  | CPU 6 | CPU 7| |
  |  +--------+-------+  +-------+------+ |   |  +--------+-------+  +-------+------+ |
  +---------------------------------------+   +---------------------------------------+
        \                                                    /
         \====== High-Speed Interconnect (QPI / UPI / Infinity Fabric) ======/
```

### Balancing hierarchy and overhead

Load balancing progresses from the cheapest hardware boundary to the most expensive:
1. **SMT Domain (Hyper-Threading)**: CPU 0 and CPU 1 share L1/L2 caches. Moving tasks between them
   costs almost nothing.
2. **MC Domain (Multi-Core)**: Cores on the same die share the L3 cache (LLC). Cache repopulation
   penalties are low.
3. **NUMA Domain**: Migrating a task across sockets forces it to access its previously allocated
   RAM remotely across the interconnect fabric, incurring high memory latency. Migration across
   NUMA boundaries is performed only when severe load imbalances occur.

### Core scheduling and CPU affinity

- **CPU Affinity (`taskset` / [`sched_setaffinity(2)`](https://zaryob.github.io/syscall/call/sched_setaffinity/))**: Locks threads to specific CPU cores, preserving
  L1/L2 cache warmth; current masks can be read via [`sched_getaffinity(2)`](https://zaryob.github.io/syscall/call/sched_getaffinity/).
- **Core Scheduling ([`prctl(2)`](https://zaryob.github.io/syscall/call/prctl/))**: Added in Linux 5.14 with `PR_SCHED_CORE`, this feature ensures that only mutually
  trusted threads share SMT sibling threads on the same physical core, preventing hardware side-channel
  vulnerabilities such as Spectre and MDS.

---

## 7. Practical monitoring, diagnosis and priority control

Useful commands for inspecting and diagnosing thread scheduling behavior directly on a running system:

### Listing threads and core assignments

To display threads alongside their scheduling class, priority, and current CPU core:

```bash
ps -eo pid,tid,class,rtprio,ni,pri,psr,comm -L | grep -v "TS   -"
```

Field meanings:
- `tid`: Thread ID.
- `class`: Scheduling class (`TS` = Normal/Fair, `FF` = FIFO, `RR` = Round-Robin, `DL` = Deadline).
- `rtprio`: Real-time priority (1-99).
- `ni`: Nice value (-20 to +19).
- `psr`: The logical processor core currently executing this thread.

For live per-thread monitoring:

```bash
top -H
```

### Tracking voluntary and involuntary context switches

To monitor switch frequencies for a target process and its child threads:

```bash
pidstat -w -t -p <PID> 1
```

Example output:

```text
14:22:01      UID      TGID       TID   cswch/s nvcswch/s  Command
14:22:02     1000      4520         -      2.00    148.00  calculator
14:22:02     1000         -      4520      1.00     50.00  |__calculator
14:22:02     1000         -      4521      1.00     98.00  |__worker_1
```

- `cswch/s` (Voluntary): High counts indicate blocking on mutexes, I/O, or network sockets.
- `nvcswch/s` (Non-voluntary): High counts indicate CPU-bound tasks hitting their timeslice limits.

### Inspecting scheduling metrics via `/proc`

Detailed runtime metrics, virtual runtime values, and migration counts are exposed under `/proc`:

```bash
cat /proc/<PID>/task/<TID>/sched
```

Key output fields:

```text
worker_1 (4521, #threads: 2)
-------------------------------------------------------------------
se.exec_start                                :       1425890.124502
se.vruntime                                  :         15420.892014
se.sum_exec_runtime                          :          1250.410293
se.nr_migrations                             :                    4
nr_switches                                  :                  340
nr_voluntary_switches                        :                   12
nr_involuntary_switches                      :                  328
```

### Adjusting scheduling policies: `chrt` and `renice`

The `chrt` command interfaces with the kernel via [`sched_setscheduler(2)`](https://zaryob.github.io/syscall/call/sched_setscheduler/) and [`sched_setattr(2)`](https://zaryob.github.io/syscall/call/sched_setattr/); policy queries use [`sched_getscheduler(2)`](https://zaryob.github.io/syscall/call/sched_getscheduler/) and [`sched_getattr(2)`](https://zaryob.github.io/syscall/call/sched_getattr/).

To switch a running thread to the `SCHED_FIFO` real-time class with priority 50:

```bash
sudo chrt -f -p 50 <TID>
```

To query a thread's current policy:

```bash
chrt -p <TID>
```

Sample response:

```text
pid 4521's current scheduling policy: SCHED_FIFO
pid 4521's current scheduling priority: 50
```

### Measuring scheduling latency with `perf sched`

To measure the wake-up latency between when a thread becomes runnable and when it actually
starts executing on a CPU:

```bash
sudo perf sched record -- sleep 2
sudo perf sched latency
```

Sample summary:

```text
 -----------------------------------------------------------------------------------------------------------------
  Task                  |   Runtime ms  | Switches | Avg delay ms | Max delay ms | Max delay start     | Max delay at       |
 -----------------------------------------------------------------------------------------------------------------
  worker_1:4521         |   1820.450 ms |      450 |     0.012 ms |     0.185 ms |   142589.102345 s   |   142589.102530 s  |
  kworker/u16:2:120     |     12.100 ms |       45 |     0.004 ms |     0.021 ms |   142588.940120 s   |   142588.940141 s  |
 -----------------------------------------------------------------------------------------------------------------
```

`Avg delay ms` and `Max delay ms` quantify how long tasks waited in runqueues before being
scheduled. Minimizing these latency values is the primary objective in real-time tuning.

---

## References and verification environment

- [Linux Kernel Documentation: CFS Scheduler](https://docs.kernel.org/scheduler/sched-design-CFS.html)
- [Linux Kernel Documentation: Deadline Task Scheduling](https://docs.kernel.org/scheduler/sched-deadline.html)
- [Peter Zijlstra: EEVDF Scheduler Patchset (Linux Kernel Archives)](https://lore.kernel.org/lkml/20230531124603.650795323@infradead.org/)
- [Robert Love: Linux Kernel Development (3rd Edition) - Chapter 4: Process Scheduling](https://www.oreilly.com/library/view/linux-kernel-development/9780768696974/)
- [`sched(7)` manual page](https://man7.org/linux/man-pages/man7/sched.7.html)

### Related system calls (Linux System Call Reference)

- [`clone(2)`](https://zaryob.github.io/syscall/call/clone/): Creating threads or child processes.
- [`clone3(2)`](https://zaryob.github.io/syscall/call/clone3/): Modern extensible `clone` interface.
- [`fork(2)`](https://zaryob.github.io/syscall/call/fork/) and [`vfork(2)`](https://zaryob.github.io/syscall/call/vfork/): Process fork system calls.
- [`getpid(2)`](https://zaryob.github.io/syscall/call/getpid/) and [`gettid(2)`](https://zaryob.github.io/syscall/call/gettid/): Querying process and thread IDs.
- [`sched_yield(2)`](https://zaryob.github.io/syscall/call/sched_yield/): Voluntarily relinquishing the processor.
- [`sched_setaffinity(2)`](https://zaryob.github.io/syscall/call/sched_setaffinity/) and [`sched_getaffinity(2)`](https://zaryob.github.io/syscall/call/sched_getaffinity/): Managing CPU affinity bitmasks.
- [`sched_setscheduler(2)`](https://zaryob.github.io/syscall/call/sched_setscheduler/) and [`sched_getscheduler(2)`](https://zaryob.github.io/syscall/call/sched_getscheduler/): Configuring scheduling policies and priorities.
- [`sched_setattr(2)`](https://zaryob.github.io/syscall/call/sched_setattr/) and [`sched_getattr(2)`](https://zaryob.github.io/syscall/call/sched_getattr/): Extended scheduling attributes (SCHED_DEADLINE and EEVDF slice tuning).
- [`prctl(2)`](https://zaryob.github.io/syscall/call/prctl/): Core scheduling isolation via `PR_SCHED_CORE`.

Commands and kernel data structures in this guide were verified on Ubuntu 24.04 LTS
(Linux 6.8.0-48 x86_64) and Debian 12 (Linux 6.6+ kernel) using `util-linux`, `procps`,
and `linux-tools-generic`.
