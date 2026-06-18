"""Memory handoff verification - a REAL content change is required, not a touch."""
import os
import time

from devteam import memory


def _init(tmp_path):
    memory.init_memory(tmp_path, "proj", "a brief")
    return tmp_path


def test_real_change_passes_handoff(tmp_path):
    _init(tmp_path)
    before = memory.snapshot_memory(tmp_path)
    state = memory.memory_dir(tmp_path) / memory.STATE_MD
    state.write_text(state.read_text(encoding="utf-8") + "\n## Done\nbuilt X\n",
                     encoding="utf-8")
    assert memory.verify_handoff(tmp_path, before) is True


def test_noop_touch_does_not_pass_handoff(tmp_path):
    _init(tmp_path)
    before = memory.snapshot_memory(tmp_path)
    # re-save IDENTICAL content and bump mtime into the future: the old
    # mtime-only check would PASS; the content check must REJECT it.
    future = time.time() + 60
    for name in (memory.STATE_MD, memory.NOTES_MD):
        f = memory.memory_dir(tmp_path) / name
        f.write_text(f.read_text(encoding="utf-8"), encoding="utf-8")
        os.utime(f, (future, future))
    assert memory.verify_handoff(tmp_path, before) is False


def test_unchanged_does_not_pass_handoff(tmp_path):
    _init(tmp_path)
    before = memory.snapshot_memory(tmp_path)
    assert memory.verify_handoff(tmp_path, before) is False
