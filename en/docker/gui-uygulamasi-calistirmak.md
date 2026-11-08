---
title: Running GUI applications in Docker
permalink: /en/docker/gui-uygulamasi-calistirmak/
status: duzenlendi
reviewed: 2026-11-09
scope: X11 and Wayland display servers on Linux, GPU acceleration (/dev/dri) and secure
  socket authentication.
lang: en
translation_key: guide-docker-gui-uygulamasi-calistirmak
translation_of: /docker/gui-uygulamasi-calistirmak/
translated: '2026-11-09'
---

# Running GUI applications in Docker

Docker containers are inherently designed for headless background services and console tools. However, running desktop applications (Qt, GTK or Electron) in containers can be useful for isolating development environments, using graphical tools that depend on old libraries or automating GUI tests.

To open a window, a container must communicate with the host’s display server or compositor. This guide covers running GUI applications with appropriate permissions and GPU acceleration in both traditional **X11** and modern **Wayland** environments.

## 1. Running a GUI application with X11

In X11, the application inside the container is the **X client**, while the host’s graphical environment is the **X server**.

### Communication channel: a Unix domain socket

X11 servers use Unix domain sockets for fast, low-latency local connections. On the host, these sockets are under `/tmp/.X11-unix/`:

- Socket path: `-v /tmp/.X11-unix:/tmp/.X11-unix:ro`
- Display number: `-e DISPLAY=$DISPLAY` (usually `:0`)

### Authentication: the danger of `xhost +` and secure `XAUTHORITY`

#### Why avoid `xhost +`?

Many online guides suggest `xhost +local:docker` or `xhost +`. These commands loosen or disable X11 access control. Because X11 does not isolate clients from one another, malicious software inside the container could monitor keyboard input in other host windows, capture screenshots or generate synthetic input events (`XSendEvent`).

#### Secure method: XAUTHORITY (MIT-MAGIC-COOKIE-1)

The secure approach is to copy the X server’s 16-byte secret cookie into an isolated file and provide that file to the container.

To prevent authentication failures (`No protocol specified`) caused by the container’s random hostname, the address family is set to `ffff` (FamilyWild):

```bash
# Güvenli geçici xauth dosyası oluşturma
XAUTH=/tmp/.docker.xauth
touch "$XAUTH"
xauth nlist "$DISPLAY" | sed -e 's/^..../ffff/' | xauth -f "$XAUTH" nmerge -
chmod 600 "$XAUTH"
```

### MIT-SHM errors and the IPC namespace

X11 applications transfer high-resolution images using shared memory (`shmget`/`shmat`) rather than copying every byte through the socket. An isolated IPC namespace can cause the application to fail with `BadShmAttach` or `BadAccess`.

**Solution:** add `--ipc=host` to the container command.

### X11 container command

```bash
docker run --rm \
  -e DISPLAY="$DISPLAY" \
  -e XAUTHORITY=/tmp/.docker.xauth \
  -v /tmp/.X11-unix:/tmp/.X11-unix:ro \
  -v "$XAUTH":/tmp/.docker.xauth:ro \
  --user "$(id -u):$(id -g)" \
  --ipc=host \
  gui-test glxgears
```

## 2. Running a native GUI application with Wayland

Wayland is the default display system in Ubuntu 22.04/24.04, Fedora and current Linux desktop environments such as GNOME and KDE Plasma. Wayland clients do not have X11’s client-isolation weaknesses; windows are managed directly by the compositor.

### Socket access and permissions (`XDG_RUNTIME_DIR`)

The host Wayland socket is at `$XDG_RUNTIME_DIR/$WAYLAND_DISPLAY`, for example `/run/user/1000/wayland-0`.

The runtime directory (not necessarily the socket) normally has mode `0700`. Access also depends on UID mapping, capabilities and compositor policy. Root inside a container is not guaranteed to be denied. Use the host UID/GID for this example.

**Solution:** run the container with the host user’s UID and GID:
`--user $(id -u):$(id -g)`

### Hardware GPU acceleration (`/dev/dri`)

Wayland applications allocate window buffers directly in GPU memory. Software rasterisation uses more CPU and can reduce responsiveness:

- Expose the GPU device nodes: `--device /dev/dri:/dev/dri`
- Read the numeric GID from the actual render device; group names and a guessed GID such as 107 are not portable.

### Shared-memory limit (`/dev/shm`)

Docker limits `/dev/shm` to **64 MB** by default. A modern browser, Qt6 or GTK4 interface allocating high-resolution buffers may run out of shared memory and crash with `SIGBUS`. Set `--shm-size=2gb` to raise this limit.

### Wayland container command

```bash
set -eu
RENDER_NODE="${RENDER_NODE:-/dev/dri/renderD128}"
RENDER_GID="$(stat -c '%g' "$RENDER_NODE")"
case "$RENDER_GID" in ''|*[!0-9]*) echo "Invalid render GID" >&2; exit 1 ;; esac
: "${XDG_RUNTIME_DIR:?Run in a Linux Wayland session}"
: "${WAYLAND_DISPLAY:?Set the Wayland socket name}"
test -S "$XDG_RUNTIME_DIR/$WAYLAND_DISPLAY"
docker run --rm -it \
  --user "$(id -u):$(id -g)" \
  -e XDG_RUNTIME_DIR="$XDG_RUNTIME_DIR" \
  -e WAYLAND_DISPLAY="$WAYLAND_DISPLAY" \
  -v "$XDG_RUNTIME_DIR/$WAYLAND_DISPLAY":"$XDG_RUNTIME_DIR/$WAYLAND_DISPLAY":ro \
  --device /dev/dri:/dev/dri \
  --group-add "$RENDER_GID" \
  --shm-size=2gb \
  gui-test vkcube-wayland
```

## 3. Example application: a glxgears / vkcube-wayland test image

A simple `Dockerfile` for testing acceleration and the display connection:

```dockerfile
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    mesa-utils \
    vulkan-tools \
    mesa-vulkan-drivers \
    libgl1-mesa-dri \
    wayland-utils \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

CMD ["wayland-info"]
```
{: data-filename="Dockerfile"}

Build the image:

```bash
docker build -t gui-test .
```

Use `gui-test glxgears` with X11; it is an X11/GLX client, not a native Wayland test. With the Wayland mount, `gui-test wayland-info` checks the protocol connection without requiring `/dev/dri` or a render group. Add the GPU options above for `gui-test vkcube-wayland`. A successful connection does not measure FPS or establish hardware acceleration.

## 4. Common problems and solutions

| Error message | Likely cause | Solution |
| :--- | :--- | :--- |
| `No protocol specified` / `Can't open display` | XAUTHORITY cookie mismatch | Use `xauth nlist` to generate and mount a wildcard (`ffff`) cookie. |
| `X Error of failed request: BadShmAttach` | Container IPC isolation | Add `--ipc=host` to `docker run`. |
| `Permission denied` on the Wayland socket | UID mapping, socket permissions or compositor policy | Use `--user $(id -u):$(id -g)`. |
| `Failed to initialize graphics backend` | Missing GPU device node | Add `--device /dev/dri:/dev/dri` and `--group-add "$RENDER_GID"`. |
| Application suddenly exits with `SIGBUS` | Insufficient `/dev/shm` | Set `--shm-size=2gb`. |

## Sources and verification environment

- [Docker documentation — Runtime Privilege and Linux Capabilities](https://docs.docker.com/engine/containers/run/#runtime-privilege-and-linux-capabilities)
- [Wayland protocol architecture](https://wayland.freedesktop.org/docs/html/)
- [X.Org authentication documentation (Xsecurity)](https://www.x.org/releases/X11R7.6/doc/man/man7/Xsecurity.7.xhtml)

8–9 November 2026: the image and numeric-GID shell paths were checked, along with `wayland-info` and `vkcube-wayland --c 10` on headless Weston with software llvmpipe. No physical Intel/AMD GPU, X11 desktop or FPS measurement was verified.
