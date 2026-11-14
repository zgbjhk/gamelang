# 打包成单文件 exe
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

python -m PyInstaller --onefile --name gamelang --console --clean gamelang.py
Write-Host "`n构建完成: dist\gamelang.exe"
