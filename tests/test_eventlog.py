from devteam import eventlog


def test_record_and_read(isolated_dirs):
    eventlog.record("task", "notes", role="backend", status="ok", cost=0.01)
    eventlog.record("phase", "notes", **{"from": "backend", "to": "frontend"})
    evs = eventlog.read()
    assert len(evs) == 2
    assert evs[0]["kind"] == "task" and evs[0]["project"] == "notes"
    assert evs[1]["to"] == "frontend"


def test_read_filters_by_project(isolated_dirs):
    eventlog.record("task", "a", status="ok")
    eventlog.record("task", "b", status="ok")
    assert len(eventlog.read(project="a")) == 1
    assert eventlog.read(project="a")[0]["project"] == "a"


def test_record_redacts_secrets(isolated_dirs):
    eventlog.record("task", "x", note="leaked ghp_0123456789012345678901234567890123")
    ev = eventlog.read()[-1]
    assert "ghp_" not in ev["note"]
    assert "[REDACTED]" in ev["note"]


def test_record_never_raises_on_bad_input(isolated_dirs):
    # objects that aren't JSON-serializable must not crash the engine
    eventlog.record("weird", "x", obj=object())   # redact skips non-str; json may fail -> swallowed
    # if it didn't raise, we're good; the log may or may not contain it
    assert True


def test_format_tail_empty(isolated_dirs):
    assert "sin eventos" in eventlog.format_tail()
