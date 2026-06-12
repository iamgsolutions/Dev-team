"""Git worktree manager (S4b) - one isolated worktree per task branch."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path


class GitError(Exception):
    pass


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if proc.returncode != 0:
        raise GitError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout.strip()


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:50] or "task"


def ensure_repo(path: Path) -> None:
    """Init a git repo with an initial commit if not already one."""
    if (path / ".git").exists():
        return
    path.mkdir(parents=True, exist_ok=True)
    _git(path, "init")
    # an initial commit is required before worktrees can be added
    (path / ".gitkeep").write_text("", encoding="utf-8")
    _git(path, "add", "-A")
    _git(path, "commit", "-m", "chore: init repository")


def create(repo: Path, task_name: str) -> tuple[Path, str]:
    """Create (or reuse) worktree+branch for a task. Idempotent: batched
    retries after a deferred/rate-limited attempt land in the same worktree."""
    branch = f"task/{slugify(task_name)}"
    wt_root = repo.parent / f"{repo.name}-worktrees"
    wt_root.mkdir(parents=True, exist_ok=True)
    wt_path = wt_root / slugify(task_name)
    if wt_path.exists():
        if (wt_path / ".git").exists():
            return wt_path, branch          # reuse existing task worktree
        raise GitError(f"path exists but is not a worktree: {wt_path}")
    _git(repo, "worktree", "add", "-b", branch, str(wt_path))
    return wt_path, branch


def commit_all(worktree: Path, message: str) -> bool:
    """Stage and commit everything in the worktree. False if nothing to commit."""
    _git(worktree, "add", "-A")
    status = _git(worktree, "status", "--porcelain")
    if not status:
        return False
    _git(worktree, "commit", "-m", message)
    return True


def remove(repo: Path, worktree: Path, force: bool = False) -> None:
    args = ["worktree", "remove", str(worktree)]
    if force:
        args.append("--force")
    _git(repo, *args)


def merge_branch(repo: Path, branch: str, message: str | None = None) -> None:
    """Merge a task branch into the repo's current branch (gates passed)."""
    args = ["merge", "--no-ff", branch]
    if message:
        args += ["-m", message]
    _git(repo, *args)
