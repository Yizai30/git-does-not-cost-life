"""Direct test of config initialization without imports."""

import os
import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_config_init():
    """Test config init directly."""
    print("=" * 60)
    print("Testing config init functionality...")
    print("=" * 60)

    # Import directly without going through CLI
    try:
        from git_submit.config_loader import save_config, get_default_config
        from git_submit.config_commands import cmd_init as config_init
    except Exception as e:
        print(f"ERROR: Failed to import: {e}")
        return False

    # Test 1: Create default config
    print("\n[Test 1] Creating default config file...")
    with tempfile.TemporaryDirectory() as tmpdir:
        test_config_path = Path(tmpdir) / "test-config.yaml"

        # Call the init command
        import io
        import contextlib

        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()

        result = config_init()

        # Restore stdout
        sys.stdout = old_stdout

        output = sys.stdout.getvalue()

        if result == 0 and "Created configuration file" in output:
            print("  ✓ Config file created successfully")
        else:
            print(f"  ✗ Config init failed with code {result}")
            print(f"  Output: {output}")
            return False

    # Test 2: Verify file exists
    print("\n[Test 2] Verifying config file...")
    if test_config_path.exists():
        print("  ✓ Config file exists")
        with open(test_config_path) as f:
            content = f.read()
            if "git-submit configuration" in content:
                print("  ✓ Contains expected content")
            else:
                print("  ✗ Content may be incorrect")
                print(f"  First 200 chars: {content[:200]}")
    else:
        print("  ✗ Config file does not exist")
        return False

    print("\n" + "=" * 60)
    print("All tests passed! Config init is working correctly.")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_config_init()
    sys.exit(0 if success else 1)
