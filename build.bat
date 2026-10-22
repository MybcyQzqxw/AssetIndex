@echo off
chcp 65001 >nul
setlocal

rem ============================================================
rem  AssetIndex 一键构建脚本
rem  使用独立 conda 环境 + pip 安装依赖，打包单文件 AssetIndex.exe
rem  可重复运行：每次都会先清理旧的构建产物再重新构建
rem ============================================================

set ENV_NAME=assetindex
set PY_VERSION=3.11

cd /d "%~dp0"

echo [1/6] 检查 conda 环境...
where conda >nul 2>nul
if errorlevel 1 (
    echo 错误：未找到 conda，请先安装 Miniconda/Anaconda 并确保已加入 PATH。
    pause
    exit /b 1
)

echo [2/6] 清理旧的构建产物...
for %%D in (build dist release) do (
    if exist "%%D" rmdir /s /q "%%D"
    if exist "%%D" (
        echo 错误：无法删除 %%D 目录，请先关闭正在运行的 AssetIndex.exe 或占用该目录的程序。
        pause
        exit /b 1
    )
)
if exist "AssetIndex.spec" del /f /q "AssetIndex.spec"

call conda env list | findstr /r /c:"^%ENV_NAME% " >nul 2>nul
if errorlevel 1 (
    echo [3/6] 创建 conda 环境 %ENV_NAME%（Python %PY_VERSION%）...
    call conda create -n %ENV_NAME% python=%PY_VERSION% -y
    if errorlevel 1 (
        echo 错误：创建 conda 环境失败。
        pause
        exit /b 1
    )
) else (
    echo [3/6] 已检测到 conda 环境 %ENV_NAME%，跳过创建。
)

echo [4/6] 安装依赖...
call conda run -n %ENV_NAME% --no-capture-output python -m pip install --upgrade pip
call conda run -n %ENV_NAME% --no-capture-output python -m pip install -r requirements.txt
if errorlevel 1 (
    echo 错误：依赖安装失败。
    pause
    exit /b 1
)

echo [5/6] 使用 PyInstaller 打包单文件 exe ...
call conda run -n %ENV_NAME% --no-capture-output python -m PyInstaller --noconfirm --clean --onefile --windowed ^
    --name AssetIndex ^
    --paths src ^
    --icon "favicon.ico" ^
    --add-data "favicon.ico;." ^
    --collect-all rapidocr_onnxruntime ^
    --collect-all pillow_heif ^
    "src\main.py"
if errorlevel 1 (
    echo 错误：PyInstaller 打包失败。
    pause
    exit /b 1
)
if not exist "dist\AssetIndex.exe" (
    echo 错误：未生成 dist\AssetIndex.exe。
    pause
    exit /b 1
)

echo [6/6] 整理输出文件...
mkdir "release"
copy /y "dist\AssetIndex.exe" "release\AssetIndex.exe" >nul
rmdir /s /q "build"
rmdir /s /q "dist"
if exist "AssetIndex.spec" del /f /q "AssetIndex.spec"

echo.
echo ============================================================
echo  打包完成！可执行文件位于：release\AssetIndex.exe
echo ============================================================

set /p OPEN_FOLDER=是否在文件资源管理器中打开该文件夹？(Y/N): 
if /i "%OPEN_FOLDER%"=="Y" (
    explorer "%~dp0release"
)

pause
