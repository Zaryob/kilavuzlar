---
title: Vim key combinations
permalink: /en/vim/vim-tus-kombinasyonlari/
status: duzenlendi
reviewed: 2026-11-02
scope: Vim without plugins; default key mappings.
lang: en
translation_key: guide-vim-vim-tus-kombinasyonlari
translation_of: /vim/vim-tus-kombinasyonlari/
translated: '2026-11-03'
---

# Vim key combinations

Unless stated otherwise, commands are used in normal mode. `Esc` returns to normal mode. `Ctrl+w h` means press Ctrl and w together, then h. `{n}` is a number placeholder, and `{harf}` is a letter of your choice.

## Inserting and selecting

- `i` / `a`: enter insert mode before / after the cursor.
- `I` / `A`: insert at the first nonblank character / end of the line.
- `o` / `O`: open a new line below / above and enter insert mode.
- `v` / `V` / `Ctrl+v`: select characters / lines / a block.
- `Esc`: leave insert or visual mode.

## Movement

- `h`, `j`, `k`, `l`: left, down, up, right.
- `{n}j` / `{n}k`: move down / up n lines.
- `w` / `b` / `e`: next word’s beginning / previous word’s beginning / end of a word.
- `0` / `^` / `$`: line beginning / first nonblank / line end.
- `gg` / `G`: start / end of the file.
- `{n}G` or `:{n}`: go to line n.
- `H` / `M` / `L`: top / middle / bottom screen line.
- `{n}H` / `{n}L`: nth line from the top / bottom of the screen.
- `f{harf}` / `F{harf}`: find the character to the right / left within the line.
- `%`: jump to the matching bracket.
- `Ctrl+e` / `Ctrl+y`: scroll down / up.
- `zt` / `zz` / `zb`: position the cursor’s line at the top / middle / bottom of the screen.

## Marks and returning

- `ma`: save the current position in mark `a`.
- `'a`: go to the first nonblank character of the marked line.
- `` `a ``: go to the exact marked position.
- `''`: return to the line of the previous jump.
- `` `. ``: return to the position of the last change.
- `:marks`: list marks.

## Deleting, copying and changing

- `x` / `X`: delete the character under / before the cursor.
- `dw` / `de` / `db`: delete to the next word’s beginning / word end / previous word’s beginning.
- `dd` / `{n}dd`: delete one / n lines.
- `d^` / `d$` or `D`: delete to the first nonblank / end of the line.
- `d'a`: delete through the marked line, including boundary lines.
- `yy` / `yw` / `ye` / `yb`: yank a line / to the next word’s beginning / word end / previous word’s beginning.
- `yl` / `y^` / `y$`: yank one character / to the first nonblank / to the end of the line.
- `y'a`: yank through the marked line, including boundary lines.
- `p` / `P`: put copied or deleted text after / before the cursor.
- `{n}p`: put n times.
- `r{harf}`: replace one character.
- `R`: enter replace mode.
- `cw` / `ce` / `cb`: change the region selected by the word motion.
- `cc` / `C`: change a whole line / through the end of the line.
- In visual mode, `d` / `c` / `y`: delete / change / yank the selection.

## Undo and repeat

- `u`: undo the last change.
- `Ctrl+r`: redo an undone change.
- `.`: repeat the last change.
- `Ctrl+a` / `Ctrl+x`: increment / decrement the number at or after the cursor.

## Registers and macros

- `"ayy` / `"add`: yank / delete a line into register `a`.
- `"ap`: put register `a`.
- `:registers` or `:reg a`: show all registers / register `a`.
- `qa`: start recording a macro in register `a`; `q` in normal mode stops recording.
- `@a` / `{n}@a`: run the macro once / n times.
- `@@`: repeat the last executed macro.

## Search and substitution

- `/metin` / `?metin`: search forward / backward; press Enter to run the search.
- `n` / `N`: next match in the search direction / opposite direction.
- `*` / `#`: search forward / backward for the word under the cursor.
- `:s/eski/yeni/`: replace the first match on the line.
- `:s/eski/yeni/g`: replace all matches on the line.
- `:%s/eski/yeni/gc`: replace matches throughout the file, confirming each one.
- `q/` / `q?` / `q:`: open forward-search / backward-search / command history; close with `:q`.
- `:set incsearch`: show matches while typing.
- `:set hlsearch` / `:nohlsearch`: highlight matches / clear the current highlights.
- `:set ignorecase`: ignore letter case.

In the default pattern syntax, `^` is the start of a line, `$` its end, `.` one character, `[abc]` a character in the set, and `[^abc]` a character outside it. `*` repeats the preceding item zero or more times; use `.*` for an arbitrary sequence. Pattern behaviour depends on `:set magic?`.

## Indentation, display and completion

- `>>` / `<<`: shift a line right / left.
- `{n}>>`: shift n lines right.
- `:set shiftwidth=4` / `:set tabstop=8`: set indentation width / tab stops.
- `:set number` / `:set nonumber`: show / hide line numbers.
- `:set list` / `:set nolist`: show / hide otherwise invisible characters.
- `~`: toggle character case.
- `ga` or `:ascii`: show the character code.
- `Ctrl+l`: redraw the screen.
- In insert mode, `Ctrl+n` / `Ctrl+p`: select the next / previous word-completion candidate.
- In insert mode, `Ctrl+x Ctrl+o`: complete using the configured `omnifunc`.
- `:TOhtml`: generate syntax-coloured HTML if the relevant runtime plugin is available.

## Folding

- `:set foldmethod=indent`: fold by indentation.
- `zo` / `zc` / `za`: open / close / toggle a fold.
- `zO` / `zC`: open / close the current fold and its nested folds.
- `zR` / `zM`: open / close all folds.
- `zj` / `zk`: move to the next / previous fold.

## Files and shell commands

- `:edit dosya`: open a file.
- `:new dosya`: open a file in a new window.
- `:w` / `:w dosya`: save / write to the named file.
- `:wq` / `:q` / `:q!`: save and quit / quit / quit discarding changes.
- `:r dosya`: insert a file after the current line.
- `:r !komut`: insert command output after the current line.
- `:!komut` / `:shell`: run a shell command / start a temporary shell.
- `:terminal`: open a terminal if supported by the Vim build.
- `:Explore`: open the file browser if netrw is available.
- `:Nread scp://kullanici@sunucu/yol/dosya`: read a remote file with netrw and SSH.
- `:Nwrite scp://kullanici@sunucu/yol/dosya`: write to a remote file with netrw and SSH.

## Buffers, tabs and windows

A buffer is a file’s in-memory contents, a window is a view of a buffer, and a tab page is a window layout.

- `:ls`: list buffers.
- `:bnext` / `:bprevious` / `:buffer {n}`: next / previous / numbered buffer.
- `:bdelete` or `:bdelete {n}`: remove a buffer from the list, warning about unsaved changes.
- `:set hidden`: allow a modified buffer to remain in the background without saving.
- `:tabnew dosya`: open a file in a new tab.
- `gt` / `gT` / `:tabclose`: next tab / previous tab / close the tab.
- `:tabmove {n}`: move the tab after tab n; 0 moves it to the front.
- `:vsplit` / `:split`: split vertically / horizontally.
- `Ctrl+w w` or `Ctrl+w h/j/k/l`: switch windows / move in the indicated direction.
- `Ctrl+w +` / `Ctrl+w -`: increase / decrease window height.
- `Ctrl+w c`: close the window.

## Sources and verification

Incorrect movement, mark, repeat and buffer commands in the original notes were corrected against Vim’s own [motion](https://vimhelp.org/motion.txt.html), [quick reference](https://vimhelp.org/quickref.txt.html), [repeat](https://vimhelp.org/repeat.txt.html) and [window](https://vimhelp.org/windows.txt.html) documentation. Local mappings and build options can change behaviour; see `:help` inside Vim.
