#!/usr/bin/env python3
"""
Build script for PDF2Audio package
"""

import subprocess
import sys
import shutil
from pathlib import Path


def run_command(cmd, description):
    """Run a shell command and handle errors."""
    print(f"\n🔄 {description}...")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Error: {description} failed")
        print(f"Command: {cmd}")
        print(f"Error: {result.stderr}")
        return False
    else:
        print(f"✅ {description} completed successfully")
        if result.stdout.strip():
            print(f"Output: {result.stdout.strip()}")
        return True


def clean_build():
    """Clean previous build artifacts."""
    print("\n🧹 Cleaning build artifacts...")
    
    # Remove build directories
    dirs_to_clean = ['build/', 'dist/', '*.egg-info/']
    for pattern in dirs_to_clean:
        for path in Path('.').glob(pattern):
            if path.is_dir():
                shutil.rmtree(path)
                print(f"   Removed: {path}")
    
    print("✅ Build artifacts cleaned")


def main():
    """Main build process."""
    print("🚀 PDF2Audio Package Build Script")
    print("=" * 40)
    
    # Clean previous builds
    clean_build()
    
    # Install in development mode
    if not run_command("pip install -e .", "Installing package in development mode"):
        sys.exit(1)
    
    # Run tests (if any)
    print("\n🧪 Running basic import test...")
    if not run_command("python -c 'import pdf2audio; print(\"Import successful\")'", "Testing package import"):
        sys.exit(1)
    
    # Test CLI commands
    if not run_command("pdf2audio --help > /dev/null", "Testing CLI command"):
        sys.exit(1)
    
    # Build source distribution
    if not run_command("python setup.py sdist", "Building source distribution"):
        sys.exit(1)
    
    # Build wheel distribution
    if not run_command("python setup.py bdist_wheel", "Building wheel distribution"):
        sys.exit(1)
    
    # Show build results
    print("\n📦 Build Results:")
    print("-" * 20)
    dist_dir = Path('dist')
    if dist_dir.exists():
        for file in dist_dir.iterdir():
            print(f"   {file.name}")
    
    print("\n🎉 Build completed successfully!")
    print("\nNext steps:")
    print("1. Test the package: pip install dist/*.whl")
    print("2. Upload to PyPI: twine upload dist/*")
    print("3. Test installation: pip install pdf2audio")


if __name__ == "__main__":
    main()