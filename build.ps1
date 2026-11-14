# 打包成单文件 exe
Set-Location $PSScriptRoot

& cmd /c "python -m PyInstaller --onefile --name gamelang --console --clean gamelang.py 2>&1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "打包失败，退出码 $LASTEXITCODE"
    exit $LASTEXITCODE
}

Write-Host "`n构建完成: dist\gamelang.exe"
