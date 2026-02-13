"""Git wrapper for executing push commands."""

import os
import subprocess
from dataclasses import dataclass
from typing import Literal


@dataclass
class GitResult:
    """Result of git command execution."""

    success: bool
    exit_code: int
    stdout: str
    stderr: str


class GitError(Exception):
    """Raised when git operation fails."""

    def __init__(self, message: str, exit_code: int, stdout: str, stderr: str):
        self.message = message
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        super().__init__(message)


def get_git_executable() -> str:
    """
    Get git executable path, respecting GIT_EXEC_PATH environment variable.

    Returns:
        Path to git executable

    Raises:
        FileNotFoundError: If git not found
    """
    # Check environment override
    if "GIT_EXEC_PATH" in os.environ:
        git_path = os.environ["GIT_EXEC_PATH"]
        if os.path.exists(git_path):
            return git_path
        raise FileNotFoundError(
            f"Git executable not found at GIT_EXEC_PATH: {git_path}"
        )

    # Check for git in PATH
    git_cmd = "git.exe" if os.name == "nt" else "git"

    try:
        result = subprocess.run(
            [git_cmd, "--version"],
            capture_output=True,
            text=True,
            check=True,
        )
        return git_cmd
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        raise FileNotFoundError(
            f"Git not found in PATH. Install from https://git-scm.com/\n"
            f"Error: {e}"
        )


def check_git_available() -> None:
    """
    Check if git is available, fail fast if not.

    Raises:
        FileNotFoundError: If git not found
    """
    get_git_executable()


def get_current_branch() -> str | None:
    """
    Get current git branch name.

    Returns:
        Branch name or None if not in a git repository
    """
    git = get_git_executable()

    try:
        result = subprocess.run(
            [git, "branch", "--show-current"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip() or None
    except subprocess.CalledProcessError:
        return None


def push(
    remote: str,
    branch: str,
    all_branches: bool = False,
    force: bool = False,
    dry_run: bool = False,
) -> GitResult:
    """
    Execute git push command.

    Args:
        remote: Remote name (e.g., 'origin')
        branch: Branch name to push
        all_branches: If True, push all branches (--all flag)
        force: If True, use force push
        dry_run: If True, don't actually push

    Returns:
        GitResult with execution details

    Raises:
        GitError: If git command fails critically
    """
    git = get_git_executable()
    cmd = [git, "push"]

    if all_branches:
        cmd.append("--all")
    else:
        cmd.extend([remote, branch])

    if force:
        cmd.append("--force")

    if dry_run:
        print(f"[DRY RUN] Would execute: {' '.join(cmd)}")
        return GitResult(success=True, exit_code=0, stdout="", stderr="")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,  # Don't raise on non-zero exit
        )

        success = result.returncode == 0
        return GitResult(
            success=success,
            exit_code=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
        )
    except Exception as e:
        raise GitError(
            message=f"Failed to execute git push: {e}",
            exit_code=-1,
            stdout="",
            stderr=str(e),
        )


def verify_push(remote: str, branch: str) -> bool:
    """
    Verify that remote branch was updated successfully.

    Args:
        remote: Remote name
        branch: Branch name

    Returns:
        True if remote branch exists, False otherwise
    """
    git = get_git_executable()

    try:
        result = subprocess.run(
            [git, "ls-remote", remote, branch],
            capture_output=True,
            text=True,
            check=True,
        )
        # Check if branch is in output
        return branch in result.stdout
    except subprocess.CalledProcessError:
        return False


PERMANENT_ERROR_PATTERNS = [
    "repository not found",
    "404",
    "permission denied",
    "does not exist",
    "could not read",
]
