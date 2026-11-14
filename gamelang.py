#!/usr/bin/env python3
"""GameLang — 把单机游戏切成中文.

用法:
    gamelang "E:\\Games\\Foo\\Foo.exe"          检测并显示当前语言配置
    gamelang "E:\\Games\\Foo\\Foo.exe" --apply  直接改成简体中文
    gamelang --restore "E:\\...\\configs.user.ini"  从备份恢复
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import engines

VERSION = "0.1.0"
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


def show(target: engines.Target, exe: Path, lang: str) -> None:
    print()
    print(row("游戏", bold(exe.stem)))
    print(row("路径", dim(str(exe))))
    print(row("引擎", cyan(target.engine)))
    if target.kind == "ini" and target.path:
        print(row("配置", str(target.path)))
        print(row("键名", f"[{target.section or 'root'}] {target.key}" if target.section
                  else target.key))
        cur = target.current or "(未设置)"
        print(row("当前", yellow(cur) if cur != lang else green(cur)))
        print(row("目标", green(lang)))
    if target.note:
        print()
        for ln in target.note.splitlines():
            print("  " + ln)


def main() -> int:
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    ap = argparse.ArgumentParser(
        prog="gamelang",
        description="检测单机游戏的语言配置, 并可一键切换为简体中文",
    )
    ap.add_argument("path", nargs="?", help="游戏 exe 路径")
    ap.add_argument("--lang", default=DEFAULT_LANG, help=f"目标语言代码 (默认 {DEFAULT_LANG})")
    ap.add_argument("--apply", action="store_true", help="实际写入配置")
    ap.add_argument("--restore", metavar="FILE", help="从 .gamelang.bak 恢复配置")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--no-banner", action="store_true", help="不显示 ASCII 标题")
    ap.add_argument("-v", "--version", action="version", version=f"GameLang {VERSION}")
    args = ap.parse_args()

    if args.restore:
        ok, msg = engines.restore(Path(args.restore))
        print((green("  ✔ ") if ok else red("  ✘ ")) + msg)
        return 0 if ok else 1

    if not args.path:
        ap.print_help()
        return 2

    exe = Path(args.path).expanduser()
    if exe.is_dir():
        cands = sorted(p for p in exe.glob("*.exe") if "unins" not in p.name.lower())
        if len(cands) == 1:
            exe = cands[0]
        elif cands:
            print(red("  目录里有多个 exe, 请指定具体文件:"))
            for p in cands:
                print("    " + p.name)
            return 2

    if not exe.is_file():
        print(red(f"  找不到文件: {exe}"))
        return 2

    target = engines.detect(exe)
    if not target:
        print(red("  ✘ 没能识别出引擎, 也不是已知的配置文件格式"))
        print(dim("    可以在 GitHub 提 issue 并附上游戏名, 我们会加支持"))
        return 1

    if args.json:
        print(json.dumps({
            "game": exe.stem,
            "exe": str(exe),
            "engine": target.engine,
            "kind": target.kind,
            "config": str(target.path) if target.path else None,
            "section": target.section,
            "key": target.key,
            "current": target.current,
            "languages": target.langs,
            "fixable": target.fixable,
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

    if not target.fixable:
        print()
        print(red("  ✘ ") + "这个游戏需要手动在游戏内设置里切换语言")
        return 1

    ok, msg = engines.apply(target, args.lang)
    print()
    print((green("  ✔ ") if ok else red("  ✘ ")) + msg)
    if ok:
        print(dim("    重启游戏生效"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
