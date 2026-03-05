#!/usr/bin/env python3
"""
Cross-platform build script for DJs KB-maskin.
Used by GitHub Actions CI/CD and can be run locally.

Usage:
    python build.py          # Build for current platform
    python build.py --test   # Test import only (no build)
"""

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def get_version():
    """Read version from src/version.py"""
    version_file = Path(__file__).parent / "src" / "version.py"
    with open(version_file) as f:
        for line in f:
            if line.startswith("__version__"):
                return line.split('"')[1]
    raise RuntimeError("Could not find version in src/version.py")


def get_icon_path(project_root):
    """Get platform-appropriate icon path"""
    if sys.platform == "darwin":
        return project_root / "Agg-med-smor-v4-transperent.icns"
    elif sys.platform == "win32":
        return project_root / "Agg-med-smor-v4-transperent.ico"
    else:
        return project_root / "Agg-med-smor-v4-transperent.png"


def get_data_files(project_root):
    """Get list of data files to bundle"""
    datas = []

    # Icon files - bundle all formats
    for ext in ("ico", "png", "icns"):
        icon = project_root / f"Agg-med-smor-v4-transperent.{ext}"
        if icon.exists():
            datas.append((str(icon), "."))

    # Manual (PDF preferred, fallback to docx)
    manual_pdf = project_root / "Manual.pdf"
    manual_docx = project_root / "Manual.docx"
    if manual_pdf.exists():
        datas.append((str(manual_pdf), "."))
    elif manual_docx.exists():
        datas.append((str(manual_docx), "."))

    # CSV files
    for csv_file in project_root.glob("titles_bibids*.csv"):
        datas.append((str(csv_file), "."))

    return datas


def build_pyinstaller_args(project_root, version):
    """Build PyInstaller command-line arguments"""
    icon_path = get_icon_path(project_root)
    data_files = get_data_files(project_root)
    output_name = f"DJs_KB_maskin_v{version}"

    args = [
        sys.executable, "-m", "PyInstaller",
        "--name", output_name,
        "--onefile",
        "--windowed",
        "--noconfirm",
    ]

    # Icon
    if icon_path.exists():
        args.extend(["--icon", str(icon_path)])

    # Data files
    for src, dst in data_files:
        args.extend(["--add-data", f"{src}{os.pathsep}{dst}"])

    # Hidden imports needed by the app
    hidden_imports = [
        "ttkbootstrap",
        "PIL._tkinter_finder",
        "google.auth.transport.requests",
        "google.oauth2.credentials",
        "googleapiclient.discovery",
        "googleapiclient.errors",
    ]
    for imp in hidden_imports:
        args.extend(["--hidden-import", imp])

    # Platform-specific options
    if sys.platform == "darwin":
        args.append("--argv-emulation")

    # Entry point
    args.append(str(project_root / "app.py"))

    return args


def post_build_macos(dist_dir, version):
    """Post-build steps for macOS: create .zip of .app bundle"""
    app_name = f"DJs_KB_maskin_v{version}"
    app_path = dist_dir / f"{app_name}.app"

    if app_path.exists():
        zip_name = f"DJs_KB_maskin_v{version}-macos"
        shutil.make_archive(str(dist_dir / zip_name), "zip", dist_dir, f"{app_name}.app")
        print(f"Created: {dist_dir / zip_name}.zip")
        return dist_dir / f"{zip_name}.zip"

    # For --onefile mode, the output is a single binary
    binary = dist_dir / app_name
    if binary.exists():
        zip_name = f"DJs_KB_maskin_v{version}-macos"
        shutil.make_archive(str(dist_dir / zip_name), "zip", dist_dir, app_name)
        print(f"Created: {dist_dir / zip_name}.zip")
        return dist_dir / f"{zip_name}.zip"

    return None


def post_build_linux(dist_dir, version):
    """Post-build steps for Linux: make binary executable"""
    binary = dist_dir / f"DJs_KB_maskin_v{version}"
    if binary.exists():
        binary.chmod(0o755)
        print(f"Made executable: {binary}")
    return binary


def build():
    """Main build function"""
    project_root = Path(__file__).parent.resolve()
    version = get_version()
    dist_dir = project_root / "dist"

    print(f"Building DJs KB-maskin v{version}")
    print(f"Platform: {platform.system()} ({sys.platform})")
    print(f"Python: {sys.version}")
    print(f"Project root: {project_root}")
    print()

    # Build PyInstaller command
    args = build_pyinstaller_args(project_root, version)
    print(f"Running: {' '.join(args[:6])}...")
    print()

    # Run PyInstaller
    result = subprocess.run(args, cwd=str(project_root))
    if result.returncode != 0:
        print(f"Build failed with exit code {result.returncode}")
        sys.exit(1)

    print()
    print("Build completed successfully!")

    # Platform-specific post-build
    if sys.platform == "darwin":
        artifact = post_build_macos(dist_dir, version)
    elif sys.platform.startswith("linux"):
        artifact = post_build_linux(dist_dir, version)
    else:
        artifact = dist_dir / f"DJs_KB_maskin_v{version}.exe"

    if artifact and Path(artifact).exists():
        size_mb = Path(artifact).stat().st_size / (1024 * 1024)
        print(f"Output: {artifact} ({size_mb:.1f} MB)")
    else:
        print(f"Output directory: {dist_dir}")
        # List what was produced
        for f in dist_dir.iterdir():
            print(f"  {f.name}")


if __name__ == "__main__":
    if "--test" in sys.argv:
        version = get_version()
        print(f"Version: {version}")
        print(f"Platform: {platform.system()}")
        print(f"Icon: {get_icon_path(Path(__file__).parent)}")
        print(f"Data files: {get_data_files(Path(__file__).parent)}")
    else:
        build()
