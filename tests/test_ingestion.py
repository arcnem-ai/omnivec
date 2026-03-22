from __future__ import annotations

import zipfile
from pathlib import Path
import stat

import pytest

from omnivec.ingestion import classify_assets, group_exact_duplicates, safe_extract_zip


def test_safe_extract_zip_rejects_path_traversal(tmp_path: Path) -> None:
    archive_path = tmp_path / "bad.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("../escape.txt", b"nope")

    with pytest.raises(ValueError, match="escape"):
        safe_extract_zip(archive_path, tmp_path / "extracted")


def test_safe_extract_zip_rejects_symlinks(tmp_path: Path) -> None:
    archive_path = tmp_path / "symlink.zip"
    symlink = zipfile.ZipInfo("docs/link.md")
    symlink.create_system = 3
    symlink.external_attr = (stat.S_IFLNK | 0o777) << 16

    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr(symlink, "target.md")

    with pytest.raises(ValueError, match="symlink"):
        safe_extract_zip(archive_path, tmp_path / "extracted")


def test_classify_assets_and_group_duplicates(tmp_path: Path) -> None:
    root = tmp_path / "assets"
    root.mkdir()
    (root / "docs").mkdir()
    (root / "images").mkdir()
    (root / "docs" / "a.md").write_text("same")
    (root / "docs" / "b.md").write_text("same")
    (root / "docs" / "c.txt").write_text("different")
    (root / "images" / "cat1.png").write_bytes(b"image")
    (root / "notes.pdf").write_bytes(b"ignored")

    inventory = classify_assets(root)

    assert inventory.documents == ["docs/a.md", "docs/b.md", "docs/c.txt"]
    assert inventory.images == ["images/cat1.png"]
    assert inventory.ignored == ["notes.pdf"]

    duplicates = group_exact_duplicates(root, inventory.documents, "document")
    assert len(duplicates) == 1
    assert duplicates[0].files == ["docs/a.md", "docs/b.md"]
