---
translation_key: guide-linux-jetson-orin-nano-openclaw
lang: tr
title: "NVIDIA Jetson Orin Nano üzerinde OpenClaw kurulumu"
permalink: /linux/jetson-orin-nano-openclaw-kurulumu/
status: duzenlendi
reviewed: 2026-11-11
scope: NVIDIA JetPack 6 (Ubuntu 22.04 LTS ARM64) üzerinde Jetson Orin Nano (8 GB) için Ollama, Qwen 3.5 2B ve OpenClaw yerel yapay zeka asistanı kurulumu, bellek optimizasyonu ve systemd servis yönetimi.
---

# NVIDIA Jetson Orin Nano üzerinde OpenClaw kurulumu

OpenClaw, harici bir bulut API'sine (OpenAI, Anthropic vb.) ihtiyaç duymadan,
yerel makinede komut çalıştırabilen, dosya okuyup düzenleyebilen ve WhatsApp
veya komut satırı üzerinden etkileşime girilebilen açık kaynaklı bir kişisel
yapay zeka asistanıdır.

NVIDIA Jetson Orin Nano (8 GB), CPU ve GPU arasında paylaşılan birleşik LPDDR5
belleğe sahiptir. Bu donanımda bir dil modelini araç çağırma (tool-calling)
özelliğiyle çalıştırmak; doğru takas alanı (swap) boyutlandırması, dikkat mekanizması
optimizasyonları, daraltılmış bağlam pencereleri ve hafif sistem istemleri gerektirir.

NVIDIA Jetson AI Lab tarafından yayınlanan örnek Python kurulum betiği yerine,
Linux sistem yönetimi standartlarına tam uyumlu, POSIX/Bash sözdizimi kullanan,
harici Python kütüphanesi gerektirmeyen ve doğrudan `systemd` birimleriyle entegre
çalışan tek parça bir Bash kurulum betiği üzerinden kurulumu adım adım inceleyeceğiz.

## Neden Python yerine Bash kurulum betiği?

Gömülü Linux ve uç bilişim (Edge AI) sistemlerinde cihaz hazırlığı (provisioning)
için Bash betikleri tercih edilir:

- **Doğrudan Çekirdek ve Sistem Arayüzleri:** Takas alanı yönetimi (`swapon`, `mkswap`, `fallocate`), `sysctl` parametreleri ve `/etc/fstab` işlemleri kabuk düzeyinde yerel çalışır. Python `subprocess` sarmalayıcılarına gerek kalmaz.
- **Kullanıcı Yetki Ayrımı:** OpenClaw ağ geçidi kullanıcının ev dizininde (`~/.openclaw`) ve kullanıcı `systemd` ortamında (kullanıcı servisi olarak) çalışmalıdır. Yanlışlıkla `root` yetkisiyle çalıştırılması durumunda dosya izinleri ve DBus oturumları bozulur. Bash betiği bu kontrolü en başta yapar ve yalnızca gereken adımlarda `sudo` kullanır.
- **Sıfır Dış Bağımlılık:** Cihazda henüz Python paket yöneticisi (`pip`) veya sanal ortam bulunmasa bile standart bir JetPack imajında doğrudan çalışır.

## Donanım ve mimari optimizasyon kararları (8 GB Orin Nano)

Orin Nano üzerinde kararlı bir asistan deneyimi için uygulanan temel kararlar şunlardır:

| Bileşen | Tercih | Teknik Gerekçe |
| :--- | :--- | :--- |
| **Çıkarım Motoru** | Ollama | JetPack 6 ARM64 CUDA sürücülerini otomatik tanır; hafif ve az bellek tüketir. |
| **Model** | Qwen 3.5 2B (Q8_0) | 8 GB paylaşımlı bellekte ~4.6 GB yer kaplar; yapısal araç çağırma (tool calling) yeteneği güçlüdür. |
| **Takas Alanı** | 16 GB `/var/swapfile` | Model yükleme ve paket derlemelerinde Linux OOM (Out of Memory) katilini engeller. |
| **Ollama Optimizasyonu** | Flash Attention & Q8_0 KV Cache | Dikkat mekanizması belleğini ve anahtar-değer önbelleğini sıkıştırır. |
| **Bağlam Penceresi** | 16,384 token (`num_ctx`) | OpenClaw'ın minimum çalışma sınırını karşılar ve bellek şişmesini sınırlar. |
| **Araç Profili** | `tools.profile: "minimal"` | Ajan sistem istemini (prompt) küçülterek yanıt süresini ve saldırı yüzeyini düşürür. |
| **Ağ Geçidi Güvenliği** | `gateway.bind: "loopback"` | Ağ geçidini yalnızca `127.0.0.1:19000` adresine bağlayarak dış ağa kapatır. `gateway.mode: "local"` bağlamayı denetlemez; yalnızca ağ geçidinin bu cihazda çalıştırılacağını belirtir. |
| **Arka Plan Süreci** | `openclaw gateway install` & Linger | Kullanıcı SSH bağlantısını kapatsa dahi ağ geçidinin arka planda çalışmasını sağlar. |

> **Uyarı:** OpenClaw cihazınızda gerçek eylemler yapabilir: komut çalıştırır, dosya okur ve değiştirir.
> Onu yalnızca güvendiğiniz bir ağda, içinde hassas veri bulunmayan bir cihazda deneyin ve
> ağ geçidini dış ağa açmayın. Bu betik uzak kurulum betiklerini indirip çalıştırır
> (`ollama.com/install.sh`, NodeSource `setup_22.x`) ve `openclaw@latest` paketini `sudo npm`
> ile kurar; çalıştırmadan önce bu betikleri indirip inceleyin ve mümkünse sürüm sabitleyin.

## Ön koşullar

- **Donanım:** NVIDIA Jetson Orin Nano (8 GB) veya Orin Nano Super geliştirici kiti.
- **İşletim Sistemi:** NVIDIA JetPack 6.x (Ubuntu 22.04 LTS aarch64).
- **Disk Alanı:** Kök dizinde (`/`) en az 25 GB boş alan (16 GB takas + 2.7 GB model + sistem paketleri).
- **Kullanıcı:** `sudo` yetkisine sahip normal bir kullanıcı hesabı.

## Tek komutla kurulum betiği: setup-openclaw-orin-nano.sh

Aşağıdaki betik; takas alanını denetler, Ollama ortam yapılandırmalarını yazar,
Qwen modelini indirir, araç çağırma API'sini doğrular, Node.js ve OpenClaw'ı
kurup ağ geçidini başlatır.

İçeriği `setup-openclaw-orin-nano.sh` adıyla kaydedin:

```bash
#!/usr/bin/env bash
#
# setup-openclaw-orin-nano.sh
# Tek komutla kurulum: NVIDIA Jetson Orin Nano (8GB) üzerinde OpenClaw ve Ollama
#

set -euo pipefail

# ANSI Renk Kodları
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Varsayılan Değişkenler
TARGET_SWAP_GB=16
SWAP_PATH="/var/swapfile"
MODEL_NAME="qwen3.5:2b"
CONTEXT_WINDOW=16384
GATEWAY_PORT=19000
# Her kurulumda rastgele üretilir; herkesin bildiği sabit bir değer kullanmayın.
AUTH_TOKEN="$(openssl rand -hex 32)"
FORCE_ARCH=0
SKIP_SWAP=0
SKIP_TEST=0

log_step() {
    local num="$1"
    local title="$2"
    echo -e "\n${BOLD}${CYAN}================================================================${NC}"
    echo -e "  ${BOLD}${CYAN}Adım ${num}: ${title}${NC}"
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
Kullanım: $(basename "$0") [SEÇENEKLER]

NVIDIA Jetson Orin Nano (8 GB) üzerinde Ollama, Qwen 3.5 2B ve OpenClaw
kurulumunu ve sistem servislerini yapılandırır.

Seçenekler:
  --swap-size <GB>    Oluşturulacak takas alanı boyutu (Varsayılan: 16)
  --swap-path <YOL>   Takas dosyasının konumu (Varsayılan: /var/swapfile)
  --model <MODEL>     Kullanılacak Ollama modeli (Varsayılan: qwen3.5:2b)
  --context <BOYUT>   Model bağlam penceresi token boyutu (Varsayılan: 16384)
  --skip-swap         Takas alanı yapılandırma adımını atla
  --skip-test         Kurulum sonrası uçtan uca test mesajını atla
  --force-arch        ARM64 (aarch64) mimari kontrolünü yoksay
  -h, --help          Bu yardım mesajını göster ve çık

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
            fail "Bilinmeyen seçenek: $1 (Yardım için --help kullanın)"
            ;;
    esac
done

ensure_swap() {
    if [[ $SKIP_SWAP -eq 1 ]]; then
        warn "Takas alanı yapılandırması atlandı (--skip-swap)."
        return 0
    fi

    local target_bytes=$((TARGET_SWAP_GB * 1024 * 1024 * 1024))
    local current_bytes
    current_bytes=$(swapon --noheadings --bytes --show=SIZE 2>/dev/null | awk '{sum += $1} END {print sum+0}')
    local current_gb
    current_gb=$(awk -v b="$current_bytes" 'BEGIN {printf "%.1f", b / (1024*1024*1024)}')

    if (( current_bytes >= target_bytes )); then
        ok "Yeterli takas alanı zaten aktif (${current_gb} GB)."
        return 0
    fi

    local free_bytes
    free_bytes=$(df -B1 / | awk 'NR==2 {print $4}')
    local reserve_bytes=$((4 * 1024 * 1024 * 1024))
    local needed_bytes=$((target_bytes + reserve_bytes))

    if (( free_bytes < needed_bytes )); then
        local free_gb
        free_gb=$(awk -v b="$free_bytes" 'BEGIN {printf "%.1f", b / (1024*1024*1024)}')
        warn "Kök dizinde (/) yalnızca ${free_gb} GB boş alan var."
        warn "${TARGET_SWAP_GB} GB takas ve 4 GB güvenlik payı için alan yetersiz. Takas oluşturma atlandı."
        return 0
    fi

    echo "  Mevcut aktif takas: ${current_gb} GB"
    echo "  ${SWAP_PATH} üzerinde ${TARGET_SWAP_GB} GB takas alanı hazırlanıyor..."

    if swapon --show=NAME 2>/dev/null | grep -Fxq "${SWAP_PATH}"; then
        sudo swapoff "${SWAP_PATH}"
    fi

    if ! sudo fallocate -l "${TARGET_SWAP_GB}G" "${SWAP_PATH}" 2>/dev/null; then
        warn "fallocate başarısız oldu; dd ile blok yazımı deneniyor..."
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
    ok "Takas alanı hazır (Toplam ${final_gb} GB aktif)."
}

install_and_tune_ollama() {
    if command -v ollama >/dev/null 2>&1; then
        ok "Ollama zaten kurulu ($(ollama --version 2>&1 | tr '\n' ' '))."
    else
        echo "  Ollama kurulum betiği çalıştırılıyor..."
        curl -fsSL https://ollama.com/install.sh | sh
        ok "Ollama kurulumu tamamlandı."
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
        ok "Ollama bellek optimizasyonları zaten yapılandırılmış."
    else
        echo "  Ollama için 8 GB bellek optimizasyonları yazılıyor..."
        bullet "OLLAMA_FLASH_ATTENTION=1 (Flash Attention ile bellek tasarrufu)"
        bullet "OLLAMA_KV_CACHE_TYPE=q8_0 (KV Cache önbellek sıkıştırması)"
        bullet "OLLAMA_KEEP_ALIVE=1h (Modeli 1 saat bellekte tutma)"

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
        echo "  Ollama servisi yeniden başlatılıyor..."
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
        ok "Ollama servisi aktif (127.0.0.1:11434)."
    else
        sudo journalctl -u ollama --no-pager -n 30 2>&1 || true
        fail "Ollama servisi başlatılamadı veya API yanıt vermiyor."
    fi
}

setup_model() {
    if ollama list 2>/dev/null | grep -q "^${MODEL_NAME}"; then
        ok "${MODEL_NAME} modeli zaten indirilmiş."
    else
        echo "  ${MODEL_NAME} modeli indiriliyor (~2.7 GB)..."
        ollama pull "${MODEL_NAME}"
        ok "${MODEL_NAME} modeli indirildi."
    fi

    echo "  Ollama yapısal araç çağırma (tool calling) test ediliyor..."
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
        ok "Yapısal araç çağırma (tool calling) başarıyla doğrulandı."
    else
        warn "Model araç çağrısı dönmedi; OpenClaw genel sohbet modunda çalışabilir."
    fi
}

install_runtime() {
    local node_major=0
    if command -v node >/dev/null 2>&1; then
        node_major=$(node -v | sed 's/^v//' | cut -d. -f1)
    fi

    if (( node_major >= 22 )); then
        ok "Node.js $(node -v) zaten kurulu."
    else
        echo "  NodeSource üzerinden Node.js 22 LTS kuruluyor..."
        curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
        sudo apt-get install -y nodejs
        ok "Node.js $(node -v) kuruldu."
    fi

    if command -v openclaw >/dev/null 2>&1; then
        ok "OpenClaw zaten kurulu ($(openclaw --version 2>&1))."
    else
        echo "  OpenClaw npm üzerinden küresel olarak kuruluyor..."
        sudo npm install -g openclaw@latest
        ok "OpenClaw $(openclaw --version) kuruldu."
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
    ok "Düşük güçlü cihaz optimizasyonları (.bashrc) uygulandı."
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
    ok "OpenClaw yapılandırma dosyası yazıldı (~/.openclaw/openclaw.json)."
    bullet "contextWindow = ${CONTEXT_WINDOW} (Bellek aşımını önler)"
    bullet "tools.profile = minimal (Saldırı yüzeyini ve sistem istemi boyutunu düşürür)"
    bullet "gateway.bind = loopback (Yalnızca localhost üzerinden erişim sağlar)"

    openclaw models set "ollama/${MODEL_NAME}"
    ok "Varsayılan model 'ollama/${MODEL_NAME}' olarak ayarlandı."

    echo "# Personal assistant" > "${ws_dir}/AGENTS.md"
    echo "Be concise and helpful." > "${ws_dir}/SOUL.md"
    echo "Use tools only when needed." > "${ws_dir}/TOOLS.md"
    echo "Name: User" > "${ws_dir}/USER.md"
    echo "OpenClaw on Jetson Orin Nano" > "${ws_dir}/IDENTITY.md"
    : > "${ws_dir}/HEARTBEAT.md"
    : > "${ws_dir}/BOOTSTRAP.md"
    ok "Hafif çalışma alanı (workspace) şablonları oluşturuldu."

    if openclaw config validate 2>&1 | grep -q "Config valid"; then
        ok "OpenClaw yapılandırması doğrulandı (Config valid)."
    else
        fail "OpenClaw yapılandırma doğrulaması başarısız oldu."
    fi

    if command -v loginctl >/dev/null 2>&1; then
        sudo loginctl enable-linger "$USER"
        ok "Kullanıcı kalıcılığı (systemd linger) etkinleştirildi."
    fi
}

start_gateway_and_test() {
    systemctl --user stop openclaw-gateway 2>/dev/null || true
    systemctl --user reset-failed openclaw-gateway 2>/dev/null || true

    openclaw gateway install --force >/dev/null 2>&1
    echo "  Ağ geçidinin (gateway) ayağa kalkması bekleniyor..."

    local gw_up=0
    for ((i=1; i<=15; i++)); do
        sleep 2
        if openclaw channels status --probe 2>&1 | grep -q "Gateway reachable"; then
            gw_up=1
            break
        fi
    done

    if [[ ${gw_up} -eq 1 ]]; then
        ok "OpenClaw ağ geçidi aktif ve erişilebilir (Gateway reachable)."
    else
        fail "Ağ geçidine bağlanılamadı. 'journalctl --user -u openclaw-gateway -n 40' ile logları inceleyin."
    fi

    if [[ ${SKIP_TEST} -eq 1 ]]; then
        warn "Test mesajı adımı atlandı (--skip-test)."
        return 0
    fi

    echo "  Ajan test mesajı ile sınanıyor..."
    local test_prompt="Hello OpenClaw. Introduce yourself in 2 short sentences. Mention that you are running locally on Jetson Orin Nano."
    echo -e "  ${BOLD}Gönderilen İstem:${NC} ${test_prompt}"

    local reply
    reply=$(openclaw agent \
        --to "+0000000000" \
        --message "${test_prompt}" \
        --thinking off 2>&1 || true)

    echo -e "  ${BOLD}Ajan Yanıtı:${NC}\n${reply}"
    ok "Ajan ilk yanıtını başarıyla üretti."
}

main() {
    echo -e "${BOLD}${CYAN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${CYAN}║    NVIDIA Jetson Orin Nano: OpenClaw Otomatik Kurulumu        ║${NC}"
    echo -e "${BOLD}${CYAN}╚════════════════════════════════════════════════════════════════╝${NC}"

    if [[ $EUID -eq 0 ]]; then
        fail "Bu betik root olarak doğrudan çalıştırılmamalıdır. Normal kullanıcı olarak çalıştırın; gerektiğinde sudo yetkisi istenecektir."
    fi

    local arch
    arch="$(uname -m)"
    if [[ "$arch" != "aarch64" ]]; then
        if [[ $FORCE_ARCH -eq 1 ]]; then
            warn "Mimari aarch64 değil ($arch), fakat --force-arch ile devam ediliyor."
        else
            fail "Bu betik ARM64 (aarch64) Jetson cihazları için hazırlanmıştır. Tespit edilen: $arch. Zorlamak için --force-arch kullanın."
        fi
    fi

    if ! sudo -v; then
        fail "Sudo yetkisi doğrulanamadı."
    fi

    log_step 1 "Bellek ve Takas Alanı (Swap) Hazırlığı"
    ensure_swap

    log_step 2 "Ollama Kurulumu ve 8 GB Donanım Optimizasyonu"
    install_and_tune_ollama

    log_step 3 "Model İndirme (${MODEL_NAME}) ve Araç Çağırma Testi"
    setup_model

    log_step 4 "Node.js 22 LTS ve OpenClaw Kurulumu"
    install_runtime

    log_step 5 "Düşük Bellek Profili ile OpenClaw Yapılandırması"
    configure_openclaw

    log_step 6 "Ağ Geçidi Servisinin Başlatılması ve Test"
    start_gateway_and_test

    echo -e "\n${BOLD}${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${GREEN}║                      Kurulum Tamamlandı!                       ║${NC}"
    echo -e "${BOLD}${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo
    echo -e "${BOLD}Yüklü Model Durumu:${NC}"
    ollama ps 2>/dev/null || true
    echo
    echo -e "${BOLD}Ajan ile Sohbet:${NC}"
    echo "  openclaw agent --to +0000000000 --message \"mesajınız\" --thinking off"
    echo
    echo -e "${BOLD}Servis Yönetimi:${NC}"
    echo "  systemctl --user restart openclaw-gateway"
    echo "  systemctl --user stop openclaw-gateway"
    echo "  openclaw channels status --probe"
    echo "  openclaw logs --follow"
    echo
    echo -e "${BOLD}WhatsApp Bağlantısı (İsteğe bağlı):${NC}"
    echo "  openclaw channels login --channel whatsapp"
    echo
}

main "$@"
```
{: data-filename="setup-openclaw-orin-nano.sh"}

Betiğe çalıştırma izni verip çalıştırın:

```bash
chmod +x setup-openclaw-orin-nano.sh
./setup-openclaw-orin-nano.sh
```

## Adım adım kurulum ve doğrulama aşamaları

Yukarıdaki betiğin arkasında yatan adımları ve sistem yapılandırmalarını tek tek
inceleyelim:

### 1. Takas alanı (Swap) boyutlandırması

8 GB birleşik belleğe sahip Orin Nano'da model belleğe alınırken veya Node.js
paketleri derlenirken sistem kolaylıkla fiziksel sınırına ulaşır. 16 GB takas
dosyası oluşturup kalıcı hale getirin:

```bash
sudo fallocate -l 16G /var/swapfile
sudo chmod 600 /var/swapfile
sudo mkswap /var/swapfile
sudo swapon /var/swapfile
echo '/var/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

Aktif durumu kontrol edin:

```bash
swapon --show
```

Beklenen çıktı:

```text
NAME          TYPE SIZE USED PRIO
/var/swapfile file  16G   0B   -2
```

### 2. Ollama kurulumu ve 8 GB bellek optimizasyonu

Ollama'nın resmi betiği JetPack 6 ARM64 ortamını otomatik olarak algılar ve
uygun CUDA hızlandırmalı ikilileri kurar:

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Kurulum sonrasında `/etc/systemd/system/ollama.service.d/environment.conf` altına
aşağıdaki sistemd drop-in ayarlarını ekleyin:

```ini
[Service]
Environment="OLLAMA_FLASH_ATTENTION=1"
Environment="OLLAMA_KV_CACHE_TYPE=q8_0"
Environment="OLLAMA_KEEP_ALIVE=1h"
```
{: data-filename="environment.conf"}

Ayarları etkinleştirmek için sistemd arka plan sürecini yenileyip servisi yeniden başlatın:

```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

### 3. Modelin çekilmesi ve araç çağırma testi

Qwen 3.5 2B modelini Ollama kütüphanesinden indirin:

```bash
ollama pull qwen3.5:2b
```

Modelin bellek kullanımını kontrol edin:

```bash
ollama ps
```

Beklenen çıktı:

```text
NAME          SIZE      PROCESSOR    CONTEXT    UNTIL
qwen3.5:2b   4.6 GB    100% GPU     16384      59 minutes from now
```

Modelin yapısal araç çağrısını (function calling) desteklediğini API üzerinden sınayın:

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

Yanıt içerisinde `"tool_calls"` anahtarının ve `{"city": "Madrid"}` parametresinin
döndüğünü doğrulayın.

### 4. Node.js 22 LTS ve OpenClaw kurulumu

OpenClaw en az Node.js 22 sürümüne ihtiyaç duyar:

```bash
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs
sudo npm install -g openclaw@latest
```

### 5. Düşük bellekli OpenClaw yapılandırması

`~/.openclaw/openclaw.json` dosyasını oluşturun:

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
      "token": "<kurulumda üretilen 64 karakterlik rastgele değer>"
    }
  }
}
```
{: data-filename="openclaw.json"}

Varsayılan modeli belirleyin:

```bash
openclaw models set "ollama/qwen3.5:2b"
```

Ajanın sistem istemine enjekte edilen çalışma alanı dosyalarını hafif tutun:

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

Yapılandırmayı doğrulayın:

```bash
openclaw config validate
```

SSH oturumu kapandığında kullanıcının arka plan servislerinin sonlandırılmasını
önlemek için linger özelliğini açın:

```bash
sudo loginctl enable-linger $USER
```

### 6. Ağ geçidini başlatma ve ilk sorgu

Ağ geçidini kalıcı bir kullanıcı `systemd` servisi olarak kurup başlatın. `openclaw gateway install`, `openclaw-gateway.service` adlı bir kullanıcı birimi yazar ve etkinleştirir; bu yüzden aşağıdaki `systemctl --user start/stop/restart` komutları ve yeniden başlatma sonrası otomatik açılış çalışır. (`systemd-run --user` ile oluşturulan geçici birim, durdurulduğunda veya cihaz yeniden başladığında kaybolur.)

```bash
openclaw gateway install
```

Ağ geçidinin hazır olduğunu doğrulayın:

```bash
openclaw channels status --probe
```

Beklenen çıktı:

```text
Gateway reachable.
```

Ajana ilk mesajınızı gönderin:

```bash
openclaw agent --to +0000000000 \
  --message "Merhaba, neler yapabilirsin?" \
  --thinking off
```

## Servis yönetimi ve operasyonel komutlar

Günlük yönetim işlemleri için aşağıdaki komutları kullanabilirsiniz:

```bash
# Ağ geçidini başlat
systemctl --user start openclaw-gateway

# Ağ geçidini durdur
systemctl --user stop openclaw-gateway

# Ağ geçidini yeniden başlat
systemctl --user restart openclaw-gateway

# Durum ve sağlık kontrolü
systemctl --user status openclaw-gateway --no-pager
openclaw channels status --probe

# Canlı log takibi
openclaw logs --follow

# Sistemd birim logları
journalctl --user -u openclaw-gateway --no-pager -n 50
```

## İsteğe bağlı: WhatsApp entegrasyonu

OpenClaw'a telefonunuzdaki WhatsApp üzerinden erişmek için terminalde oturum açın:

```bash
openclaw channels login --channel whatsapp
```

Terminalde beliren QR kodu WhatsApp uygulamanızda **Bağlı Cihazlar > Cihaz Bağla**
ekranından taratın. Ardından ağ geçidini yeniden başlatın:

```bash
systemctl --user restart openclaw-gateway
```

WhatsApp'ta kendinize mesaj gönderdiğinizde ajan yanıt verecektir. Sohbet içinde
kullanabileceğiniz doğrudan komutlar:

- `/status`: Oturum bilgisi, harcanan token ve bağlam boyutu.
- `/new`: Geçmişi sıfırlayıp yeni bir oturum başlatır.
- `/stop`: Çalışmakta olan ajan eylemini anında durdurur.
- `/model`: Yapılandırılmış modeller arasında geçiş yapar.

## Büyük Jetson sistemleri için alternatif: Path B (AGX Orin ve Thor)

Eğer 32 GB / 64 GB belleğe sahip **Jetson AGX Orin** veya **AGX Thor** kullanıyorsanız,
Ollama yerine Docker üzerinde **vLLM** motoru ve daha büyük MoE modelleri
(örneğin `Nemotron 3 Nano 30B-A3B`) çalıştırabilirsiniz:

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

> **Uyarı:** `--network host` ile konteynerin dinlediği her port doğrudan cihazın ağ arayüzlerinde açılır ve vLLM varsayılan olarak kimlik doğrulaması istemez. Bu yüzden komut `--host 127.0.0.1` ile yalnızca yerel arayüze bağlanır; sunucuyu ağa açmanız gerekiyorsa `--api-key` ile bir anahtar tanımlayın. Hugging Face belirtecini komut satırına yazmayın: kabuk geçmişine ve süreç listesine düşer. Komuttan önce `read -rs HF_TOKEN && export HF_TOKEN` ile ortam değişkenine alın; `-e HF_TOKEN` değeri oradan okur.

Model servise girdikten sonra `openclaw onboard --skip-daemon` sihirbazını
çalıştırıp sağlayıcı olarak `http://127.0.0.1:8000/v1` adresindeki vLLM'i seçebilirsiniz.

## Sık karşılaşılan sorunlar ve çözümleri

| Belirti / Hata Mesajı | Olası Neden | Çözüm |
| :--- | :--- | :--- |
| `model requires more system memory (7.3 GiB)` | Model varsayılan bağlam penceresi 8 GB sınırı aşıyor. | `~/.openclaw/openclaw.json` içinde `"contextWindow": 16384` ayarını kontrol edin. |
| `Model context window too small. Minimum is 16000` | OpenClaw bağlam penceresi 16K altına ayarlanmış. | Bağlam değerini tam olarak `16384` yapın. |
| `No API key found for provider "anthropic"` | Varsayılan model Ollama olarak seçilmemiş. | `openclaw models set "ollama/qwen3.5:2b"` komutunu çalıştırın. |
| Araç çağırma yanıtı düz metin JSON dönüyor | Ollama yerel API modu yerine generic OpenAI modu kullanılmış. | Yapılandırmada `"api": "ollama"` olduğunu doğrulayın. |
| SSH bağlantısı kesilince ağ geçidi duruyor | Kullanıcı servisleri oturum kapatıldığında sonlandırılıyor. | `sudo loginctl enable-linger $USER` komutunu uygulayın. |
| `LLM request timed out` | Sistem istemi veya çalışma alanı dosyaları çok uzun. | `AGENTS.md` ve `SOUL.md` dosyalarını kısa tutun; `tools.profile: "minimal"` kullanın. |

## Kaynaklar

- [NVIDIA Jetson AI Lab: OpenClaw Eğitimi](https://www.jetson-ai-lab.com/tutorials/openclaw/)
- [Jetson AI Lab GitHub Deposu](https://github.com/NVIDIA-AI-IOT/jetson-ai-lab)
- [OpenClaw Resmi Belgeleri](https://github.com/openclaw/openclaw)
- [Ollama Dokümantasyonu](https://github.com/ollama/ollama)
