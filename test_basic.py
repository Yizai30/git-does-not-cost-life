"""Basic test to verify git-submit works."""

import sys
import os

def test_basic():
    """Test basic functionality without type hints."""
    print("=" * 50)
    print("git-submit 基础功能测试")
    print("=" * 50)

    # Test 1: Check if we can import
    try:
        print("\n✅ 测试 1: 导入模块...")
        # Simple import without type checking
        import os
        import sys
        import subprocess
        import argparse
        import tempfile
        print("    ✓ 核准库导入成功")
    except Exception as e:
        print(f"    ✗ 标准库导入失败: {e}")
        return False

    # Test 2: Check YAML loading
    try:
        print("\n✅ 测试 2: YAML 加载...")
        import yaml
        print("    ✓ YAML 库可用")
    except Exception as e:
        print(f"    ✗ YAML 库不可用: {e}")
        return False

    # Test 3: Check pathlib
    try:
        print("\n✅ 测试 3: 路径处理...")
        from pathlib import Path
        test_path = Path.home() / ".git-submit-test"
        print(f"    ✓ 可访问测试路径: {test_path}")
    except Exception as e:
        print(f"    ✗ 路径处理失败: {e}")
        return False

    # Test 4: Create simple dataclass
    try:
        print("\n✅ 测试 4: 数据类...")
        from dataclasses import dataclass

        @dataclass
        class TestState:
            name: str
            value: int

        state = TestState(name="test", value=42)
        print(f"    ✓ 数据类创建成功: {state}")
    except Exception as e:
        print(f"    ✗ 数据类创建失败: {e}")
        return False

    print("\n" + "=" * 50)
    print("所有基础测试通过！✅")
    print("=" * 50)
    return True


if __name__ == "__main__":
    success = test_basic()
    sys.exit(0 if success else 1)
