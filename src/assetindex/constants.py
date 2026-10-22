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
