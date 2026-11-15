---
translation_key: guide-emacs-cmake-ve-lldb
lang: tr
title: "Emacs ile CMake ve LLDB kullanmak"
permalink: /emacs/cmake-ve-lldb/
status: duzenlendi
reviewed: 2026-11-14
scope: GNU Emacs 29+ üzerinde Eglot, project.el, compile ve dape ile modern C++ ve lldb-dap hata ayıklama.
---

# Emacs ile CMake ve LLDB kullanmak

Emacs üzerinde C++ geliştirme deneyimi, son yıllarda yerleşik LSP istemcisi `eglot`,
proje yöneticisi `project.el` ve Debug Adapter Protocol (DAP) istemcisi `dape` sayesinde
büyük bir dönüşüm geçirdi. Artık onlarca harici eklenti (`lsp-mode`, `treemacs`, `hydra`,
`dap-mode`) kurmadan, hafif ve yerleşik kütüphanelerle modern bir IDE deneyimi elde etmek mümkündür.

Bu kılavuzda CMake tabanlı bir C++ projesini Emacs içinde yapılandırmayı, derlemeyi ve
LLVM 18+ ile gelen `lldb-dap` aracılığıyla görsel olarak hata ayıklamayı (debugging)
ele alacağız.

## 1. Neden dape ve lldb-dap?

Geçmişte Emacs'te hata ayıklama için iki temel yol bulunuyordu:

1. **GUD**: Köklü bir hata ayıklama arayüzüdür; `gud-lldb` desteği ise Emacs 30 ile eklenmiştir. Dape, terminal çıktısını ayrıştırmak yerine yapılandırılmış DAP protokolünü kullanır.
2. **`dap-mode`**: VS Code hata ayıklama protokolünü Emacs'e getirdi ancak `lsp-mode` ekosistemine sıkı sıkıya bağlıdır ve oldukça ağırdır.

**`dape` (Debug Adapter Protocol for Emacs)**:
- Emacs 29+ ile gelen yerleşik `eglot` ve `project.el` ile tam uyumludur; harici bir LSP paketine ihtiyaç duymaz.
- GDB-MI tarzı temiz, çok pencereli bir bilgi paneli (`*dape-info*`) açar: İş parçacıkları (threads), çağrı yığını (stack trace), yerel değişkenler, izleme listesi (watch) ve breakpoint listesi.
- Kaynak kodun içine doğrudan satır içi değişken değerlerini yazar (`inlay hints`).
- `repeat-mode` desteğiyle tek bir tuşla (`n`, `s`, `c`, `o`) hızlı adımlama sağlar.

> **Not:** LLVM 18 sürümüyle birlikte `lldb-vscode` aracının adı protokolün evrenselliğini
> vurgulamak için resmen **`lldb-dap`** olarak değiştirilmiştir.

## 2. Emacs yapılandırması (`init.el`)

Aşağıdaki yapılandırmayı `~/.emacs.d/init.el` veya `~/.config/emacs/init.el` dosyanıza ekleyin:

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
  ;; Git deposu olmasa dahi kökte duran .dir-locals.el dosyasını proje kökü say.
  ;; CMakeLists.txt işaret olarak kullanılmaz: alt dizinlerde de bulunduğu için
  ;; her alt dizini ayrı proje yapar.
  (add-to-list 'project-vc-extra-root-markers ".dir-locals.el"))

(use-package compile
  :ensure nil
  :custom
  ;; compilation-read-command varsayılan değerinde (t) bırakılır: C-c c komutu
  ;; çalıştırmadan önce gösterir. Sormadan yinelemek için C-c r (recompile) kullanın.
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

`e` ve büyük `R` bağları, dape’in `c` (continue) ve `r` (restart) tuşlarını ve repeat-map davranışlarını korur.

> **Uyarı:** `compilation-read-command` değişkenini `nil` yapmayın. Emacs belgesinin de belirttiği gibi bu durumda
> `compile`, bir dosyanın ya da `.dir-locals.el` dosyasının tanımladığı `compile-command` değerini size göstermeden
> çalıştırır; indirdiğiniz bir depo bu yolla keyfi komut çalıştırabilir. Varsayılan değerde komut önce minibuffer'da görünür.

Proje kökü işareti olarak `CMakeLists.txt` yerine `.dir-locals.el` kullanılır: `project.el` en yakın işareti kök sayar ve
alt dizinlerinde de `CMakeLists.txt` bulunan bir projede her alt dizin ayrı proje olurdu. Git deposu içinde bu ayara gerek yoktur.

## 3. Proje düzeyinde CMake ve Clangd ayarları

Emacs derleme komutunun projeyi tanıması için proje köküne `.dir-locals.el` ekleyebilirsiniz:

```elisp
((nil . ((compile-command . "cmake --build build -j")
         (project-compilation-buffer-name-function . project-prefixed-buffer-name))))
```
{: data-filename=".dir-locals.el"}

Clangd için ayrıca bir ayar gerekmez: `compile_commands.json` dosyasını düzenlediğiniz dosyanın üst dizinlerinde ve bu
dizinlerin `build/` alt dizinlerinde kendisi arar. Derleme dizininiz başka bir addaysa `init.el` içindeki clangd
argümanlarına `"--compile-commands-dir=<dizin>"` ekleyin ya da proje köküne `CompileFlags: {CompilationDatabase: <dizin>}`
içeren bir `.clangd` dosyası koyun. `eglot-workspace-configuration` ile gönderilen `compilationDatabasePath` işe yaramaz;
clangd bu alanı yalnızca `initializationOptions` içinde okur.

CMake yapılandırmanızda derleme veritabanını (`compile_commands.json`) üretmeyi unutmayın:

```cmake
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
```
{: data-filename="CMakeLists.txt"}

## 4. Hata ayıklama iş akışı

Örnek bir C++ programında adım adım hata ayıklama süreci:

### 1. Adım: Derleme

Kaynak dosya açıkken `C-c c` (`compile`) veya `C-x p c` (`project-compile`) tuşlayın.
Derleme çıktısı `*compilation*` penceresinde akar. Hata varsa ``C-x ` `` (`next-error`) ile
hatalı satıra atlayabilirsiniz.

```bash
cmake -B build -DCMAKE_BUILD_TYPE=Debug -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
cmake --build build -j
```

> **Önemli:** Hata ayıklama sembollerinin tam görünmesi için projenin **Debug** veya **RelWithDebInfo**
> modunda derlenmiş olması gerekir.

### 2. Adım: Breakpoint (Kesme Noktası) Koyma

Kaynak kodda duraklamak istediğiniz satıra gelin:
- `C-x C-a b` (`dape-breakpoint-toggle`): O satıra kesme noktası koyar. Satır başında kırmızı bir gösterge belirir.
- `C-x C-a e` (`dape-breakpoint-expression`): Koşullu kesme noktası ekler (örneğin döngü sayacı `i == 100` olduğunda dur).

### 3. Adım: Dape Oturumunu Başlatma

- `C-x C-a d` (`dape`) tuşlayın.
- Minibuffer'da `lldb-cpp` yapılandırmasını seçin.
- İkili dosya yolu sorulduğunda `build/uygulama` dosyasını onaylayın.

Emacs otomatik olarak pencereleri yeniden düzenler (`gdb` düzeni):
- Sol üstte kaynak kodunuz.
- Sağ üstte çağrı yığını (Stack) ve iş parçacıkları (Threads).
- Sağ altta yerel değişkenlerin anlık değerleri (Locals).
- Alt kısımda etkileşimli LLDB komut satırı (`*dape-repl*`).

### 4. Adım: Değişkenleri İnceleme ve Adımlama

Program breakpoint satırında durduğunda:
- **Satır İçi Değerler:** Değişkenlerin güncel değerleri doğrudan kodun sağında silik metin olarak görünür.
- **İzleme (Watch):** `C-x C-a w` (`dape-watch-dwim`) ile bir ifadeyi (örneğin `dizi.size()`) izleme listesine ekleyin; ifade `*dape-info*` penceresinin Watch bölümünde her duraklamada yeniden hesaplanır. Aynı komut, listedeki bir ifadeyi kaldırmak için de kullanılır.
- **Tek Tuşla Adımlama (`repeat-mode`):** İlk adımdan sonra ön ek tuşuna basmadan sadece tek harflere basarak ilerleyin:
  - `n` : Sonraki satıra geç (Step Over / Next)
  - `s` : Fonksiyonun içine gir (Step Into)
  - `o` : Fonksiyondan çık (Step Out)
  - `c` : Bir sonraki kesme noktasına kadar devam et (Continue)
  - `r` : Programı baştan başlat (Restart)
  - `q` : Hata ayıklama oturumunu kapat (Quit)

### 5. Adım: LLDB REPL Kullanımı

Özel bir bellek adresini dökmek veya C++ ifadesi çalıştırmak istediğinizde `*dape-repl*`
penceresine geçin:

```text
p my_vector.size()
expr my_vector.push_back(42)
x/16xb pointer_address
```

## Kaynaklar ve doğrulama ortamı

- [Dape Resmi Deposu ve Belgeleri](https://github.com/svaante/dape)
- [LLVM lldb-dap Dokümantasyonu](https://lldb.llvm.org/)
- [GNU Emacs Eglot Kullanım Kılavuzu](https://www.gnu.org/software/emacs/manual/html_node/eglot/)
- [clangd: proje kurulumu ve `compile_commands.json` araması](https://clangd.llvm.org/installation#project-setup)
- [clangd protokol eklentileri: `compilationDatabasePath`](https://clangd.llvm.org/extensions#compilation-commands)

8–9 Kasım 2026: yapılandırma ve tuş/repeat haritaları Emacs 31.1 batch modunda dape 0.19.0 ve 0.28.0 ile kontrol edildi. Etkileşimli LLDB/DAP oturumu çalıştırılmadı.

14 Kasım 2026: güncellenen `init.el` Emacs 31.1 batch modunda dape 0.27.1 ile yüklendi; `C-x C-a w` bağının `dape-watch-dwim` olduğu, `.dir-locals.el` işaretinin alt dizinden proje kökünü bulduğu ve `compilation-read-command` `nil` iken `compile-command` değerinin güvensiz sayıldığı kontrol edildi.
