# Spider IDE
russian: 

**Spider IDE** — IDE на PyQt6 для собственного языка **Spider**
с GUI-конструктором поверх Tkinter. Минималистичный интерфейс (сетка на фоне редактора,
миникарта, сворачивание кода, live-отладка) плюс интерпретатор, который позволяет
собирать оконные приложения одной строкой на команду.

> Автор: project.exe и spider team · Версия языка: **2.0** · Версия IDE: **3.0 Alpha**
---

## Особенности

### IDE
- **Бруталистский UI**: чёрная/белая сетка фона, моноширинный шрифт, нулевые скругления,
  инвертированные ховеры. Две темы — `brutal` (тёмная) и `light` (светлая), переключение
  на лету через *Settings → Appearance*.
- **Редактор**: подсветка синтаксиса Spider, автодополнение (встроенные + динамически
  найденные `var`/`func`), сниппеты по Tab, авто-закрытие скобок/кавычек,
  отступы на новой строке, сворачивание блоков, миникарта с цветными полосами кода,
  колонка номеров строк с иконками fold.
- **Анализ**: встроенный линтер (неизвестные команды, незакрытые строки/скобки),
  панель **PROBLEMS**, панель **VARIABLES** со static-analysis и live-значениями
  при отладке (JSON-канал `.spider_debug.json`).
- **Вкладки**: несколько файлов, сплит-вью (`Ctrl+\`), welcome-экран, недавние файлы.
- **Вывод**: консоль OUTPUT с цветовой разметкой, интерактивный терминал,
  find & replace (`Ctrl+F`), статус-бар (LN/COL, кодировка, RAM через `psutil`).

### Язык Spider
- Построчная модель: каждая строка — одна команда `имя(параметры)`.
- GUI-конструктор: `window`, `text`, `button`, `shape`, `input`, `checkbox`,
  `slider`, `dropdown`, `image` и др.
- Реактивность: `textv` привязывает текст к переменной и обновляется сам;
  события `on(...)` и горячие клавиши `bind(...)`.
- Вычисления: арифметика, сравнения, логика, списки с индексами/срезами,
  строковые методы и конкатенация.
- Переносимость: скрипт `.spider` исполняется и из IDE, и отдельным `spider_runtime.exe`.

---

## Быстрый старт

### Из исходников (нужен Python 3.10+)
```powershell
pip install PyQt6 psutil
py run.py
```
Откроется IDE. Создайте файл (**+ FILE**), напишите скрипт (см. [Язык Spider](#язык-spider))
и нажмите **RUN** (или `F5`). Вывод — в панели OUTPUT, окно приложения — отдельным Tkinter-окном.

### Готовый `.exe` (без установки Python)
Распакуйте архив сборки → запустите `SpiderIDE\SpiderIDE.exe`.
Внутри папки лежат два файла — это нормально, см. [Сборка](#сборка-из-исходников):
```
SpiderIDE\
├── SpiderIDE.exe        ← сама IDE (оконный режим, без консоли)
├── spider_runtime.exe   ← интерпретатор языка (запускается IDE при RUN)
└── _internal\           ← зависимости Qt / Tkinter / Python
```
IDE при **RUN** поднимает `spider_runtime.exe` как дочерний процесс и читает его stdout.

---

## Сборка из исходников

Сборка описана в `SpiderIDE.spec` и намеренно делает **два** исполняемых файла:

| Артефакт | Режим | Зачем |
|---|---|---|
| `SpiderIDE.exe` | `console=False` (windowed) | GUI не должен показывать чёрное окно |
| `spider_runtime.exe` | `console=True` + `CREATE_NO_WINDOW` при запуске | рантайму нужен живой `stdout` для PIPE из IDE, но окно консоли прячется флагом |

> Почему не один `.exe`: GUI, собранный windowed, не может выступать Python-интерпретатором
> (`sys.executable` указывает на сам GUI-экзешник), а windowed-дочерний процесс теряет
> `stdout`. Поэтому язык вынесен в отдельный консольный рантайм, который IDE запускает
> с подавлением окна. Это архитектурное решение, а не недоработка.

Команда сборки (из корня проекта):
```powershell
py -m PyInstaller --clean --noconfirm --distpath .\out SpiderIDE.spec
```
Результат — `.\out\SpiderIDE\` с обоими `.exe`. Перед сборкой убедитесь, что
`SpiderIDE.exe` / `spider_runtime.exe` не запущены (иначе `dist` будет занят и
`COLLECT` упадёт с `PermissionError`):
```powershell
Get-Process SpiderIDE, spider_runtime -ErrorAction SilentlyContinue | Stop-Process -Force
```

Зависимости для сборки: `pyinstaller`, `pillow` (для генерации `assets/app.ico` из PNG).

---

## Язык Spider

### Минимальная программа
Первая строка обязательна — `Spider(Start)`. Строка `End` в конце допустима как
визуальный маркер (IDE-шаблон подставляет её), но рантайм её игнорирует:
```spider
Spider(Start)
window(title = "Hello", width = 400, height = 200, bg = "#ffffff")
text(text = "Привет, Spider!", x = 20, y = 20, color = "#000000", size = 18)
print("запустилось")
```

### Команды

| Команда | Назначение | Ключевые параметры |
|---|---|---|
| `window` | создать окно (однократно) | `title, width, height, bg` |
| `text` | статичный текст на canvas | `text, x, y, color, size` |
| `textv` | текст, привязанный к переменной (обновляется сам) | `var, x, y, color, size` |
| `button` | кнопка с действием | `id, text, x, y, width, height, bg, color, action` |
| `shape` | прямоугольник/круг на canvas | `id, type=square\|circle, x, y, color, size` |
| `move` | сдвинуть элемент по `id` | `id, x, y` (поддерживает `+N` / `-N` / абсолют) |
| `input` | поле ввода | `id, placeholder, x, y, width` |
| `checkbox` | флажок (значение → в переменную по `id`) | `id, text, value, x, y` |
| `slider` | слайдер (значение → в переменную по `id`) | `id, from, to, value, step, orient, x, y` |
| `dropdown` | выпадающий список (значение → в переменную) | `id, options="a,b,c", value, width, x, y` |
| `image` | картинка PNG/GIF | `id, file, x, y` |
| `var` | создать/изменить переменную | `var(имя=значение)` **или** `var(name=…, value=…)` |
| `print` | вывод в OUTPUT | `print(значение)` или `print(text=…)` |
| `title` | заголовок-раздел в OUTPUT | `title("…")` |
| `check` | условное ветвление | `what=условие, yes=действие, no=действие` |
| `wait` | планировщик задержки | `time=сек` (см. ограничения) |
| `bind` | горячая клавиша → действие | `key=…, action=…` |
| `on` | событие виджета → действие | `id=…, event=…, action=…` |
| `clear` | очистить canvas | — |

### Значения: арифметика, сравнения, логика
Пробелы вокруг `=` и операторов разрешены. Неизвестное имя или непарсящееся выражение
не роняет скрипт — оно возвращается как строка (graceful fallback).
```spider
var(a = 10)
var(b = 3)
var(sum = a + b)        # 13
var(pow = a ** b)       # 1000
var(mod = a % b)        # 1
var(big = a > b)        # True
var(ok  = big and a == 10)
var(no  = not ok)
check(what = a > 5, yes = print(Больше), no = print(Меньше))
```

### Списки и строки
```spider
var(scores = [10, 20, 30, 40, 50])
var(first = scores[0])     # 10
var(last  = scores[-1])    # 50
var(mid   = scores[1:4])   # [20, 30, 40]

var(name = "Spider")
var(up   = name.upper())               # SPIDER
var(hi   = "Hi " + name)               # Hi Spider   (литерал + переменная)
var(n    = len(name))                  # 6
var(rep  = name.replace("Spider", "Python"))
```

### События и реакции
`action` в `on`/`button`/`check` — это **любая строка-команда**; она исполняется полным
диспетчером, поэтому внутри можно писать `var(...)`, `print(...)`, `move(...)` и т.д.
```spider
var(score = 0)
text(text = "Score:", x = 20, y = 40)
textv(var = score, x = 80, y = 40)
button(id = plus, text = "+1", x = 20, y = 70)
on(id = plus, event = click, action = "var(score = score + 1)")
on(id = plus, event = click, action = "check(what = score >= 3, yes = print(Победа), no = print(Ещё))")
```

Поддерживаемые `event`: `click, dblclick, rightclick, keypress, keydown, keyup,
hover, enter, leave, motion, focus_in, focus_out, submit, change`.

Семантика `change`:
- `slider` / `checkbox` / `dropdown` — срабатывает при **изменении значения**;
- `input` — при **потере фокуса** или нажатии **Enter** (не по каждой клавише).

`bind` понимает алиасы клавиш Tk: `Enter→Return`, `Esc→Escape`, `Up/Down/Left/Right`,
`Space, Tab, BackSpace, Delete, Home, End, PageUp→Prior, PageDown→Next`, а также
одиночные символы (`r`, `c`, …).
```spider
bind(key = Enter, action = print(Enter нажат))
bind(key = r,     action = "var(score = 0)")
```

### Отладка и вывод
- `print` / `title` пишут в панель OUTPUT IDE (или в консоль при запуске рантайма напрямую).
- При **DEBUG** рантайм сбрасывает live-состояние переменных в `.spider_debug.json`,
  которое IDE показывает в панели **VARIABLES**.

### Ограничения синтаксиса (важно)
Spider 1.4 — **построчный** язык без блоков и областей видимости. Отсюда:
- Нет `{ }`, `if/else`-тел, функций с телом, циклов с блоком — только однострочные
  `check(...)` и события. (Полноценные блоки/функции — это переход на AST, см. Roadmap.)
- Выражения внутри значений пишите **без кавычек в середине** и помните про fallback:
  конкатенация двух строковых *литералов* (`"a" + "b"`) требует актуального `values.py`
  с функцией `_is_single_string_literal`; конструкция `литерал + переменная`
  (`"Hi " + name`) работает всегда.
- `wait(time=…)` в построчной модели лишь планирует задержку через Tk-цикл и **не
  приостанавливает** следующие строки — это не «пауза исполнения».
- Комментарии (`#`, `//`) безопасны даже со скобками внутри (парсер берёт первую
  балансирующую `)`).

---

## Архитектура проекта

```
SpiderIDE_1.2/
├── run.py                     # точка входа IDE (sys.path + запуск spider_ide.main)
├── SpiderIDE.spec             # PyInstaller: собирает SpiderIDE.exe + spider_runtime.exe
├── assets/                    # little_logo.png, app.ico, …
├── spider_ide/                # ── ПАКЕТ IDE (PyQt6) ──
│   ├── main.py                #   сборка QApplication, splash, главное окно
│   ├── core/
│   │   ├── config.py          #   конфиг/темы/недавние файлы (%USERPROFILE%\.spider_ide)
│   │   ├── editor.py          #   SpiderEditor, LineNumberArea, Minimap, FindReplace,
│   │   │                      #   CompletionPopup, EditorContainer
│   │   ├── syntax.py          #   SpiderSyntaxHighlighter (подсветка)
│   │   ├── code_folding.py    #   CodeFoldingManager (сворачивание)
│   │   └── runner.py          #   Runner: запуск spider_runtime.exe, чтение stdout
│   └── ui/
│       ├── style_kit.py       #   темы DARK/LIGHT, сетка-фон, mono(), виджеты-хелперы
│       ├── main_window.py     #   MainWindow: меню, тулбар, вкладки, сплит, статус-бар
│       ├── tabs.py            #   BrutalistTabBar (кастомные вкладки)
│       ├── sidebar.py         #   проводник файлов
│       ├── console.py         #   OUTPUT / PROBLEMS
│       ├── terminal.py        #   интерактивный терминал
│       ├── settings_dialog.py #   переключатель тем/настроек
│       ├── splash_screen.py   #   заставка
│       └── …                  #   help/welcome/open/project_search/dialogs
└── spider_runtime/            # ── ПАКЕТ ЯЗЫКА (Tkinter) ──
    ├── spider.py              #   CLI-точка входа: читает .spider, гоняет строки
    ├── parser.py              #   regex/сканер: extract_command, parse_params, parse_action
    ├── values.py              #   движок значений: evaluate / unwrap_literal (песочница)
    ├── executor.py            #   SpiderExecutor: dispatch cmd_* + tkinter-действия
    ├── widgets.py             #   WidgetMixin: input/checkbox/slider/dropdown/image/on
    ├── vars.py                #   SpiderVars: плоское хранилище + автоконверсия типов
    └── errors.py              #   SpiderError: реестр кодов ошибок
```

**Пайплайн исполнения одной строки:**
```
строка → parser.extract_command / extract_params_string
       → parser.parse_params            (сырые строки значений)
       → executor._dispatch             (маршрутизация по имени команды)
       → executor.cmd_<имя>             → values.evaluate(значение) → tkinter-действие
```
IDE и рантайм связаны процессом: `runner.py` поднимает `spider_runtime.exe`,
пишет ему путь к файлу и читает stdout построчно, раскрашивая OUTPUT.

---

## Как расширить язык (чеклист «5 мест»)

Новая конструкция должна появиться **синхронно** в пяти точках, иначе получится
рассинхрон «IDE обещает — рантайм падает» (или наоборот):

1. **`spider_runtime/parser.py`** — разбор новой формы/параметров (если нужна новая
   синтаксическая конструкция, а не просто новая команда).
2. **`spider_runtime/executor.py`** — метод `cmd_<имя>` + ветка в `_dispatch`.
3. **`spider_runtime/values.py` / `vars.py`** — новые типы значений / встроенные функции
   в `_SAFE_BUILTINS` / ключи в `_BOOL_LITERALS`.
4. **`spider_ide/core/syntax.py`** — подсветка нового ключевого слова/команды.
5. **`spider_ide/core/editor.py`** — `self.completions`, `self.snippets` и
   `known_commands` в линтере (иначе автодополнения не будет, а линтер сыплет
   «Unknown command»).

Плюс опционально документация в `help_dialog` / `welcome_dialog`.

---

## Диагностика «чист ли диск» (перед сборкой)

Главный источник багов в этом проекте — рассинхрон версий модулей (частичное применение
правок). Быстрая проверка состояния дисковых файлов без запуска GUI:

```powershell
$rt = ".\spider_runtime"
function has($l,$p,$f){ "{0,-22} {1}" -f $l, $(if((Select-String -Path $f -Pattern $p -SimpleMatch -Quiet)){"PASS"}else{"FAIL"}) }
function no ($l,$p,$f){ "{0,-22} {1}" -f $l, $(if((Select-String -Path $f -Pattern $p -SimpleMatch -Quiet)){"FAIL"}else{"PASS"}) }
has "parser: cmd-arg"   "def parse_params(param_str, cmd=None):" "$rt\parser.py"
has "parser: skip-sp"   "while k >= 0 and s[k] in"               "$rt\parser.py"
has "parser: balanced)" "return line[start + 1:i]"               "$rt\parser.py"
no  "parser: no rfind"  "rfind(')')"                             "$rt\parser.py"
has "exec: mixin"       "class SpiderExecutor(WidgetMixin):"     "$rt\executor.py"
has "exec: place"       "self.canvas.place"                      "$rt\executor.py"
no  "exec: no pack"     "self.canvas.pack"                       "$rt\executor.py"
has "exec: key-alias"   "aliases"                                "$rt\executor.py"
has "widgets: mixin"    "class WidgetMixin:"                     "$rt\widgets.py"
has "widgets: changeQ"  "_change_actions"                        "$rt\widgets.py"
```
Все строки должны быть **PASS** (для `no …` — тоже PASS, т.е. запрещённый маркер отсутствует).
Если есть FAIL — правка не дошла до диска; пересобирать бессмысленно, сначала чините файл.

---

## Темы и настройки

- Переключение: *Settings → Appearance → `brutal` / `light` → Save & Close*.
- Тема применяется ко всему UI синхронно: вкладки, сайдбар, редактор (сетка-фон),
  колонка номеров, миникарта, консоль, find/replace, диалоги.
- Конфиг и недавние файлы хранятся в `%USERPROFILE%\.spider_ide\` — переживают перезапуск.

---

## Roadmap / известное

- **Закрыто в 1.4**: новые виджеты (`input/checkbox/slider/dropdown/image`), события
  (`on` + алиасы `bind`), арифметика/сравнения/логика, списки/срезы/индексы,
  строковые операции, устойчивость рантайма к ошибкам (catch-all без обрыва),
  корректный разбор пробелов вокруг `=` и комментариев со скобками,
  семантика `change` без спама и затирания значений.
- **Следующий крупный шаг (развилка)**: переход на AST — блоки `{ }`, функции `func`,
  циклы `for/while` с телом, области видимости. Это фактически новый рантайм и потребует
  синхронной переделки подсветки/сниппетов/линтера.
- **Косметика**: строгий режим ошибок вместо graceful-fallback (флаг в `values.evaluate`);
  нормальные таймеры/анимации вместо «псевдо-`wait`».

---

## автор

Проект: **Spider IDE** · Язык: **Spider** · Автор: **project.exe и spider team** 

english: 

# Spider IDE

**Spider IDE** is a PyQt6-based IDE for the custom **Spider** language with a
Tkinter-based GUI constructor. A minimalist interface (grid background in the editor,
minimap, code folding, live debugging) plus an interpreter that lets you build windowed
applications one command per line.

> Author: project.exe and the Spider team · Language version: **2.0** · IDE version: **3.0 Alpha**

---

## Features

### IDE
- **Brutalist UI**: black/white grid background, monospaced font, zero corner rounding,
  inverted hovers. Two themes — `brutal` (dark) and `light` — switched live via
  *Settings → Appearance*.
- **Editor**: Spider syntax highlighting, autocompletion (built-in + dynamically
  discovered `var`/`func`), Tab snippets, auto-closing of brackets/quotes, indentation on
  a new line, block folding, minimap with colored code bands, line-number column with
  fold icons.
- **Analysis**: built-in linter (unknown commands, unterminated strings/brackets),
  **PROBLEMS** panel, **VARIABLES** panel with static analysis and live values during
  debugging (JSON channel `.spider_debug.json`).
- **Tabs**: multiple files, split view (`Ctrl+\`), welcome screen, recent files.
- **Output**: OUTPUT console with color markup, interactive terminal, find & replace
  (`Ctrl+F`), status bar (LN/COL, encoding, RAM via `psutil`).

### The Spider language
- Line-by-line model: every line is one command `name(parameters)`.
- GUI constructor: `window`, `text`, `button`, `shape`, `input`, `checkbox`,
  `slider`, `dropdown`, `image`, etc.
- Reactivity: `textv` binds text to a variable and updates itself; `on(...)` events and
  `bind(...)` hotkeys.
- Computation: arithmetic, comparisons, logic, lists with indexes/slices, string methods
  and concatenation.
- Portability: a `.spider` script runs both from the IDE and from the standalone
  `spider_runtime.exe`.

---

## Quick start

### From source (Python 3.10+ required)
```powershell
pip install PyQt6 psutil
py run.py
```
The IDE opens. Create a file (**+ FILE**), write a script (see
[The Spider language](#the-spider-language)) and press **RUN** (or `F5`). Output goes to
the OUTPUT panel; the application window appears as a separate Tkinter window.

### Ready-made `.exe` (no Python installation required)
Unpack the build archive → run `SpiderIDE\SpiderIDE.exe`. Two files sit inside the folder
— this is expected, see [Building from source](#building-from-source):
```
SpiderIDE\
├── SpiderIDE.exe        ← the IDE itself (windowed mode, no console)
├── spider_runtime.exe   ← the language interpreter (launched by the IDE on RUN)
└── _internal\           ← Qt / Tkinter / Python dependencies
```
On **RUN** the IDE spawns `spider_runtime.exe` as a child process and reads its stdout.

---

## Building from source

The build is described in `SpiderIDE.spec` and intentionally produces **two** executables:

| Artifact | Mode | Why |
|---|---|---|
| `SpiderIDE.exe` | `console=False` (windowed) | the GUI must not show a black console window |
| `spider_runtime.exe` | `console=True` + `CREATE_NO_WINDOW` at launch | the runtime needs a live `stdout` for the IDE's PIPE, but its console window is hidden via the flag |

> Why not a single `.exe`: a windowed-built GUI cannot act as a Python interpreter
> (`sys.executable` points at the GUI executable itself), and a windowed child process
> loses its `stdout`. That is why the language is split out into a separate console
> runtime that the IDE launches with the window suppressed. This is an architectural
> decision, not an oversight.

Build command (from the project root):
```powershell
py -m PyInstaller --clean --noconfirm --distpath .\out SpiderIDE.spec
```
Result — `.\out\SpiderIDE\` with both `.exe` files. Before building, make sure
`SpiderIDE.exe` / `spider_runtime.exe` are not running (otherwise `dist` stays locked and
`COLLECT` fails with `PermissionError`):
```powershell
Get-Process SpiderIDE, spider_runtime -ErrorAction SilentlyContinue | Stop-Process -Force
```
Build dependencies: `pyinstaller`, `pillow` (to generate `assets/app.ico` from the PNG).

---

## The Spider language

### Minimal program
The first line is mandatory — `Spider(Start)`. A trailing `End` line is allowed as a
visual marker (the IDE template inserts it), but the runtime ignores it:
```spider
Spider(Start)
window(title = "Hello", width = 400, height = 200, bg = "#ffffff")
text(text = "Hello, Spider!", x = 20, y = 20, color = "#000000", size = 18)
print("started")
```

### Commands

| Command | Purpose | Key parameters |
|---|---|---|
| `window` | create the window (once) | `title, width, height, bg` |
| `text` | static text on the canvas | `text, x, y, color, size` |
| `textv` | text bound to a variable (auto-updates) | `var, x, y, color, size` |
| `button` | button with an action | `id, text, x, y, width, height, bg, color, action` |
| `shape` | rectangle/circle on the canvas | `id, type=square\|circle, x, y, color, size` |
| `move` | move an element by `id` | `id, x, y` (supports `+N` / `-N` / absolute) |
| `input` | text input field | `id, placeholder, x, y, width` |
| `checkbox` | checkbox (value → variable keyed by `id`) | `id, text, value, x, y` |
| `slider` | slider (value → variable keyed by `id`) | `id, from, to, value, step, orient, x, y` |
| `dropdown` | drop-down list (value → variable) | `id, options="a,b,c", value, width, x, y` |
| `image` | PNG/GIF image | `id, file, x, y` |
| `var` | create/modify a variable | `var(name=value)` **or** `var(name=…, value=…)` |
| `print` | output to OUTPUT | `print(value)` or `print(text=…)` |
| `title` | section header in OUTPUT | `title("…")` |
| `check` | conditional branch | `what=condition, yes=action, no=action` |
| `wait` | delay scheduler | `time=seconds` (see limitations) |
| `bind` | hotkey → action | `key=…, action=…` |
| `on` | widget event → action | `id=…, event=…, action=…` |
| `clear` | clear the canvas | — |

### Values: arithmetic, comparisons, logic
Spaces around `=` and operators are allowed. An unknown name or an unparseable expression
does not crash the script — it is returned as a string (graceful fallback).
```spider
var(a = 10)
var(b = 3)
var(sum = a + b)        # 13
var(pow = a ** b)       # 1000
var(mod = a % b)        # 1
var(big = a > b)        # True
var(ok  = big and a == 10)
var(no  = not ok)
check(what = a > 5, yes = print(More), no = print(Less))
```

### Lists and strings
```spider
var(scores = [10, 20, 30, 40, 50])
var(first = scores[0])     # 10
var(last  = scores[-1])    # 50
var(mid   = scores[1:4])   # [20, 30, 40]

var(name = "Spider")
var(up   = name.upper())               # SPIDER
var(hi   = "Hi " + name)               # Hi Spider   (literal + variable)
var(n    = len(name))                  # 6
var(rep  = name.replace("Spider", "Python"))
```

### Events and reactions
`action` in `on`/`button`/`check` is **any command line**; it is executed by the full
dispatcher, so you can write `var(...)`, `print(...)`, `move(...)`, etc. inside it.
```spider
var(score = 0)
text(text = "Score:", x = 20, y = 40)
textv(var = score, x = 80, y = 40)
button(id = plus, text = "+1", x = 20, y = 70)
on(id = plus, event = click, action = "var(score = score + 1)")
on(id = plus, event = click, action = "check(what = score >= 3, yes = print(Win), no = print(Keep going))")
```

Supported `event` values: `click, dblclick, rightclick, keypress, keydown, keyup,
hover, enter, leave, motion, focus_in, focus_out, submit, change`.

`change` semantics:
- `slider` / `checkbox` / `dropdown` — fires when the **value changes**;
- `input` — on **focus loss** or pressing **Enter** (not on every keystroke).

`bind` understands Tk key aliases: `Enter→Return`, `Esc→Escape`, `Up/Down/Left/Right`,
`Space, Tab, BackSpace, Delete, Home, End, PageUp→Prior, PageDown→Next`, plus single
characters (`r`, `c`, …).
```spider
bind(key = Enter, action = print(Enter pressed))
bind(key = r,     action = "var(score = 0)")
```

### Debugging and output
- `print` / `title` write to the IDE's OUTPUT panel (or to the console when the runtime is
  launched directly).
- In **DEBUG** mode the runtime dumps live variable state to `.spider_debug.json`, which
  the IDE shows in the **VARIABLES** panel.

### Syntax limitations (important)
Spider 1.4 is a **line-by-line** language with no blocks and no scopes. Hence:
- No `{ }`, no `if/else` bodies, no functions with a body, no loops with a block — only
  single-line `check(...)` and events. (Full blocks/functions require the AST migration,
  see Roadmap.)
- Write expressions inside values **without quotes in the middle**, and remember the
  fallback: concatenating two string *literals* (`"a" + "b"`) requires an up-to-date
  `values.py` containing `_is_single_string_literal`; the `literal + variable` form
  (`"Hi " + name`) always works.
- `wait(time=…)` in the line-by-line model only schedules a delay through the Tk loop and
  does **not** pause the following lines — it is not an "execution pause".
- Comments (`#`, `//`) are safe even with parentheses inside them (the parser takes the
  first balanced `)`).

---

## Project architecture

```
SpiderIDE_1.2/
├── run.py                     # IDE entry point (sys.path + launching spider_ide.main)
├── SpiderIDE.spec             # PyInstaller: builds SpiderIDE.exe + spider_runtime.exe
├── assets/                    # little_logo.png, app.ico, …
├── spider_ide/                # ── IDE PACKAGE (PyQt6) ──
│   ├── main.py                #   QApplication assembly, splash, main window
│   ├── core/
│   │   ├── config.py          #   config/themes/recent files (%USERPROFILE%\.spider_ide)
│   │   ├── editor.py          #   SpiderEditor, LineNumberArea, Minimap, FindReplace,
│   │   │                      #   CompletionPopup, EditorContainer
│   │   ├── syntax.py          #   SpiderSyntaxHighlighter (syntax highlighting)
│   │   ├── code_folding.py    #   CodeFoldingManager (code folding)
│   │   └── runner.py          #   Runner: launches spider_runtime.exe, reads its stdout
│   └── ui/
│       ├── style_kit.py       #   DARK/LIGHT themes, grid background, mono(), widget helpers
│       ├── main_window.py     #   MainWindow: menu, toolbar, tabs, split view, status bar
│       ├── tabs.py            #   BrutalistTabBar (custom tabs)
│       ├── sidebar.py         #   file explorer
│       ├── console.py         #   OUTPUT / PROBLEMS
│       ├── terminal.py        #   interactive terminal
│       ├── settings_dialog.py #   theme/settings switcher
│       ├── splash_screen.py   #   splash screen
│       └── …                  #   help/welcome/open/project_search/dialogs
└── spider_runtime/            # ── LANGUAGE PACKAGE (Tkinter) ──
    ├── spider.py              #   CLI entry point: reads .spider, runs its lines
    ├── parser.py              #   regex/scanner: extract_command, parse_params, parse_action
    ├── values.py              #   value engine: evaluate / unwrap_literal (sandboxed)
    ├── executor.py            #   SpiderExecutor: cmd_* dispatch + tkinter actions
    ├── widgets.py             #   WidgetMixin: input/checkbox/slider/dropdown/image/on
    ├── vars.py                #   SpiderVars: flat store + automatic type coercion
    └── errors.py              #   SpiderError: error-code registry
```

**Execution pipeline for a single line:**
```
line → parser.extract_command / extract_params_string
     → parser.parse_params            (raw value strings)
     → executor._dispatch             (routing by command name)
     → executor.cmd_<name>            → values.evaluate(value) → tkinter action
```
The IDE and the runtime are linked by a process: `runner.py` spawns `spider_runtime.exe`,
writes it the file path, and reads its stdout line by line, coloring the OUTPUT panel.

---

## Extending the language (the "5 places" checklist)

A new construct must appear **synchronously** in five places, otherwise you get the
"IDE promises — runtime crashes" desync (or the reverse):

1. **`spider_runtime/parser.py`** — parsing of the new form/parameters (only if a new
   syntactic construct is needed, not merely a new command).
2. **`spider_runtime/executor.py`** — a `cmd_<name>` method + a branch in `_dispatch`.
3. **`spider_runtime/values.py` / `vars.py`** — new value types / built-in functions in
   `_SAFE_BUILTINS` / keys in `_BOOL_LITERALS`.
4. **`spider_ide/core/syntax.py`** — highlighting of the new keyword/command.
5. **`spider_ide/core/editor.py`** — `self.completions`, `self.snippets`, and
   `known_commands` in the linter (otherwise there is no autocompletion and the linter
   spams "Unknown command").

Plus, optionally, documentation in `help_dialog` / `welcome_dialog`.

---

## Diagnostics: is the disk clean? (before building)

The main source of bugs in this project is module-version desync (partially applied
edits). A quick check of the on-disk file state without launching the GUI:

```powershell
$rt = ".\spider_runtime"
function has($l,$p,$f){ "{0,-22} {1}" -f $l, $(if((Select-String -Path $f -Pattern $p -SimpleMatch -Quiet)){"PASS"}else{"FAIL"}) }
function no ($l,$p,$f){ "{0,-22} {1}" -f $l, $(if((Select-String -Path $f -Pattern $p -SimpleMatch -Quiet)){"FAIL"}else{"PASS"}) }
has "parser: cmd-arg"   "def parse_params(param_str, cmd=None):" "$rt\parser.py"
has "parser: skip-sp"   "while k >= 0 and s[k] in"               "$rt\parser.py"
has "parser: balanced)" "return line[start + 1:i]"               "$rt\parser.py"
no  "parser: no rfind"  "rfind(')')"                             "$rt\parser.py"
has "exec: mixin"       "class SpiderExecutor(WidgetMixin):"     "$rt\executor.py"
has "exec: place"       "self.canvas.place"                      "$rt\executor.py"
no  "exec: no pack"     "self.canvas.pack"                       "$rt\executor.py"
has "exec: key-alias"   "aliases"                                "$rt\executor.py"
has "widgets: mixin"    "class WidgetMixin:"                     "$rt\widgets.py"
has "widgets: changeQ"  "_change_actions"                        "$rt\widgets.py"
```
Every line must read **PASS** (for `no …` lines, PASS means the forbidden marker is
absent). If any line is FAIL, the edit never reached disk; rebuilding is pointless — fix
the file first.

---

## Themes and settings

- Switching: *Settings → Appearance → `brutal` / `light` → Save & Close*.
- The theme applies to the whole UI synchronously: tabs, sidebar, editor (grid
  background), line-number column, minimap, console, find/replace, dialogs.
- Config and recent files live in `%USERPROFILE%\.spider_ide\` and survive restarts.

---

## Roadmap / known issues

- **Closed in 1.4**: new widgets (`input/checkbox/slider/dropdown/image`), events
  (`on` + `bind` aliases), arithmetic/comparisons/logic, lists/slices/indexes, string
  operations, runtime resilience to errors (catch-all without aborting), correct parsing
  of spaces around `=` and of comments containing parentheses, `change` semantics without
  spam or value clobbering.
- **Next big step (fork in the road)**: migration to AST — blocks `{ }`, `func` functions,
  `for/while` loops with a body, scopes. This is effectively a new runtime and will
  require a synchronous rewrite of highlighting/snippets/linter.
- **Polish**: a strict error mode instead of graceful fallback (a flag in
  `values.evaluate`); real timers/animations instead of the "pseudo-`wait`".

---

## Author

Project: **Spider IDE** · Language: **Spider** · Author: **project.exe and the Spider team**
