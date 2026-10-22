# AssetIndex

资产照片自动分组重命名工具（PySide6 界面，粉色主题，可打包为单文件 exe）。

将「图片来源（Resource）」目录中按时间戳排序的照片，每连续 3 张为一组，通过 OCR 读取第 2 张（资产标牌）上
“资产编号”后的内容，并以 `编号-整体照片.jpg`、`编号-带标签照片.jpg`、`编号-铭牌.jpg` 输出到「图片输出（Output）」目录。

## 规则

- 来源目录文件数必须是 3 的整数倍，且全部为文件名带时间戳的图片（jpg/png/bmp/gif/tiff/webp/heic），否则警告并不输出。
- 输出统一为 jpg。
- 编号与输出目录中已有文件重复：跳过该组，终端汇总跳过组数。
- 第 2 张照片识别不到资产编号：跳过该组，并以红色醒目提示该组 3 张照片的完整路径。
- 两个目录路径会被记忆（QSettings），下次启动自动恢复。
- OCR 使用 RapidOCR（ONNX，完全离线）。

## 运行（开发模式）

```
conda create -n assetindex python=3.11 -y
conda activate assetindex
pip install -r requirements.txt
python src\main.py
```

## 构建（打包为 exe）

需要本机已安装 conda（Miniconda/Anaconda）并加入 PATH。`build.bat` 会：

1. 清理旧的 `build\`、`dist\`、`release\` 和 `AssetIndex.spec`（可重复运行，每次都是干净的重新构建）；
2. 创建 conda 环境 `assetindex`（Python 3.11，已存在则复用），并用 pip 安装 `requirements.txt` 中的依赖；
3. 用 PyInstaller 打包单文件 exe，并只保留 `release\AssetIndex.exe`；
4. 末尾询问是否在文件资源管理器中打开 exe 所在目录（输入 `Y` 打开）。

在命令行（cmd 或 PowerShell）中执行：

```
cd /d D:\gitspace\AssetIndex
.\build.bat
```

PowerShell 中也可写为 `cmd /c build.bat`。也可以直接双击 `build.bat`。

构建前请先关闭正在运行的 `AssetIndex.exe`，否则无法清理 `release\` 目录。不再需要该环境时可用 `conda env remove -n assetindex` 删除。
