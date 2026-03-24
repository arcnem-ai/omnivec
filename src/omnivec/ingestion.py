"""ZIP safety checks, file inventory, and exact duplicate helpers."""

from __future__ import annotations

import hashlib
import os
import shutil
import stat
import zipfile
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from omnivec.schemas import AssetKind, DuplicateGroup

SUPPORTED_DOCUMENT_SUFFIXES = {".txt", ".md", ".markdown"}
SUPPORTED_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}


@dataclass(slots=True)
class AssetInventory:
    """Lists supported document files, image files, and ignored files."""

    documents: list[str]
    images: list[str]
    ignored: list[str]

    @property
    def supported_count(self) -> int:
        return len(self.documents) + len(self.images)


def safe_extract_zip(zip_path: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    root = destination.resolve()

    with zipfile.ZipFile(zip_path) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue

            if _is_symlink(info):
                raise ValueError(f"ZIP entry {info.filename!r} is a symlink, which is not allowed")

            relative_path = Path(info.filename)
            if relative_path.is_absolute() or ".." in relative_path.parts:
                raise ValueError(
                    f"ZIP entry {info.filename!r} would escape the extraction directory"
                )

            target_path = destination / relative_path
            resolved_target = target_path.resolve()
            if os.path.commonpath([str(root), str(resolved_target)]) != str(root):
                raise ValueError(
                    f"ZIP entry {info.filename!r} would escape the extraction directory"
                )

            target_path.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(info) as source, target_path.open("wb") as output:
                shutil.copyfileobj(source, output)


def classify_assets(root: Path) -> AssetInventory:
    documents: list[str] = []
    images: list[str] = []
    ignored: list[str] = []

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue

        relative = path.relative_to(root).as_posix()
        suffix = path.suffix.lower()
        if suffix in SUPPORTED_DOCUMENT_SUFFIXES:
            documents.append(relative)
        elif suffix in SUPPORTED_IMAGE_SUFFIXES:
            images.append(relative)
        else:
            ignored.append(relative)

    return AssetInventory(documents=documents, images=images, ignored=ignored)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def group_exact_duplicates(root: Path, files: list[str], kind: AssetKind) -> list[DuplicateGroup]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for relative in files:
        grouped[sha256_file(root / relative)].append(relative)

    results = [
        DuplicateGroup(kind=kind, sha256=sha, files=sorted(paths))
        for sha, paths in grouped.items()
        if len(paths) > 1
    ]
    return sorted(results, key=lambda group: (group.kind, group.files[0]))


def _is_symlink(info: zipfile.ZipInfo) -> bool:
    mode = info.external_attr >> 16
    return stat.S_ISLNK(mode)
