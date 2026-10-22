"""Shared constants for the AssetIndex application."""

APP_NAME = "AssetIndex"
GROUP_SIZE = 3
GROUP_SUFFIXES = ("整体照片", "带标签照片", "铭牌")

IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".jpe", ".jfif", ".png", ".bmp", ".gif",
    ".tif", ".tiff", ".webp", ".heic", ".heif",
}

# System files Windows/macOS drop into folders on their own; never treated as user files.
IGNORED_FILENAMES = {"thumbs.db", "desktop.ini", ".ds_store"}

OUTPUT_FORMAT = ".jpg"
JPEG_QUALITY = 95

# Folders pre-filled on first launch (a remembered choice takes precedence).
DEFAULT_RESOURCE_DIR = r"D:\mine\！文件\设备统计\Resource"
DEFAULT_OUTPUT_DIR = r"D:\mine\！文件\设备统计\Output"
