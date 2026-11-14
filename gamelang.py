#!/usr/bin/env python3
"""GameLang — 让单机游戏说中文。

用法：
    gamelang "D:\\游戏\\某某.exe"           只检测，不改动
    gamelang "D:\\游戏\\某某.exe" --apply   改成简体中文
    gamelang --restore "D:\\...\\配置.ini"   从备份恢复
    直接双击运行                             交互模式（适合新手）
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import engines

VERSION = "0.2.0"
DEFAULT_LANG = "schinese"
C_ENABLED = os.environ.get("NO_COLOR") is None


def c(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m" if C_ENABLED else text


dim = lambda s: c(s, "2")
bold = lambda s: c(s, "1")
cyan = lambda s: c(s, "36")
green = lambda s: c(s, "32")
yellow = lambda s: c(s, "33")
red = lambda s: c(s, "31")


BANNER = r"""
   ___                       _
  / _ \__ _ _ __ ___   ___  | |    __ _ _ __   __ _
 | |_  / _` | '_ ` _ \ / _ \ | |   / _` | '_ \ / _` |
 |  _| (_| | | | | | |  __/ | |__| (_| | | | | (_| |
  |_|  \__,_|_| |_| |_|\___| |_____\__,_|_| |_|\__, |
                                              |___/
"""


def row(label: str, value: str) -> str:
    return f"  {dim(label.ljust(8))} {value}"


def show(target: "engines.Target", exe: Path, lang: str) -> None:
    print()
    print(row("游戏", bold(exe.stem)))
    print(row("路径", dim(str(exe))))
    print(row("引擎", cyan(target.engine)))
    if target.kind == "ini" and target.path:
        print(row("配置", str(target.path)))
        print(row("键名", f"[{target.section}] {target.key}" if target.section else target.key))
        cur = target.current or "（未设置）"
        print(row("当前", yellow(cur) if cur != lang else green(cur)))
        print(row("目标", green(lang)))
    if target.note:
        print()
        for ln in target.note.splitlines():
            print("  " + ln)


def pick_exe(folder: Path) -> Path | None:
    """从文件夹里挑出唯一的游戏 exe."""
    cands = sorted(p for p in folder.glob("*.exe")
                   if "unins" not in p.name.lower() and "vcredist" not in p.name.lower())
    if len(cands) == 1:
        return cands[0]
    if not cands:
        print(red("  这个文件夹里没有找到 exe 文件"))
        return None
    print(red("  这个文件夹里有多个 exe，请把具体那个拖进来："))
    for p in cands[:12]:
        print("    · " + p.name)
    return None


def normalize(raw: str) -> Path:
    return Path(raw.strip().strip('"').strip("'")).expanduser()


def resolve(path: Path) -> Path | None:
    if path.is_dir():
        return pick_exe(path)
    if path.is_file():
        return path
    return None


def do_apply(target: "engines.Target", lang: str) -> int:
    if not target.fixable:
        print()
        print(red("  × ") + "这个游戏需要在游戏内设置里手动切换语言")
        return 1
    ok, msg = engines.apply(target, lang)
    print()
    print((green("  √ ") if ok else red("  × ")) + msg)
    if ok:
        print(dim("    重启游戏后生效"))
    return 0 if ok else 1


def bail(msg: str, code: int = 1) -> int:
    print(red("  × ") + msg)
    return code


# ---------------------------------------------------------------- 交互模式

def interactive() -> int:
    print(dim(BANNER))
    print(f"  {dim('GameLang v' + VERSION)}   {dim('让每个游戏都说中文')}")
    print()
    print("  把游戏的 exe 文件直接拖到这个窗口里，然后按回车：")
    print()
    try:
        raw = input("  > ")
    except (EOFError, KeyboardInterrupt):
        print()
        return 1

    if not raw.strip():
        print(red("  没有输入路径"))
        return 1

    exe = resolve(normalize(raw))
    if exe is None:
        return 1

    target = engines.detect(exe)
    if target is None:
        print()
        print(red("  × ") + "没能识别出这个游戏的语言配置")
        print(dim("    可以到 GitHub 提 issue 并附上游戏名字，我们会加支持"))
        return 1

    show(target, exe, DEFAULT_LANG)

    if not target.fixable:
        print()
        print(dim("  提示：按上面的说明在游戏设置里切换即可"))
        return 0

    if target.current == DEFAULT_LANG:
        print()
        print(green("  这个游戏已经是简体中文了，不需要修改"))
        return 0

    print()
    try:
        ans = input("  是否现在改成简体中文？直接回车＝是，输入 n＝否： ")
    except (EOFError, KeyboardInterrupt):
        print()
        return 1

    if ans.strip().lower() in ("n", "no", "否", "不"):
        print(dim("  已取消，没有改动任何文件"))
        return 0

    return do_apply(target, DEFAULT_LANG)


# ---------------------------------------------------------------- 命令行

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="gamelang",
        usage="gamelang <游戏exe路径> [选项]",
        description="检测单机游戏的语言配置，并可一键切换为简体中文",
        add_help=False,
    )
    ap.add_argument("path", nargs="?", help="游戏 exe 路径，也可以直接给游戏文件夹")
    ap.add_argument("--lang", default=DEFAULT_LANG, help="目标语言代码，默认 schinese（简体中文）")
    ap.add_argument("--apply", action="store_true", help="实际写入配置，不加则只检测不改动")
    ap.add_argument("--restore", metavar="文件", help="从 .gamelang.bak 备份恢复原配置")
    ap.add_argument("--json", action="store_true", help="以 JSON 格式输出检测结果")
    ap.add_argument("--no-banner", action="store_true", help="不显示标题")
    ap.add_argument("-h", "--help", action="help", help="显示本帮助")
    ap.add_argument("-v", "--version", action="version",
                    version=f"GameLang {VERSION}", help="查看版本号")
    try:
        ap._positionals.title = "参数"
        ap._optionals.title = "选项"
    except AttributeError:
        pass
    return ap


def prepare_console() -> None:
    """双击运行时把窗口代码页切到 UTF-8, 并打开颜色支持."""
    if sys.platform != "win32":
        return
    try:
        os.system("chcp 65001 >nul 2>&1")
    except Exception:
        pass
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    try:
        import ctypes
        k32 = ctypes.windll.kernel32
        handle = k32.GetStdHandle(-11)
        mode = ctypes.c_uint32()
        if k32.GetConsoleMode(handle, ctypes.byref(mode)):
            k32.SetConsoleMode(handle, mode.value | 0x0004)
    except Exception:
        pass


def main() -> int:
    prepare_console()
    ap = build_parser()
    args = ap.parse_args()
    launched_by_double_click = len(sys.argv) == 1

    if args.restore:
        ok, msg = engines.restore(normalize(args.restore))
        print((green("  √ ") if ok else red("  × ")) + msg)
        return 0 if ok else 1

    if launched_by_double_click:
        code = interactive()
        print()
        try:
            input("  按回车键关闭窗口...")
        except (EOFError, KeyboardInterrupt):
            pass
        return code

    if not args.path:
        ap.print_help()
        return 2

    exe = resolve(normalize(args.path))
    if exe is None:
        return bail("找不到这个文件或文件夹")

    target = engines.detect(exe)
    if target is None:
        return bail("没能识别出这个游戏的语言配置，可以到 GitHub 提 issue 附上游戏名")

    if args.json:
        print(json.dumps({
            "游戏": exe.stem,
            "路径": str(exe),
            "引擎": target.engine,
            "类型": target.kind,
            "配置": str(target.path) if target.path else None,
            "配置节": target.section,
            "键名": target.key,
            "当前语言": target.current,
            "可用语言": target.langs,
            "可自动修改": target.fixable,
        }, ensure_ascii=False, indent=2))
        return 0

    if not args.no_banner:
        print(dim(BANNER))
        print(f"  {dim('GameLang v' + VERSION)}   {dim('让每个游戏都说中文')}")

    show(target, exe, args.lang)

    if not args.apply:
        print()
        if target.fixable:
            print(f"  {yellow('提示')} 加 --apply 一键改成 {args.lang}")
        return 0

    return do_apply(target, args.lang)


if __name__ == "__main__":
    sys.exit(main())
