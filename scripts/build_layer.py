"""Build the Lambda layer zip using Python's zipfile module.

Avoids PowerShell Compress-Archive permission issues with pip-installed packages.
"""

import os
import zipfile
import sys

BUILD_DIR = r"C:\hbuild\python"
OUTPUT_ZIP = r"C:\hbuild\shared-layer.zip"


def zipdir(path: str, zipf: zipfile.ZipFile, prefix: str = "") -> None:
    for root, dirs, files in os.walk(path):
        # Skip __pycache__ directories
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for file in files:
            # Skip .pyc files
            if file.endswith(".pyc"):
                continue
            file_path = os.path.join(root, file)
            arcname = os.path.join(prefix, os.path.relpath(file_path, os.path.dirname(path)))
            zipf.write(file_path, arcname)


def main() -> None:
    if not os.path.isdir(BUILD_DIR):
        print(f"ERROR: {BUILD_DIR} does not exist. Run pip install first.")
        sys.exit(1)

    print(f"Zipping {BUILD_DIR} -> {OUTPUT_ZIP}")
    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zipf:
        zipdir(BUILD_DIR, zipf, prefix="")

    size_mb = os.path.getsize(OUTPUT_ZIP) / (1024 * 1024)
    print(f"Done. Size: {size_mb:.1f} MB")


if __name__ == "__main__":
    main()
