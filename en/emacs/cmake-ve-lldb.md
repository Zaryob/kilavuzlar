---
title: Using CMake and LLDB in Emacs
permalink: /en/emacs/cmake-ve-lldb/
status: duzenlendi
reviewed: 2026-11-09
scope: Modern C++ development and lldb-dap debugging in GNU Emacs 29+ with Eglot,
  project.el, compile and dape.
lang: en
translation_key: guide-emacs-cmake-ve-lldb
translation_of: /emacs/cmake-ve-lldb/
translated: '2026-11-09'
---

# Using CMake and LLDB in Emacs

C++ development in Emacs has changed substantially through the built-in LSP client `eglot`, project manager `project.el` and Debug Adapter Protocol client `dape`. A modern IDE workflow can now be built with lightweight components without installing a large stack of packages such as `lsp-mode`, `treemacs`, `hydra` and `dap-mode`.

This guide configures and builds a CMake-based C++ project in Emacs, then debugs it visually using `lldb-dap` from LLVM 18+.

## 1. Why dape and lldb-dap?

Historically, debugging in Emacs had two main approaches:

1. **GUD**: a long-established debugger interface; `gud-lldb` itself was added in Emacs 30. Dape uses the structured DAP protocol instead of parsing terminal output.
2. **`dap-mode`**: brought the VS Code debugging protocol to Emacs, but is closely tied to the larger `lsp-mode` ecosystem.

**`dape` — Debug Adapter Protocol for Emacs:**
- Works with the built-in `eglot` and `project.el` in Emacs 29+ without requiring another LSP package.
- Opens a GDB-MI-style multipane dashboard (`*dape-info*`) with threads, stack traces, locals, watches and breakpoints.
- Displays variable values directly in source buffers as inlay hints.
- Uses `repeat-mode` for single-key stepping (`n`, `s`, `c`, `o`).

> [!NOTE]
> In LLVM 18, `lldb-vscode` was renamed **`lldb-dap`** to reflect the protocol’s broader applicability.

## 2. Emacs configuration (`init.el`)

Add this configuration to `~/.emacs.d/init.el` or `~/.config/emacs/init.el`:

```elisp
;;; init.el --- Modern C++, CMake ve LLDB Yapılandırması

(require 'use-package)
(setq use-package-always-ensure t)

;; -------------------------------------------------------------
;; 1. Dil Sunucusu (Yerleşik Eglot + Clangd)
;; -------------------------------------------------------------
(use-package eglot
  :ensure nil ; Emacs 29 ile yerleşiktir
  :hook
  ((c-mode c++-mode c-ts-mode c++-ts-mode) . eglot-ensure)
  :config
  (add-to-list 'eglot-server-programs
               '((c-mode c++-mode c-ts-mode c++-ts-mode)
                 . ("clangd"
                    "--background-index"
                    "--clang-tidy"
                    "--completion-style=detailed"
                    "--header-insertion=iwyu"))))

;; -------------------------------------------------------------
;; 2. Proje ve Derleme (Yerleşik project.el & compile)
;; -------------------------------------------------------------
(use-package project
  :ensure nil
  :config
  ;; Git deposu olmasa dahi CMakeLists.txt bulunan dizini proje kökü say
  (add-to-list 'project-vc-extra-root-markers "CMakeLists.txt"))

(use-package compile
  :ensure nil
  :custom
  ;; Her defasında sormadan doğrudan son derleme komutunu çalıştır
  ;; Komutu değiştirmek istediğinizde C-u M-x compile yapabilirsiniz
  (compilation-read-command nil)
  (compilation-scroll-output 'first-error)
  (compilation-always-kill t)
  :bind
  (("C-c c" . compile)
   ("C-c r" . recompile)))

;; -------------------------------------------------------------
;; 3. Modern Hata Ayıklama (dape + lldb-dap)
;; -------------------------------------------------------------
(use-package dape
  :preface
  (setq dape-buffer-window-arrangement 'gdb)
  :config
  ;; Adımlama sırasında tek tuş kullanımını etkinleştir (n, s, c, o)
  (repeat-mode 1)
  
  ;; Kod içinde değişken değerlerini satır sonunda göster
  (setq dape-inlay-hints t)

  ;; lldb-dap yapılandırmasını özelleştir
  (with-eval-after-load 'dape
    (add-to-list 'dape-configs
                 `(lldb-cpp
                   modes (c-mode c++-mode c-ts-mode c++-ts-mode)
                   command "lldb-dap"
                   :type "executable"
                   :request "launch"
                   :cwd "."
                   :program (lambda ()
                              (read-file-name "İkili dosya seçin: "
                                              (expand-file-name "build/" (dape-cwd))))
                   :args []
                   :stopOnEntry nil)))
  :bind
  (("C-x C-a d" . dape)
   ("C-x C-a b" . dape-breakpoint-toggle)
   ("C-x C-a e" . dape-breakpoint-expression)
   ("C-x C-a R" . dape-repl)
   ("C-x C-a i" . dape-info)))
```
{: data-filename="init.el"}

The `e` and uppercase `R` bindings preserve dape’s `c` (continue) and `r` (restart), including their repeat-map actions.

## 3. Project-level CMake and Clangd configuration

Add `.dir-locals.el` to the project root so the Clangd language server and Emacs compilation command recognise the project:

```elisp
((nil . ((compile-command . "cmake --build build -j")
         (project-compilation-buffer-name-function . project-prefixed-buffer-name)))
 (c++-mode . ((eglot-workspace-configuration
               . (:clangd (:compilationDatabasePath "build"))))))
```
{: data-filename=".dir-locals.el"}

Enable generation of the compilation database (`compile_commands.json`) in CMake:

```cmake
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
```
{: data-filename="CMakeLists.txt"}

## 4. Debugging workflow

The following steps demonstrate debugging a C++ program.

### Step 1: Build

With a source file open, use `C-c c` (`compile`) or `C-x p c` (`project-compile`). Output appears in `*compilation*`. Jump to a reported error with `C-x \`` (`next-error`).

```bash
cmake -B build -DCMAKE_BUILD_TYPE=Debug -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
cmake --build build -j
```

> [!IMPORTANT]
> Build in **Debug** or **RelWithDebInfo** mode to make debugging symbols available.

### Step 2: Set breakpoints

Move to the source line where execution should stop:
- `C-x C-a b` (`dape-breakpoint-toggle`): toggles a breakpoint and displays a red marker at the start of the line.
- `C-x C-a e` (`dape-breakpoint-expression`): adds a conditional breakpoint, for example stopping when a loop counter satisfies `i == 100`.

### Step 3: Start a dape session

- Press `C-x C-a d` (`dape`).
- Choose `lldb-cpp` in the minibuffer.
- Confirm `build/uygulama` when asked for the binary path.

Emacs rearranges the windows into the `gdb` layout:
- Source at the upper left.
- Stack and threads at the upper right.
- Current local variables at the lower right.
- An interactive LLDB command line (`*dape-repl*`) at the bottom.

### Step 4: Inspect variables and step

When execution stops at a breakpoint:
- **Inline values:** current variable values appear as faint text beside the code.
- **Watches:** press `i` in `*dape-info*` to watch an expression such as `dizi.size()`.
- **Single-key stepping (`repeat-mode`):** after the first command, continue with individual letters without repeating the prefix:
  - `n`: step over / next line.
  - `s`: step into a function.
  - `o`: step out of a function.
  - `c`: continue to the next breakpoint.
  - `r`: restart the program.
  - `q`: quit the debugging session.

### Step 5: Use the LLDB REPL

Switch to `*dape-repl*` to inspect a memory address or evaluate a C++ expression:

```text
p my_vector.size()
expr my_vector.push_back(42)
x/16xb pointer_address
```

## Sources and verification environment

- [dape repository and documentation](https://github.com/svaante/dape)
- [LLVM lldb-dap documentation](https://lldb.llvm.org/)
- [GNU Emacs Eglot manual](https://www.gnu.org/software/emacs/manual/html_node/eglot/)

8–9 November 2026: configuration and key/repeat maps were checked in batch Emacs 31.1 with dape 0.19.0 and 0.28.0. No interactive LLDB/DAP session was run.
