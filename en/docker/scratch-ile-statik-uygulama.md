---
title: A static Docker application with scratch
permalink: /en/docker/scratch-ile-statik-uygulama/
status: duzenlendi
reviewed: 2026-11-02
scope: A C++ console application statically compiled with GCC in a Linux container.
lang: en
translation_key: guide-docker-scratch-ile-statik-uygulama
translation_of: /docker/scratch-ile-statik-uygulama/
translated: '2026-11-03'
---

# A static Docker application with scratch

`scratch` creates an image that starts with an empty filesystem. It contains no shell, package manager or shared libraries. We can statically compile a simple C++ application and run it on this base.

## Application

Create `hello.cc` in an empty directory:

```cpp
#include <iostream>

int main() {
    std::cout << "Merhaba, dünya!\n";
    return 0;
}
```

## Dockerfile

The build tools remain in the first stage; only the application is copied into the final image. This also avoids accidentally compiling a non-Linux binary on macOS or Windows.

```dockerfile
FROM gcc:14 AS build
WORKDIR /src
COPY hello.cc .
RUN g++ -O2 -static -o hello hello.cc

FROM scratch
COPY --from=build /src/hello /hello
USER 65532:65532
ENTRYPOINT ["/hello"]
```

## Build and run

In an environment where Docker runs Linux containers:

```bash
docker build --tag hello-scratch .
docker run --rm hello-scratch
```

Expected output:

```text
Merhaba, dünya!
```

## Limitations and verification

Static linking does not remove every application’s runtime requirements. Certificates, time-zone data and files the application needs to read may still be required. This example is only a program that writes to the console.

The behaviour of `scratch` was checked against the [Docker base image documentation](https://docs.docker.com/build/building/base-images/). The example was compiled and run for Linux/ARM64 using Docker Engine 29.6.2; its output was `Merhaba, dünya!` (“Hello, world!”).
