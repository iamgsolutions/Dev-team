"""Git worktree manager (S4b) - one isolated worktree per task branch."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path


class GitError(Exception):
    pass


def _git(repo: Path, *args: str, timeout: int = 120) -> str:
    # timeout (audit fix): a hung git (stale index.lock, slow disk) would
    # otherwise freeze the single-threaded 24/7 daemon forever.
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            stdin=subprocess.DEVNULL, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise GitError(f"git {' '.join(args)} timed out after {timeout}s")
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


def commit_all(worktree: Path, message: str, model: str | None = None,
               role: str | None = None) -> bool:
    """Stage and commit everything in the worktree. False if nothing to commit.

    When model/role are given they are appended as git trailers so every
    change is forever attributable to the model that produced it:
        Model: opencode/deepseek-v4-flash-free
        Role: backend
    """
    _git(worktree, "add", "-A")
    status = _git(worktree, "status", "--porcelain")
    if not status:
        return False
    trailers = []
    if model:
        trailers.append(f"Model: {model}")
    if role:
        trailers.append(f"Role: {role}")
    if trailers:
        message = message + "\n\n" + "\n".join(trailers)
    _git(worktree, "commit", "-m", message)
    return True


def has_changes_vs_base(worktree: Path, base: str = "main") -> bool:
    """True if the worktree produced changes vs the base branch (i.e. the agent
    actually wrote something). Used to catch a brain that returns 'ok' but commits
    nothing - an empty worktree would otherwise sail through gates + audit."""
    try:
        committed = _git(worktree, "diff", "--name-only", f"{base}...HEAD").strip()
        uncommitted = _git(worktree, "status", "--porcelain").strip()
    except GitError:
        return True  # can't tell -> don't block (fail open, the gates still run)
    return bool(committed or uncommitted)


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


def delete_branch(repo: Path, branch: str) -> None:
    """Delete a (merged) branch so a same-named phase re-run can recreate it."""
    try:
        _git(repo, "branch", "-D", branch)
    except GitError:
        pass
