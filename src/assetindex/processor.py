"""Core pipeline: validate the resource folder, group photos by three, OCR the number, export."""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, List, Optional

from .constants import (
    GROUP_SIZE,
    GROUP_SUFFIXES,
    IGNORED_FILENAMES,
    IMAGE_EXTENSIONS,
    JPEG_QUALITY,
    OUTPUT_FORMAT,
)
from .ocr_engine import AssetNumberReader, open_image
from .timestamps import extract_timestamp

# level: "info" | "success" | "warn" | "error" | "alert"
Logger = Callable[[str, str], None]


@dataclass
class PhotoFile:
    path: str
    timestamp: datetime


@dataclass
class ScanResult:
    photos: List[PhotoFile] = field(default_factory=list)
    problems: List[str] = field(default_factory=list)


@dataclass
class RunSummary:
    exported: int = 0
    skipped_duplicate: int = 0
    failed: int = 0
    aborted: bool = False


def scan_resource(folder: str) -> ScanResult:
    """List the photos in ``folder`` (sorted by timestamp) and collect validation problems."""
    result = ScanResult()
    names = sorted(os.listdir(folder), key=str.lower)
    files = [n for n in names if os.path.isfile(os.path.join(folder, n))]
    files = [n for n in files if n.lower() not in IGNORED_FILENAMES]

    if not files:
        result.problems.append("图片来源目录下没有任何文件")
        return result

    non_images = [n for n in files if os.path.splitext(n)[1].lower() not in IMAGE_EXTENSIONS]
    for n in non_images:
        result.problems.append(f"非图片文件：{n}")

    no_stamp: List[str] = []
    for n in files:
        if n in non_images:
            continue
        stamp = extract_timestamp(os.path.splitext(n)[0])
        if stamp is None:
            no_stamp.append(n)
        else:
            result.photos.append(PhotoFile(os.path.join(folder, n), stamp))
    for n in no_stamp:
        result.problems.append(f"文件名中没有时间戳：{n}")

    if len(files) % GROUP_SIZE != 0:
        result.problems.append(
            f"文件数量为 {len(files)}，不是 {GROUP_SIZE} 的整数倍（多出 {len(files) % GROUP_SIZE} 个）"
        )

    result.photos.sort(key=lambda p: (p.timestamp, os.path.basename(p.path).lower()))
    return result


def _safe_name(number: str) -> str:
    return re.sub(r'[\\/:*?"<>|\s]+', "", number)


def _group_output_paths(output_dir: str, number: str) -> List[str]:
    return [os.path.join(output_dir, f"{number}-{suffix}{OUTPUT_FORMAT}") for suffix in GROUP_SUFFIXES]


def _save_jpg(src: str, dst: str) -> None:
    open_image(src).save(dst, "JPEG", quality=JPEG_QUALITY, optimize=True)


def run(resource_dir: str, output_dir: str, log: Logger, reader: Optional[AssetNumberReader] = None) -> RunSummary:
    summary = RunSummary()

    if not os.path.isdir(resource_dir):
        log("error", f"图片来源目录不存在：{resource_dir}")
        summary.aborted = True
        return summary
    if os.path.normcase(os.path.abspath(resource_dir)) == os.path.normcase(os.path.abspath(output_dir)):
        log("error", "图片来源目录与图片输出目录不能相同")
        summary.aborted = True
        return summary

    log("info", "正在检查图片来源目录…")
    scan = scan_resource(resource_dir)
    if scan.problems:
        log("warn", f"检查未通过，共 {len(scan.problems)} 个问题，已停止输出：")
        for problem in scan.problems:
            log("warn", f"  · {problem}")
        summary.aborted = True
        return summary

    groups = [scan.photos[i:i + GROUP_SIZE] for i in range(0, len(scan.photos), GROUP_SIZE)]
    log("success", f"检查通过：共 {len(scan.photos)} 张照片，分为 {len(groups)} 组")

    try:
        os.makedirs(output_dir, exist_ok=True)
    except OSError as exc:
        log("error", f"无法创建输出目录：{exc}")
        summary.aborted = True
        return summary

    log("info", "正在加载文字识别模型…")
    reader = reader or AssetNumberReader()

    for index, group in enumerate(groups, start=1):
        names = " / ".join(os.path.basename(p.path) for p in group)
        log("info", f"[{index}/{len(groups)}] 正在识别：{names}")
        try:
            number = reader.read(group[1].path)
        except Exception as exc:
            number = None
            log("error", f"识别出错：{exc}")

        number = _safe_name(number) if number else None
        if not number:
            summary.failed += 1
            detail = "\n".join(f"    {p.path}" for p in group)
            log("alert", f"第 {index} 组未能识别到资产编号（已跳过，请手动处理），该组照片：\n{detail}")
            continue

        targets = _group_output_paths(output_dir, number)
        if any(os.path.exists(t) for t in targets):
            summary.skipped_duplicate += 1
            log("info", f"    编号 {number} 已存在于输出目录，跳过该组")
            continue

        written: List[str] = []
        try:
            for photo, target in zip(group, targets):
                _save_jpg(photo.path, target)
                written.append(target)
        except Exception as exc:
            for t in written:
                try:
                    os.remove(t)
                except OSError:
                    pass
            summary.failed += 1
            detail = "\n".join(f"    {p.path}" for p in group)
            log("alert", f"第 {index} 组写入失败（{exc}），该组照片：\n{detail}")
            continue

        summary.exported += 1
        log("success", f"    编号 {number}：已输出 3 张")

    log("info", "—" * 28)
    log(
        "success" if not summary.failed else "warn",
        f"处理完成：成功输出 {summary.exported} 组，跳过重复编号 {summary.skipped_duplicate} 组，"
        f"失败 {summary.failed} 组",
    )
    return summary
