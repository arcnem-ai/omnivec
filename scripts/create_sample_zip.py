from __future__ import annotations

import argparse
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a demo ZIP from sample_assets.")
    parser.add_argument("--source", default="sample_assets", help="Source asset directory")
    parser.add_argument("--output", default="sample-assets.zip", help="Output ZIP path")
    args = parser.parse_args()

    source = Path(args.source)
    output = Path(args.output)
    if not source.exists():
        raise SystemExit(f"Source directory not found: {source}")

    included = []
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
        for relative in sorted(
            path.relative_to(source)
            for path in source.rglob("*")
            if path.is_file() and path.name != "README.md"
        ):
            archive.write(source / relative, arcname=relative.as_posix())
            included.append(relative.as_posix())

    print(f"Created {output}")
    for path in included:
        print(path)


if __name__ == "__main__":
    main()
