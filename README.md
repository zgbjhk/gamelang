# GameLang

> 一个命令，让任何单机游戏说中文。

买来的游戏一打开全是英文？翻遍设置也找不到语言选项？

GameLang 直接读游戏的语言配置文件，告诉你当前是什么语言，然后一键改成简体中文。改之前自动备份，随时能改回来。

## 下载就能用（不用装任何东西）

1. 打开 **[下载页面](https://github.com/zgbjhk/gamelang/releases/latest)**
2. 下载 `gamelang.exe`
3. 双击打开
4. 把游戏的 exe 文件拖进窗口，按回车
5. 问「是否现在改成简体中文」时，直接按回车确认

重启游戏，界面就是中文了。

原配置会自动备份成 `.gamelang.bak`，在同一个文件夹里，想反悔随时能恢复。

> Windows 11 / Windows 10 都能用，不需要安装 Python，也不需要联网。

## 能识别哪些游戏

| 引擎 | 改哪里 |
| --- | --- |
| 虚幻引擎 4 / 5 | `Engine/Config/Engine.ini` 里的 `Culture=` |
| Unity | `steam_settings/configs.user.ini` 里的 `language=`，以及存档里的 PlayerPrefs |
| Ren'Py | `game/options.rpy` |
| RPG Maker | 游戏目录下的语言配置 |
| 其他 | 兜底扫描 `language`、`lang`、`locale`、`culture` 这些键 |

识别不出来也没关系，工具会明确告诉你这个游戏需要在游戏内设置里手动切，并给出大概位置。

## 命令行用法

喜欢敲命令的话：

```bash
# 只检测，不改动任何文件（默认行为）
gamelang "D:\游戏\某某\某某.exe"

# 一键改成简体中文
gamelang "D:\游戏\某某\某某.exe" --apply

# 改成其他语言
gamelang "D:\游戏\某某\某某.exe" --apply --lang english

# 输出 JSON，方便接到别的工具里
gamelang "D:\游戏\某某\某某.exe" --json

# 反悔了，从备份恢复
gamelang --restore "D:\游戏\某某\steam_settings\configs.user.ini"
```

可以直接把游戏文件夹路径传进去，工具会自动在里面找 exe。

| 选项 | 作用 |
| --- | --- |
| `--apply` | 真正写入配置。不加只检测，绝不改文件 |
| `--lang` | 目标语言，默认 `schinese`（简体中文） |
| `--restore` | 从 `.gamelang.bak` 恢复原配置 |
| `--json` | 输出 JSON 格式的检测结果 |
| `--no-banner` | 不显示标题，适合脚本调用 |

## 安全说明

- 默认只读。不加 `--apply` 时不会写任何文件
- 写入前一定先备份成 `.gamelang.bak`
- 只动语言相关的单行配置，不改游戏本体文件
- 纯本地运行，不联网，不上传任何数据

## 从源码运行

```bash
git clone https://github.com/zgbjhk/gamelang.git
cd gamelang
python gamelang.py "D:\游戏\某某\某某.exe"
```

需要 Python 3.8 以上。

## 自己打包成 exe

```powershell
.\build.ps1
```

产物在 `dist\gamelang.exe`。

## 常见问题

**双击没反应？**
可能被 Windows 拦了，右键 exe → 属性 → 勾选「解除锁定」。

**提示「没能识别出这个游戏」？**
到 [Issues](https://github.com/zgbjhk/gamelang/issues) 说一声游戏名字，我们会加上支持。

**改了还是英文？**
有些游戏会把语言存在存档或注册表里，工具会提示你去游戏设置里切。另外确认游戏重启过了。

## 许可证

MIT
