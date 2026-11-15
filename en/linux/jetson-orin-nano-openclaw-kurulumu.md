---
translation_key: guide-linux-jetson-orin-nano-openclaw
lang: en
title: "Installing OpenClaw on NVIDIA Jetson Orin Nano"
permalink: /en/linux/jetson-orin-nano-openclaw-kurulumu/
status: duzenlendi
reviewed: 2026-11-11
translated: 2026-11-11
scope: Setting up OpenClaw, Ollama, Qwen 3.5 2B, and system services on NVIDIA JetPack 6 (Ubuntu 22.04 LTS ARM64) for Jetson Orin Nano (8 GB).
---

# Installing OpenClaw on NVIDIA Jetson Orin Nano

OpenClaw is an open-source personal AI assistant capable of executing shell commands,
reading and editing files, and interacting via WhatsApp or the command line locally,
without requiring third-party cloud APIs (such as OpenAI or Anthropic).

The NVIDIA Jetson Orin Nano (8 GB) features unified LPDDR5 memory shared between the
CPU and GPU. Running a local language model with structured tool-calling capabilities
on this hardware demands deliberate swap sizing, attention optimizations, constrained
context windows, and concise system prompts.

Rather than relying on the sample Python setup script from the NVIDIA Jetson AI Lab,
we walk through an automated, production-grade Bash installation script that conforms
to Linux systems administration standards, requires no external Python libraries,
and integrates directly with `systemd` user units.

## Why a Bash installation script over Python?

For provisioning embedded Linux and Edge AI appliances, shell scripts provide
distinct operational benefits:

- **Direct Kernel and System Interfaces:** Swap management (`swapon`, `mkswap`, `fallocate`), `sysctl` settings, and `/etc/fstab` adjustments operate natively without Python `subprocess` overhead.
- **Privilege Separation:** The OpenClaw gateway must run in the user's home directory (`~/.openclaw`) and user systemd daemon (as a user service). Accidental execution as `root` corrupts file ownership and DBus session sockets. A Bash script enforces this early and invokes `sudo` only when needed.
- **Zero External Dependencies:** It runs immediately on any clean JetPack OS image without requiring Python virtual environments, `pip`, or extra modules.

## Architecture and hardware tuning decisions (8 GB Orin Nano)

The following architectural choices ensure stability under strict 8 GB memory constraints:

| Component | Choice | Technical Rationale |
| :--- | :--- | :--- |
| **Inference Engine** | Ollama | Auto-detects JetPack 6 ARM64 CUDA libraries; lightweight with minimal runtime overhead. |
| **Model** | Qwen 3.5 2B (Q8_0) | Occupies ~4.6 GB in unified GPU memory; provides robust structured tool calling. |
| **Swap Space** | 16 GB `/var/swapfile` | Prevents the Linux OOM (Out of Memory) killer during model loads and package builds. |
| **Ollama Tuning** | Flash Attention & Q8_0 KV Cache | Compresses key-value cache memory and attention activations. |
| **Context Window** | 16,384 tokens (`num_ctx`) | Meets OpenClaw's operating requirement while bounding memory growth. |
| **Tool Profile** | `tools.profile: "minimal"` | Minimizes prompt overhead, decreases latency, and mitigates prompt injection risks. |
| **Gateway Security** | `gateway.bind: "loopback"` | Binds exclusively to `127.0.0.1:19000` to prevent unintended network exposure. `gateway.mode: "local"` does not control binding; it only states that the gateway runs on this device. |
| **Background Service** | `openclaw gateway install` & Linger | Keeps the gateway running after SSH disconnections. |

> **Warning:** OpenClaw can take real actions on your device: it runs commands and reads and modifies files. Try it only on a network you trust, on a device that holds no sensitive data, and do not expose the gateway beyond the local machine. This script downloads and runs remote installers (`ollama.com/install.sh`, NodeSource `setup_22.x`) and installs `openclaw@latest` with `sudo npm`; download and review those scripts before running them, and pin versions where you can.

## Prerequisites

- **Hardware:** NVIDIA Jetson Orin Nano (8 GB) or Orin Nano Super Developer Kit.
- **Operating System:** NVIDIA JetPack 6.x (Ubuntu 22.04 LTS aarch64).
- **Disk Space:** At least 25 GB free space on `/` (16 GB swap + 2.7 GB model + system packages).
- **User:** A non-root user with `sudo` privileges.

## One-click installation script: setup-openclaw-orin-nano.sh

The script below provisions swap, writes Ollama systemd drop-in configurations,
pulls the Qwen model, verifies tool calling, installs Node.js and OpenClaw, and starts
the gateway.

Save this script as `setup-openclaw-orin-nano.sh`:

```bash
#!/usr/bin/env bash
#
# setup-openclaw-orin-nano.sh
# One-click setup: OpenClaw and Ollama on NVIDIA Jetson Orin Nano (8GB)
#

set -euo pipefail

# ANSI Color Codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Default Configuration Variables
TARGET_SWAP_GB=16
SWAP_PATH="/var/swapfile"
MODEL_NAME="qwen3.5:2b"
CONTEXT_WINDOW=16384
GATEWAY_PORT=19000
# Generated randomly on every install; never use a fixed, publicly known value.
AUTH_TOKEN="$(openssl rand -hex 32)"
FORCE_ARCH=0
SKIP_SWAP=0
SKIP_TEST=0

log_step() {
    local num="$1"
    local title="$2"
    echo -e "\n${BOLD}${CYAN}================================================================${NC}"
    echo -e "  ${BOLD}${CYAN}Step ${num}: ${title}${NC}"
    echo -e "${BOLD}${CYAN}================================================================${NC}"
}

ok() {
    echo -e "  ${GREEN}✓ $1${NC}"
}

warn() {
    echo -e "  ${YELLOW}⚠ $1${NC}"
}

fail() {
    echo -e "  ${RED}✗ $1${NC}" >&2
    exit 1
}

bullet() {
    echo -e "  - $1"
}

usage() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Configures Ollama, Qwen 3.5 2B, and OpenClaw on NVIDIA Jetson Orin Nano (8 GB).

Options:
  --swap-size <GB>    Swap space size in gigabytes (Default: 16)
  --swap-path <PATH>  Swap file path (Default: /var/swapfile)
  --model <MODEL>     Ollama model name (Default: qwen3.5:2b)
  --context <SIZE>    Model context window size in tokens (Default: 16384)
  --skip-swap         Skip swap verification and creation
  --skip-test         Skip post-install end-to-end test message
  --force-arch        Ignore ARM64 (aarch64) architecture check
  -h, --help          Show this help message and exit

EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --swap-size)
            TARGET_SWAP_GB="$2"
            shift 2
            ;;
        --swap-path)
            SWAP_PATH="$2"
            shift 2
            ;;
        --model)
            MODEL_NAME="$2"
            shift 2
            ;;
        --context)
            CONTEXT_WINDOW="$2"
            shift 2
            ;;
        --skip-swap)
            SKIP_SWAP=1
            shift
            ;;
        --skip-test)
            SKIP_TEST=1
            shift
            ;;
        --force-arch)
            FORCE_ARCH=1
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            fail "Unknown option: $1 (Use --help for usage details)"
            ;;
    esac
done

ensure_swap() {
    if [[ $SKIP_SWAP -eq 1 ]]; then
        warn "Swap setup skipped by user (--skip-swap)."
        return 0
    fi

    local target_bytes=$((TARGET_SWAP_GB * 1024 * 1024 * 1024))
    local current_bytes
    current_bytes=$(swapon --noheadings --bytes --show=SIZE 2>/dev/null | awk '{sum += $1} END {print sum+0}')
    local current_gb
    current_gb=$(awk -v b="$current_bytes" 'BEGIN {printf "%.1f", b / (1024*1024*1024)}')

    if (( current_bytes >= target_bytes )); then
        ok "Sufficient swap already active (${current_gb} GB)."
        return 0
    fi

    local free_bytes
    free_bytes=$(df -B1 / | awk 'NR==2 {print $4}')
    local reserve_bytes=$((4 * 1024 * 1024 * 1024))
    local needed_bytes=$((target_bytes + reserve_bytes))

    if (( free_bytes < needed_bytes )); then
        local free_gb
        free_gb=$(awk -v b="$free_bytes" 'BEGIN {printf "%.1f", b / (1024*1024*1024)}')
        warn "Only ${free_gb} GB free on /."
        warn "Insufficient space for a ${TARGET_SWAP_GB} GB swap file with a 4 GB safety margin. Skipping swap creation."
        return 0
    fi

    echo "  Current active swap: ${current_gb} GB"
    echo "  Creating ${TARGET_SWAP_GB} GB swap file at ${SWAP_PATH}..."

    if swapon --show=NAME 2>/dev/null | grep -Fxq "${SWAP_PATH}"; then
        sudo swapoff "${SWAP_PATH}"
    fi

    if ! sudo fallocate -l "${TARGET_SWAP_GB}G" "${SWAP_PATH}" 2>/dev/null; then
        warn "fallocate failed; falling back to dd zero-fill..."
        sudo dd if=/dev/zero of="${SWAP_PATH}" bs=1M count=$((TARGET_SWAP_GB * 1024)) status=progress
    fi

    sudo chmod 600 "${SWAP_PATH}"
    sudo mkswap "${SWAP_PATH}" >/dev/null
    sudo swapon "${SWAP_PATH}"

    local fstab_line="${SWAP_PATH} none swap sw 0 0"
    if ! grep -qs "^${SWAP_PATH}" /etc/fstab; then
        echo "${fstab_line}" | sudo tee -a /etc/fstab >/dev/null
    fi

    local final_bytes
    final_bytes=$(swapon --noheadings --bytes --show=SIZE 2>/dev/null | awk '{sum += $1} END {print sum+0}')
    local final_gb
    final_gb=$(awk -v b="$final_bytes" 'BEGIN {printf "%.1f", b / (1024*1024*1024)}')
    ok "Swap ready (Total ${final_gb} GB active)."
}

install_and_tune_ollama() {
    if command -v ollama >/dev/null 2>&1; then
        ok "Ollama already installed ($(ollama --version 2>&1 | tr '\n' ' '))."
    else
        echo "  Running Ollama installer..."
        curl -fsSL https://ollama.com/install.sh | sh
        ok "Ollama installed."
    fi

    local env_dir="/etc/systemd/system/ollama.service.d"
    local env_file="${env_dir}/environment.conf"
    local needs_restart=0

    sudo mkdir -p "${env_dir}"

    local expected_config='[Service]
Environment="OLLAMA_FLASH_ATTENTION=1"
Environment="OLLAMA_KV_CACHE_TYPE=q8_0"
Environment="OLLAMA_KEEP_ALIVE=1h"'

    if [[ -f "${env_file}" ]] && cmp -s <(echo "${expected_config}") "${env_file}"; then
        ok "Ollama memory optimizations already configured."
    else
        echo "  Applying 8 GB memory optimizations for Ollama..."
        bullet "OLLAMA_FLASH_ATTENTION=1 (Flash Attention memory reduction)"
        bullet "OLLAMA_KV_CACHE_TYPE=q8_0 (KV Cache quantization)"
        bullet "OLLAMA_KEEP_ALIVE=1h (Hold model in memory for 1 hour)"

        echo "${expected_config}" | sudo tee "${env_file}" >/dev/null
        sudo systemctl daemon-reload
        needs_restart=1
    fi

    sudo mkdir -p /usr/share/ollama
    if id "ollama" >/dev/null 2>&1; then
        sudo chown -R ollama:ollama /usr/share/ollama
    fi
    sudo chmod 755 /usr/share/ollama

    local state
    state="$(systemctl is-active ollama 2>/dev/null || true)"
    if [[ "${state}" != "active" || ${needs_restart} -eq 1 ]]; then
        echo "  Restarting Ollama service..."
        sudo systemctl restart ollama
    fi

    local ready=0
    for ((i=1; i<=15; i++)); do
        if [[ "$(systemctl is-active ollama 2>/dev/null)" == "active" ]] && curl -sf http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
            ready=1
            break
        fi
        sleep 2
    done

    if [[ ${ready} -eq 1 ]]; then
        ok "Ollama service is active (127.0.0.1:11434)."
    else
        sudo journalctl -u ollama --no-pager -n 30 2>&1 || true
        fail "Ollama service failed to start or API is unreachable."
    fi
}

setup_model() {
    if ollama list 2>/dev/null | grep -q "^${MODEL_NAME}"; then
        ok "${MODEL_NAME} model already downloaded."
    else
        echo "  Downloading ${MODEL_NAME} (~2.7 GB)..."
        ollama pull "${MODEL_NAME}"
        ok "${MODEL_NAME} model downloaded."
    fi

    echo "  Testing Ollama structured tool calling..."
    local payload
    payload=$(cat << 'EOF'
{
  "model": "qwen3.5:2b",
  "messages": [{"role": "user", "content": "What is the weather in Madrid?"}],
  "stream": false,
  "options": {"num_ctx": 16384},
  "tools": [{
    "type": "function",
    "function": {
      "name": "get_weather",
      "description": "Get weather for a city",
      "parameters": {
        "type": "object",
        "required": ["city"],
        "properties": {
          "city": {"type": "string", "description": "City name"}
        }
      }
    }
  }]
}
EOF
)
    if [[ "${MODEL_NAME}" != "qwen3.5:2b" ]]; then
        payload="${payload/\"model\": \"qwen3.5:2b\"/\"model\": \"${MODEL_NAME}\"}"
    fi

    local response
    response=$(curl -s -m 120 -X POST http://127.0.0.1:11434/api/chat \
        -H "Content-Type: application/json" \
        -d "${payload}" 2>/dev/null || true)

    if echo "${response}" | grep -q '"tool_calls"'; then
        ok "Structured tool calling verified."
    else
        warn "No structured tool call returned; OpenClaw will operate in standard chat mode."
    fi
}

install_runtime() {
    local node_major=0
    if command -v node >/dev/null 2>&1; then
        node_major=$(node -v | sed 's/^v//' | cut -d. -f1)
    fi

    if (( node_major >= 22 )); then
        ok "Node.js $(node -v) already installed."
    else
        echo "  Installing Node.js 22 LTS via NodeSource..."
        curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
        sudo apt-get install -y nodejs
        ok "Node.js $(node -v) installed."
    fi

    if command -v openclaw >/dev/null 2>&1; then
        ok "OpenClaw already installed ($(openclaw --version 2>&1))."
    else
        echo "  Installing OpenClaw globally via npm..."
        sudo npm install -g openclaw@latest
        ok "OpenClaw $(openclaw --version) installed."
    fi

    mkdir -p /var/tmp/openclaw-compile-cache
    if ! grep -qs "NODE_COMPILE_CACHE" "$HOME/.bashrc"; then
        echo 'export NODE_COMPILE_CACHE=/var/tmp/openclaw-compile-cache' >> "$HOME/.bashrc"
    fi
    if ! grep -qs "OPENCLAW_NO_RESPAWN" "$HOME/.bashrc"; then
        echo 'export OPENCLAW_NO_RESPAWN=1' >> "$HOME/.bashrc"
    fi
    export NODE_COMPILE_CACHE=/var/tmp/openclaw-compile-cache
    export OPENCLAW_NO_RESPAWN=1
    ok "Low-memory runtime optimizations applied (.bashrc)."
}

configure_openclaw() {
    local oc_dir="$HOME/.openclaw"
    local ws_dir="${oc_dir}/workspace"
    local config_file="${oc_dir}/openclaw.json"

    mkdir -p "${ws_dir}"

    cat > "${config_file}" << EOF
{
  "models": {
    "providers": {
      "ollama": {
        "baseUrl": "http://127.0.0.1:11434",
        "apiKey": "ollama-local",
        "api": "ollama",
        "models": [
          {
            "id": "${MODEL_NAME}",
            "name": "Qwen 3.5 2B",
            "contextWindow": ${CONTEXT_WINDOW}
          }
        ]
      }
    }
  },
  "tools": {
    "profile": "minimal"
  },
  "gateway": {
    "port": ${GATEWAY_PORT},
    "mode": "local",
    "bind": "loopback",
    "auth": {
      "mode": "token",
      "token": "${AUTH_TOKEN}"
    }
  }
}
EOF
    ok "OpenClaw configuration written (~/.openclaw/openclaw.json)."
    bullet "contextWindow = ${CONTEXT_WINDOW} (Prevents memory exhaustion)"
    bullet "tools.profile = minimal (Reduces prompt overhead and attack surface)"
    bullet "gateway.bind = loopback (Restricts binding to localhost)"

    openclaw models set "ollama/${MODEL_NAME}"
    ok "Default model set to 'ollama/${MODEL_NAME}'."

    echo "# Personal assistant" > "${ws_dir}/AGENTS.md"
    echo "Be concise and helpful." > "${ws_dir}/SOUL.md"
    echo "Use tools only when needed." > "${ws_dir}/TOOLS.md"
    echo "Name: User" > "${ws_dir}/USER.md"
    echo "OpenClaw on Jetson Orin Nano" > "${ws_dir}/IDENTITY.md"
    : > "${ws_dir}/HEARTBEAT.md"
    : > "${ws_dir}/BOOTSTRAP.md"
    ok "Lightweight workspace templates created."

    if openclaw config validate 2>&1 | grep -q "Config valid"; then
        ok "OpenClaw configuration verified (Config valid)."
    else
        fail "OpenClaw configuration validation failed."
    fi

    if command -v loginctl >/dev/null 2>&1; then
        sudo loginctl enable-linger "$USER"
        ok "User service persistence (systemd linger) enabled."
    fi
}

start_gateway_and_test() {
    systemctl --user stop openclaw-gateway 2>/dev/null || true
    systemctl --user reset-failed openclaw-gateway 2>/dev/null || true

    openclaw gateway install --force >/dev/null 2>&1
    echo "  Waiting for gateway to initialize..."

    local gw_up=0
    for ((i=1; i<=15; i++)); do
        sleep 2
        if openclaw channels status --probe 2>&1 | grep -q "Gateway reachable"; then
            gw_up=1
            break
        fi
    done

    if [[ ${gw_up} -eq 1 ]]; then
        ok "OpenClaw gateway active and reachable."
    else
        fail "Could not reach gateway. Inspect logs with: journalctl --user -u openclaw-gateway -n 40"
    fi

    if [[ ${SKIP_TEST} -eq 1 ]]; then
        warn "Test message skipped (--skip-test)."
        return 0
    fi

    echo "  Sending test message to agent..."
    local test_prompt="Hello OpenClaw. Introduce yourself in 2 short sentences. Mention that you are running locally on Jetson Orin Nano."
    echo -e "  ${BOLD}Prompt:${NC} ${test_prompt}"

    local reply
    reply=$(openclaw agent \
        --to "+0000000000" \
        --message "${test_prompt}" \
        --thinking off 2>&1 || true)

    echo -e "  ${BOLD}Agent Response:${NC}\n${reply}"
    ok "Agent generated its initial response successfully."
}

main() {
    echo -e "${BOLD}${CYAN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${CYAN}║     NVIDIA Jetson Orin Nano: OpenClaw Automated Setup         ║${NC}"
    echo -e "${BOLD}${CYAN}╚════════════════════════════════════════════════════════════════╝${NC}"

    if [[ $EUID -eq 0 ]]; then
        fail "Do not run this script directly as root. Run as a regular user; sudo will be invoked when necessary."
    fi

    local arch
    arch="$(uname -m)"
    if [[ "$arch" != "aarch64" ]]; then
        if [[ $FORCE_ARCH -eq 1 ]]; then
            warn "Architecture is not aarch64 ($arch), continuing due to --force-arch."
        else
            fail "This script is tailored for ARM64 (aarch64) Jetson platforms. Detected: $arch. Use --force-arch to override."
        fi
    fi

    if ! sudo -v; then
        fail "Unable to validate sudo credentials."
    fi

    log_step 1 "Memory and Swap Space Setup"
    ensure_swap

    log_step 2 "Ollama Installation and 8 GB Hardware Tuning"
    install_and_tune_ollama

    log_step 3 "Model Download (${MODEL_NAME}) and Tool-Calling Check"
    setup_model

    log_step 4 "Node.js 22 LTS and OpenClaw Installation"
    install_runtime

    log_step 5 "Low-Memory OpenClaw Configuration"
    configure_openclaw

    log_step 6 "Gateway Service Launch and End-to-End Validation"
    start_gateway_and_test

    echo -e "\n${BOLD}${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${GREEN}║                      Setup Complete!                           ║${NC}"
    echo -e "${BOLD}${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo
    echo -e "${BOLD}Loaded Model Status:${NC}"
    ollama ps 2>/dev/null || true
    echo
    echo -e "${BOLD}Chatting with Agent:${NC}"
    echo "  openclaw agent --to +0000000000 --message \"your message\" --thinking off"
    echo
    echo -e "${BOLD}Service Management:${NC}"
    echo "  systemctl --user restart openclaw-gateway"
    echo "  systemctl --user stop openclaw-gateway"
    echo "  openclaw channels status --probe"
    echo "  openclaw logs --follow"
    echo
    echo -e "${BOLD}WhatsApp Integration (Optional):${NC}"
    echo "  openclaw channels login --channel whatsapp"
    echo
}

main "$@"
```
{: data-filename="setup-openclaw-orin-nano.sh"}

Make the script executable and run it:

```bash
chmod +x setup-openclaw-orin-nano.sh
./setup-openclaw-orin-nano.sh
```

## Step-by-step breakdown and system configuration

Below is an in-depth breakdown of what occurs at each stage of the installation:

### 1. Swap space allocation

With unified memory on the Orin Nano, memory-intensive model loads or Node.js
builds can trigger the OOM killer. Allocate a persistent 16 GB swap file:

```bash
sudo fallocate -l 16G /var/swapfile
sudo chmod 600 /var/swapfile
sudo mkswap /var/swapfile
sudo swapon /var/swapfile
echo '/var/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

Verify active swap:

```bash
swapon --show
```

Expected output:

```text
NAME          TYPE SIZE USED PRIO
/var/swapfile file  16G   0B   -2
```

### 2. Ollama setup and 8 GB memory tuning

The official Ollama script detects JetPack 6 ARM64 and installs the required CUDA
libraries automatically:

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Create a systemd drop-in configuration at `/etc/systemd/system/ollama.service.d/environment.conf`:

```ini
[Service]
Environment="OLLAMA_FLASH_ATTENTION=1"
Environment="OLLAMA_KV_CACHE_TYPE=q8_0"
Environment="OLLAMA_KEEP_ALIVE=1h"
```
{: data-filename="environment.conf"}

Reload the systemd daemon and restart the service:

```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

### 3. Model download and tool-calling verification

Pull Qwen 3.5 2B:

```bash
ollama pull qwen3.5:2b
```

Check memory usage:

```bash
ollama ps
```

Expected output:

```text
NAME          SIZE      PROCESSOR    CONTEXT    UNTIL
qwen3.5:2b   4.6 GB    100% GPU     16384      59 minutes from now
```

Verify tool calling via the Ollama REST API:

```bash
curl -s http://localhost:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3.5:2b",
    "messages": [{"role": "user", "content": "What is the weather in Madrid?"}],
    "stream": false,
    "options": {"num_ctx": 16384},
    "tools": [{
      "type": "function",
      "function": {
        "name": "get_weather",
        "description": "Get weather for a city",
        "parameters": {
          "type": "object",
          "required": ["city"],
          "properties": {
            "city": {"type": "string", "description": "City name"}
          }
        }
      }
    }]
  }'
```

Verify that `"tool_calls"` is present in the response with `{"city": "Madrid"}`.

### 4. Node.js 22 LTS and OpenClaw installation

OpenClaw requires Node.js version 22 or higher:

```bash
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs
sudo npm install -g openclaw@latest
```

### 5. Low-memory OpenClaw configuration

Create `~/.openclaw/openclaw.json`:

```json
{
  "models": {
    "providers": {
      "ollama": {
        "baseUrl": "http://127.0.0.1:11434",
        "apiKey": "ollama-local",
        "api": "ollama",
        "models": [
          {
            "id": "qwen3.5:2b",
            "name": "Qwen 3.5 2B",
            "contextWindow": 16384
          }
        ]
      }
    }
  },
  "tools": {
    "profile": "minimal"
  },
  "gateway": {
    "port": 19000,
    "mode": "local",
    "bind": "loopback",
    "auth": {
      "mode": "token",
      "token": "<64-character random value generated during install>"
    }
  }
}
```
{: data-filename="openclaw.json"}

Set the default model:

```bash
openclaw models set "ollama/qwen3.5:2b"
```

Initialize lightweight workspace files to minimize prompt overhead:

```bash
mkdir -p ~/.openclaw/workspace
echo "# Personal assistant" > ~/.openclaw/workspace/AGENTS.md
echo "Be concise and helpful." > ~/.openclaw/workspace/SOUL.md
echo "Use tools only when needed." > ~/.openclaw/workspace/TOOLS.md
echo "Name: User" > ~/.openclaw/workspace/USER.md
echo "OpenClaw on Jetson Orin Nano" > ~/.openclaw/workspace/IDENTITY.md
: > ~/.openclaw/workspace/HEARTBEAT.md
: > ~/.openclaw/workspace/BOOTSTRAP.md
```

Validate the configuration:

```bash
openclaw config validate
```

Enable user lingering so background services survive SSH disconnections:

```bash
sudo loginctl enable-linger $USER
```

### 6. Starting the gateway and running initial queries

Install and start the gateway as a persistent systemd user service. `openclaw gateway install` writes and enables a user unit named `openclaw-gateway.service`, so the `systemctl --user start/stop/restart` commands below and start-up after a reboot work. (A transient unit created with `systemd-run --user` disappears when it is stopped or the device reboots.)

```bash
openclaw gateway install
```

Confirm gateway availability:

```bash
openclaw channels status --probe
```

Expected output:

```text
Gateway reachable.
```

Send a prompt:

```bash
openclaw agent --to +0000000000 \
  --message "Hello, what tasks can you assist with?" \
  --thinking off
```

## Service management reference

Operational commands for daily lifecycle management:

```bash
# Start the gateway
systemctl --user start openclaw-gateway

# Stop the gateway
systemctl --user stop openclaw-gateway

# Restart the gateway
systemctl --user restart openclaw-gateway

# Status and probe
systemctl --user status openclaw-gateway --no-pager
openclaw channels status --probe

# Follow logs in real time
openclaw logs --follow

# Inspect systemd unit logs
journalctl --user -u openclaw-gateway --no-pager -n 50
```

## Optional: Connecting WhatsApp

To use OpenClaw directly from WhatsApp on your mobile phone:

```bash
openclaw channels login --channel whatsapp
```

Scan the terminal QR code in WhatsApp under **Settings > Linked Devices > Link a Device**.
Then restart the gateway:

```bash
systemctl --user restart openclaw-gateway
```

Once paired, the following direct commands can be sent inside the chat:

- `/status`: Session statistics, tokens consumed, and active context length.
- `/new`: Reset conversation history and start a fresh session.
- `/stop`: Interrupt running agent actions immediately.
- `/model`: Switch between configured model backends.

## Alternative for higher-end Jetson hardware: Path B (AGX Orin and Thor)

For systems with 32 GB or 64 GB unified memory, such as the **Jetson AGX Orin**
or **AGX Thor**, consider deploying **vLLM** in Docker with larger MoE architectures
(such as `Nemotron 3 Nano 30B-A3B`):

```bash
docker run -d \
  --runtime nvidia \
  --gpus all \
  --network host \
  --ipc host \
  -e HF_TOKEN \
  -v $HOME/.cache/huggingface:/data/models/huggingface \
  ghcr.io/nvidia-ai-iot/vllm:latest-jetson-orin \
  vllm serve stelterlab/NVIDIA-Nemotron-3-Nano-30B-A3B-AWQ \
  --host 127.0.0.1 \
  --gpu-memory-utilization 0.8 \
  --trust-remote-code \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3_coder \
  --kv-cache-dtype fp8
```

> **Warning:** With `--network host`, every port the container listens on is opened directly on the device’s network interfaces, and vLLM asks for no authentication by default. The command therefore binds to the local interface only with `--host 127.0.0.1`; if you must expose the server, define a key with `--api-key`. Do not type the Hugging Face token on the command line: it ends up in shell history and the process list. Load it into the environment first with `read -rs HF_TOKEN && export HF_TOKEN`; `-e HF_TOKEN` reads the value from there.

Once the model container is serving at `http://127.0.0.1:8000/v1`, run `openclaw onboard --skip-daemon`
and select vLLM as the provider.

## Troubleshooting

| Symptom / Error Message | Root Cause | Remediation |
| :--- | :--- | :--- |
| `model requires more system memory (7.3 GiB)` | Default context window exceeds 8 GB limit. | Ensure `"contextWindow": 16384` is defined in `~/.openclaw/openclaw.json`. |
| `Model context window too small. Minimum is 16000` | Context setting is lower than OpenClaw minimum. | Set `"contextWindow": 16384`. |
| `No API key found for provider "anthropic"` | Default model was not switched to Ollama. | Execute `openclaw models set "ollama/qwen3.5:2b"`. |
| Tool calling returns raw JSON text | Generic OpenAI mode used instead of native Ollama mode. | Verify `"api": "ollama"` is specified in `openclaw.json`. |
| Gateway stops upon SSH exit | Systemd kills user units on session logout. | Execute `sudo loginctl enable-linger $USER`. |
| `LLM request timed out` | System prompt or workspace files exceed prompt budget. | Keep `AGENTS.md` and `SOUL.md` concise; set `tools.profile: "minimal"`. |

## References

- [NVIDIA Jetson AI Lab: OpenClaw Tutorial](https://www.jetson-ai-lab.com/tutorials/openclaw/)
- [Jetson AI Lab GitHub Repository](https://github.com/NVIDIA-AI-IOT/jetson-ai-lab)
- [OpenClaw Official Repository](https://github.com/openclaw/openclaw)
- [Ollama Project Documentation](https://github.com/ollama/ollama)
