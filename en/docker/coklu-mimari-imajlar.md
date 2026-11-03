---
title: Multi-architecture Docker images
permalink: /en/docker/coklu-mimari-imajlar/
status: duzenlendi
reviewed: 2026-11-02
scope: Docker, Buildx and Linux containers; AMD64 and ARM64.
lang: en
translation_key: guide-docker-coklu-mimari-imajlar
translation_of: /docker/coklu-mimari-imajlar/
translated: '2026-11-03'
---

# Multi-architecture Docker images

Buildx lets one tag provide images for different processor architectures. This example targets `linux/amd64` and `linux/arm64`.

## Prerequisites

You need a working Docker installation and Buildx:

```bash
docker version
docker buildx version
```

Docker Desktop includes emulation support; switching to the old Edge channel is unnecessary. On Linux, support depends on the installed BuildKit setup. If emulation is unavailable, see [Docker’s QEMU installation instructions](https://docs.docker.com/build/building/multi-platform/#install-qemu-manually). Builds under emulation may be slower.

## Create a builder

```bash
docker buildx create --name kilavuz-builder --driver docker-container --use
docker buildx inspect --bootstrap
```

Look for both targets in the `Platforms` output. If a builder with this name already exists, select it with `docker buildx use kilavuz-builder`.

## Example Dockerfile

Create a `Dockerfile` in an empty working directory:

```dockerfile
FROM alpine:3.22
CMD ["uname", "-m"]
```

The base image must support the target architectures.

## Test locally

First load one target into the local image store:

```bash
docker buildx build --platform linux/arm64 --load -t mimari-deneme:arm64 .
docker run --rm --platform linux/arm64 mimari-deneme:arm64
```

The expected output is `aarch64`. Running an image for another architecture requires emulation.

## Publish a multi-architecture image

The `docker-container` output is not automatically loaded into the local image store. To push both targets to a registry, put your own Docker Hub username in the variable below. `--push` uploads the image to your account.

```bash
DOCKER_KULLANICI=hesabiniz
docker login
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag "$DOCKER_KULLANICI/mimari-deneme:1" \
  --push .
docker buildx imagetools inspect "$DOCKER_KULLANICI/mimari-deneme:1"
```

The manifest output should include `linux/amd64` and `linux/arm64`.

## Sources and verification

The explanation was checked against the [Docker multi-platform documentation](https://docs.docker.com/build/building/multi-platform/) and [Buildx command reference](https://docs.docker.com/reference/cli/docker/buildx/build/). A local OCI archive containing AMD64 and ARM64 targets was produced using Docker Engine 29.6.2; running the ARM64 image returned `aarch64`. Publishing to a registry was not tested during this repository review.
