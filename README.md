# GameLang

**One command to make any PC game speak Chinese.**

A zero-dependency CLI that detects your game's engine, finds where it stores its
language setting, and flips it to 简体中文 — with automatic backup and restore.

```
  GameLang v0.1.0   make every game speak Chinese

  game      AirportSim
  path      E:\Games\AirportSim\AirportSim.exe
  engine    Unity · Steam
  config    E:\Games\AirportSim\steam_settings\configs.user.ini
  key       [user::general] language
  current   french
  target    schinese

  ✔ written language=schinese
    backup: configs.user.ini.gamelang.bak
```

## Why

Changing a game's language usually means digging through forums for a config
path that nobody documents. The path depends on the engine, the store, and
sometimes on whether it's a cracked build. GameLang just knows.

## Install

```bash
git clone https://github.com/zgbjhk/gamelang.git
cd gamelang
python gamelang.py "D:\Games\SomeGame\SomeGame.exe"
```

No `pip install` needed — pure standard library.

Build a single-file executable:

```powershell
.\build.ps1
```

## Usage

```bash
# inspect only (never writes anything)
gamelang "D:\Games\Foo\Foo.exe"

# switch to Simplified Chinese
gamelang "D:\Games\Foo\Foo.exe" --apply

# other languages
gamelang "D:\Games\Foo\Foo.exe" --apply --lang english

# undo
gamelang --restore "D:\Games\Foo\steam_settings\configs.user.ini"

# machine-readable
gamelang "D:\Games\Foo\Foo.exe" --json
```

You can also pass the game **folder** — GameLang picks the exe when there's only one.

## Supported engines

| Engine | Detects | Can write |
|---|---|---|
| Unreal Engine 4/5 | `GameUserSettings.ini` → `[Internationalization] Culture` | ✅ |
| Unity + Steam emulator | `steam_settings/configs.user.ini` → `language` | ✅ |
| Unity (native) | PlayerPrefs registry location | manual (in-game menu) |
| Ren'Py | language packs in `game/tl/` | manual (in-game menu) |
| RPG Maker MV/MZ | `data/System.json` | manual |
| Anything else | scans `ini/cfg/json/xml/yaml` for `language`/`lang`/`locale`/`culture` | ✅ |

Unity's native PlayerPrefs key name is different in almost every game, so we
report the registry location instead of guessing and corrupting your save.

## Safety

- Never writes unless you pass `--apply`
- Backs up to `<file>.gamelang.bak` before the first modification
- `--restore` puts the original bytes back
- Keeps your line endings (CRLF/LF), BOM and comments intact

## Adding an engine

Add a `detect_yourgame(exe) -> Target | None` function in
[engines.py](engines.py) and append it to `DETECTORS`. That's the whole API.

## 中文说明

GameLang 是一个零依赖的命令行小工具：给它一个游戏 exe，它会自动识别游戏引擎，
找到语言配置在哪，然后帮你切成简体中文。

- 默认只检测、不改动；加 `--apply` 才真正写入
- 改之前自动备份为 `xxx.gamelang.bak`，`--restore` 可还原
- 已支持：虚幻引擎 4/5、Unity（含 Steam 模拟器）、Ren'Py、RPG Maker MV/MZ，以及其他带 `language` 键的通用配置文件

```bash
python gamelang.py "D:\游戏\某游戏.exe"          # 只看
python gamelang.py "D:\游戏\某游戏.exe" --apply  # 改成中文
```

## License

MIT
