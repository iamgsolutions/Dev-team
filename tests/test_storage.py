import json

from devteam import storage


def test_atomic_write_and_load(tmp_path):
    p = tmp_path / "x.json"
    storage.atomic_write_json(p, {"a": 1})
    assert json.loads(p.read_text(encoding="utf-8")) == {"a": 1}
    assert not list(tmp_path.glob("*.tmp"))   # no temp leftovers


def test_load_json_safe_missing_returns_default(tmp_path):
    assert storage.load_json_safe(tmp_path / "nope.json", {"d": True}) == {"d": True}


def test_load_json_safe_corrupt_quarantines_and_defaults(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{ this is not json", encoding="utf-8")
    out = storage.load_json_safe(p, {"ok": 1})
    assert out == {"ok": 1}
    assert (tmp_path / "bad.json.corrupt").exists()   # quarantined for forensics
    assert not p.exists()


def test_redact_masks_known_secret_shapes():
    cases = [
        "sk-abcdefghijklmnopqrstuvwxyz0123",
        "ghp_0123456789012345678901234567890123",
        "AIzaSyA1234567890123456789012345678901234",
        "aws_secret_access_key = ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcd",
        "password: 'supersecret123'",
        "sk_live_0123456789abcdef0123",
    ]
    for c in cases:
        assert "[REDACTED]" in storage.redact(c), c


def test_redact_leaves_clean_text():
    txt = "El proyecto notes pasó los tests y la fase backend está completa."
    assert storage.redact(txt) == txt


def test_atomic_write_overwrites_existing(tmp_path):
    p = tmp_path / "y.json"
    storage.atomic_write_json(p, {"v": 1})
    storage.atomic_write_json(p, {"v": 2})
    assert json.loads(p.read_text(encoding="utf-8")) == {"v": 2}
