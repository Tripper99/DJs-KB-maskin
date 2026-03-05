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


def get_bundled_data(project_root):
    """Get files to bundle INSIDE the executable (icons only)"""
    datas = []
    for ext in ("ico", "png", "icns"):
        icon = project_root / f"Agg-med-smor-v4-transperent.{ext}"
        if icon.exists():
            datas.append((str(icon), "."))
    return datas


def get_companion_files(project_root):
    """Get files to place NEXT TO the executable (CSV, Manual, etc.)"""
    files = []

    # Manual (PDF preferred, fallback to docx)
    manual_pdf = project_root / "Manual.pdf"
    manual_docx = project_root / "Manual.docx"
    if manual_pdf.exists():
        files.append(manual_pdf)
    elif manual_docx.exists():
        files.append(manual_docx)

    # CSV files
    for csv_file in project_root.glob("titles_bibids*.csv"):
        files.append(csv_file)

    return files


def build_pyinstaller_args(project_root, version):
    """Build PyInstaller command-line arguments"""
    icon_path = get_icon_path(project_root)
    bundled_data = get_bundled_data(project_root)
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

    # Bundled data (icons only)
    for src, dst in bundled_data:
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
        # Use --onedir on macOS to produce a proper .app bundle
        # (--onefile + --windowed is deprecated and causes CI hangs)
        args[args.index("--onefile")] = "--onedir"

    # Entry point
    args.append(str(project_root / "app.py"))

    return args


def copy_companion_files(project_root, dist_dir):
    """Copy companion files (CSV, Manual) next to the executable"""
    files = get_companion_files(project_root)
    copied = []
    for f in files:
        dest = dist_dir / f.name
        shutil.copy2(str(f), str(dest))
        copied.append(dest)
        print(f"  Copied: {f.name}")
    return copied


def post_build_macos(project_root, dist_dir, version):
    """Post-build steps for macOS: create DMG with .app bundle + companion files"""
    output_name = f"DJs_KB_maskin_v{version}"
    app_bundle = dist_dir / f"{output_name}.app"

    if not app_bundle.exists():
        print(f"WARNING: Expected .app bundle not found at {app_bundle}")
        print("Falling back to onedir output...")
        app_bundle = dist_dir / output_name

    # Create staging directory for DMG contents
    dmg_name = f"DJs_KB_maskin_v{version}-macos"
    staging_dir = project_root / f"_staging_{dmg_name}"
    if staging_dir.exists():
        shutil.rmtree(staging_dir)
    staging_dir.mkdir()

    # Copy .app bundle into staging
    dest_app = staging_dir / app_bundle.name
    shutil.copytree(str(app_bundle), str(dest_app))
    print(f"  Staged: {app_bundle.name}")

    # Create Applications symlink for drag-to-install
    apps_link = staging_dir / "Applications"
    apps_link.symlink_to("/Applications")
    print("  Created: Applications symlink")

    # Copy companion files into staging
    copy_companion_files(project_root, staging_dir)

    # Create DMG using hdiutil (preserves permissions and executable bits)
    dmg_path = dist_dir / f"{dmg_name}.dmg"
    subprocess.run([
        "hdiutil", "create",
        "-volname", f"DJs KB-maskin v{version}",
        "-srcfolder", str(staging_dir),
        "-ov",
        "-format", "UDZO",  # compressed DMG
        str(dmg_path),
    ], check=True)

    # Clean up staging
    shutil.rmtree(staging_dir)

    print(f"Created: {dmg_path}")
    return dmg_path


def post_build_linux(project_root, dist_dir, version):
    """Post-build steps for Linux: make binary executable, copy companion files"""
    binary = dist_dir / f"DJs_KB_maskin_v{version}"
    if binary.exists():
        binary.chmod(0o755)
        print(f"Made executable: {binary}")

    print("Copying companion files next to executable...")
    copy_companion_files(project_root, dist_dir)
    return binary


def post_build_windows(project_root, dist_dir):
    """Post-build steps for Windows: copy companion files"""
    print("Copying companion files next to executable...")
    copy_companion_files(project_root, dist_dir)


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
    print()

    # Platform-specific post-build
    if sys.platform == "darwin":
        artifact = post_build_macos(project_root, dist_dir, version)
    elif sys.platform.startswith("linux"):
        artifact = post_build_linux(project_root, dist_dir, version)
    else:
        post_build_windows(project_root, dist_dir)
        artifact = dist_dir / f"DJs_KB_maskin_v{version}.exe"

    if artifact and Path(artifact).exists():
        size_mb = Path(artifact).stat().st_size / (1024 * 1024)
        print(f"Output: {artifact} ({size_mb:.1f} MB)")
    else:
        print(f"Output directory: {dist_dir}")
        for f in dist_dir.iterdir():
            print(f"  {f.name}")


if __name__ == "__main__":
    if "--test" in sys.argv:
        version = get_version()
        print(f"Version: {version}")
        print(f"Platform: {platform.system()}")
        print(f"Icon: {get_icon_path(Path(__file__).parent)}")
        print(f"Bundled data: {get_bundled_data(Path(__file__).parent)}")
        print(f"Companion files: {get_companion_files(Path(__file__).parent)}")
    else:
        build()
