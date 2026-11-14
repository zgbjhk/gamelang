"""GameLang 引擎识别与语言配置定位.

零第三方依赖. 每个引擎实现一个 detect_xxx(exe) -> Target | None 函数,
新增引擎只需再加一个函数并注册进 DETECTORS.
"""
from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Steam 语言代码 -> 中文
CHINESE_CODES = ("schinese", "zh-cn", "zh_cn", "zh-hans", "zh_hans", "chs", "chinese", "简体中文")

LANG_KEY_RE = re.compile(r"^\s*(language|lang|locale|culture|Language|LanguageVersion)\s*[=:]\s*(.+?)\s*$", re.I)

CONFIG_SUFFIXES = {".ini", ".cfg", ".json", ".xml", ".yaml", ".yml", ".txt"}
SKIP_DIRS = {"managed", "monobleedingedge", "paks", "recordings", "logs", "crashes"}


@dataclass
class Target:
    engine: str
    kind: str                      # ini | registry | manual | none
    path: Path | None = None
    section: str = ""
    key: str = ""
    current: str | None = None
    note: str = ""
    langs: list[str] = field(default_factory=list)
    fixable: bool = False


# ---------------------------------------------------------------- ini 读写

def _read_text(path: Path) -> tuple[str, bool, str]:
    raw = path.read_bytes()
    bom = raw.startswith(b"\xef\xbb\xbf")
    if bom:
        raw = raw[3:]
    nl = "\r\n" if b"\r\n" in raw else "\n"
    return raw.decode("utf-8", errors="replace"), bom, nl


def get_ini_value(path: Path, section: str, key: str) -> str | None:
    text, _, _ = _read_text(path)
    cur = ""
    for ln in text.splitlines():
        m = re.match(r"^\s*\[(.+?)\]\s*$", ln)
        if m:
            cur = m.group(1).strip()
            continue
        m2 = re.match(rf"^\s*{re.escape(key)}\s*=\s*(.+?)\s*$", ln, re.I)
        if m2 and (not section or cur.lower() == section.lower()):
            return m2.group(1)
    return None


def set_ini_value(path: Path, section: str, key: str, value: str) -> bool:
    """把 ini 里的 key 改成 value. 找不到就新增到指定 section 末尾."""
    text, bom, nl = _read_text(path)
    lines = text.split(nl)
    cur = ""
    hit = False

    for i, ln in enumerate(lines):
        m = re.match(r"^\s*\[(.+?)\]\s*$", ln)
        if m:
            cur = m.group(1).strip()
            continue
        m2 = re.match(rf"^(\s*{re.escape(key)}\s*=\s*)(.*?)(\s*)$", ln, re.I)
        if m2 and (not section or cur.lower() == section.lower()):
            lines[i] = m2.group(1) + value
            hit = True
            break

    if not hit:
        if section:
            start = None
            for i, ln in enumerate(lines):
                if re.match(rf"^\s*\[{re.escape(section)}\]\s*$", ln, re.I):
                    start = i
                    break
            if start is None:
                while lines and lines[-1].strip() == "":
                    lines.pop()
                lines += ["", f"[{section}]", f"{key}={value}", ""]
            else:
                j = start + 1
                while j < len(lines) and not re.match(r"^\s*\[.+\]\s*$", lines[j]):
                    j += 1
                lines.insert(j, f"{key}={value}")
        else:
            while lines and lines[-1].strip() == "":
                lines.pop()
            lines += [f"{key}={value}", ""]

    path.write_text(nl.join(lines), encoding="utf-8-sig" if bom else "utf-8", newline="")
    return True


def backup(path: Path) -> Path:
    """第一次修改前备份原文件, 已备份过就不覆盖."""
    bak = path.with_suffix(path.suffix + ".gamelang.bak")
    if not bak.exists():
        bak.write_bytes(path.read_bytes())
    return bak


# ---------------------------------------------------------------- 各引擎识别

def detect_unreal(exe: Path) -> Target | None:
    if exe.parent.name.lower() != "win64" or exe.parent.parent.name.lower() != "binaries":
        return None
    root = exe.parents[2]
    if not (root / "Content").exists():
        return None

    proj = exe.stem
    local = os.environ.get("LOCALAPPDATA", "")
    candidates = [
        Path(local) / proj / "Saved" / "Config" / "WindowsNoEditor" / "GameUserSettings.ini",
        Path(local) / proj / "Saved" / "Config" / "Windows" / "GameUserSettings.ini",
        root / "Saved" / "Config" / "WindowsNoEditor" / "GameUserSettings.ini",
    ]
    for cfg in candidates:
        if cfg.is_file():
            cur = get_ini_value(cfg, "Internationalization", "Culture")
            return Target("Unreal Engine", "ini", cfg, "Internationalization", "Culture",
                          cur, fixable=True)
    return Target("Unreal Engine", "manual", None,
                  note="游戏还没运行过, 首次进游戏退出后再运行本工具即可定位配置")


def _find_steam_settings(exe: Path) -> Path | None:
    bases = [exe.parent]
    p = exe.parent
    for _ in range(3):
        if p.parent == p:
            break
        p = p.parent
        bases.append(p)
    for b in bases:
        cand = b / "steam_settings" / "configs.user.ini"
        if cand.is_file():
            return cand
        for hit in b.glob("*/steam_settings/configs.user.ini"):
            return hit
    return None


def detect_unity(exe: Path) -> Target | None:
    # 优先找 Steam 模拟器/客户端的语言配置, 不管 steam_api dll 在不在
    cfg = _find_steam_settings(exe)
    if cfg:
        cur = get_ini_value(cfg, "user::general", "language")
        return Target("Unity · Steam", "ini", cfg, "user::general", "language",
                      cur, fixable=True)

    datas = [d for d in exe.parent.iterdir()
             if d.is_dir() and d.name.lower().endswith("_data")]
    if not datas:
        return None
    data = datas[0]
    if not (exe.parent / "UnityPlayer.dll").exists() and not (data / "globalgamemanagers").exists():
        return None

    company = product = ""
    appinfo = data / "app.info"
    if appinfo.is_file():
        lines = appinfo.read_text(encoding="utf-8", errors="ignore").splitlines()
        if len(lines) >= 2:
            company, product = lines[0].strip(), lines[1].strip()

    note = "Unity 原生游戏的语言存在 PlayerPrefs, 没有通用键名, 请在游戏内设置里切换"
    if company and product:
        note += f"\n  注册表位置: HKCU\\Software\\{company}\\{product}"
    return Target("Unity", "manual", None, note=note)


def detect_renpy(exe: Path) -> Target | None:
    root = exe.parent
    gdir = root / "game"

    if not (root / "renpy").exists():
        if not gdir.is_dir():
            return None
        # 只有 game 目录还不够, 必须有 Ren'Py 的特征文件
        marks = (list(gdir.glob("*.rpy")) + list(gdir.glob("*.rpyc"))
                 + list(gdir.glob("*.rpa")) + list(gdir.glob("script.*")))
        if not marks:
            return None

    tl = gdir / "tl"
    langs = []
    if tl.is_dir():
        langs = sorted(d.name for d in tl.iterdir() if d.is_dir())
    if not langs:
        note = "未发现 game/tl 语言包, 游戏可能只有单语言"
    else:
        note = "可用语言包: " + ", ".join(langs) + "\n  在游戏主菜单 → Preferences → Language 中选择"
    return Target("Ren'Py", "manual", None, note=note, langs=langs)


def detect_rpgmaker(exe: Path) -> Target | None:
    root = exe.parent
    www = root / "www"
    sys_json = (www if www.is_dir() else root) / "data" / "System.json"
    if not sys_json.is_file():
        return None
    note = "RPG Maker 语言通常由插件或翻译文件控制, 请在游戏内设置或检查 data 目录"
    return Target("RPG Maker MV/MZ", "manual", None, note=note)


def _iter_configs(root: Path, max_depth: int = 2):
    root = root.resolve()
    for dirpath, dirnames, filenames in os.walk(root):
        d = Path(dirpath)
        try:
            depth = len(d.relative_to(root).parts)
        except ValueError:
            continue
        if depth >= max_depth:
            dirnames[:] = []
        dirnames[:] = [x for x in dirnames if x.lower() not in SKIP_DIRS]
        for fn in filenames:
            if Path(fn).suffix.lower() in CONFIG_SUFFIXES:
                yield d / fn


def detect_generic(exe: Path) -> Target | None:
    """兜底: 扫游戏目录找带 language/lang/locale/culture 键的配置文件."""
    for cfg in _iter_configs(exe.parent):
        try:
            if cfg.stat().st_size > 2 * 1024 * 1024:
                continue
            text, _, _ = _read_text(cfg)
        except OSError:
            continue
        cur_section = ""
        for ln in text.splitlines():
            m = re.match(r"^\s*\[(.+?)\]\s*$", ln)
            if m:
                cur_section = m.group(1).strip()
                continue
            m2 = LANG_KEY_RE.match(ln)
            if m2:
                return Target("未知 (通用扫描)", "ini", cfg, cur_section,
                              m2.group(1), m2.group(2), fixable=True)
    return None


DETECTORS = (detect_unreal, detect_unity, detect_renpy, detect_rpgmaker, detect_generic)


def detect(exe: Path) -> Target | None:
    if not exe.is_file():
        return None
    for fn in DETECTORS:
        try:
            t = fn(exe)
        except Exception:
            t = None
        if t:
            return t
    return None


# ---------------------------------------------------------------- 应用

def apply(target: Target, lang: str) -> tuple[bool, str]:
    if target.kind == "ini" and target.path and target.fixable:
        bak = backup(target.path)
        set_ini_value(target.path, target.section, target.key, lang)
        return True, f"已写入 {target.key}={lang}\n  备份: {bak.name}"
    if target.kind == "registry":
        return False, "该游戏的语言只有游戏内设置可以改, 无法直接写配置"
    return False, "该引擎暂不支持自动修改, 请看上面的提示手动处理"


def restore(path: Path) -> tuple[bool, str]:
    bak = path.with_suffix(path.suffix + ".gamelang.bak")
    if not bak.exists():
        return False, f"没有找到备份: {bak.name}"
    path.write_bytes(bak.read_bytes())
    bak.unlink()
    return True, "已从备份恢复原配置"
