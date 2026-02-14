#!/usr/bin/env python3
"""Release automation script for tagging and publishing to PyPI."""

import argparse
import subprocess
import sys


def run_command(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run command and display output."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=check)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Release automation for git-submit")
    parser.add_argument("version", help="Version to release (e.g., 0.1.0)")
    parser.add_argument("--skip-tests", action="store_true", help="Skip running tests")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually publish")

    args = parser.parse_args()

    version = args.version

    print(f"\n🚀 Preparing release {version}\n")

    # 1. Run tests
    if not args.skip_tests:
        print("\n1️⃣ Running tests...")
        run_command(["pytest", "--cov=src", "--cov-report=term"])

    # 2. Update version in pyproject.toml
    print(f"\n2️⃣ Updating version to {version}...")
    run_command([
        "python", "-c",
        f\"import toml; f = open('pyproject.toml'); c = f.read(); "
        f\"c = c.replace(version='0.1.0', version='{version}'); "
        f\"open('pyproject.toml', 'w').write(c)\"
    ])

    # 3. Update version in __init__.py
    print(f"\n3️⃣ Updating version in __init__.py...")
    run_command([
        "python", "-c",
        f\"import s; f = open('src/git_submit/__init__.py'); "
        f\"c = f.read(); c = c.replace('0.1.0', '{version}'); "
        f\"open('src/git_submit/__init__.py', 'w').write(c)\"
    ])

    # 4. Build distributions
    print("\n4️⃣ Building distributions...")
    run_command(["python", "-m", "build"])

    # 5. Check distributions
    print("\n5️⃣ Checking distributions...")
    run_command(["twine", "check", "dist/*"])

    if args.dry_run:
        print("\n⚠ DRY RUN - Skipping publish and tag")
        return 0

    # 6. Commit changes
    print(f"\n6️⃣ Committing version bump to {version}...")
    run_command([
        "git", "add",
        "pyproject.toml",
        "src/git_submit/__init__.py",
        "CHANGELOG.md",
        "README.md"
    ])
    run_command(["git", "commit", "-m", f\"Bump version to {version}\n\n\n- Version {version}\n- Update documentation\n\" ])

    # 7. Create git tag
    print(f"\n7️⃣ Creating tag v{version}...")
    run_command(["git", "tag", "-a", f"v{version}", "-m", f\"Version {version}\" ])
    run_command(["git", "push", "origin", "main"])
    run_command(["git", "push", "--tags"])

    # 8. Publish to PyPI
    print(f"\n8️⃣ Publishing to PyPI...")
    run_command(["twine", "upload", "dist/*"])

    print(f"\n✅ Release {version} complete!")
    print(f"\nNext steps:")
    print(f"  1. Create GitHub release: https://github.com/Yizai30/git-does-not-cost-life/releases/new")
    print(f"  2. Upload binaries from dist/")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Command failed: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nRelease cancelled by user.")
        sys.exit(130)
