"""Discord listener: command parsing (pure) + intervention application (mocked)."""
import pytest

from devteam import discord_listener as dl
from devteam.state import Project


# --- parse_command (pure) -----------------------------------------------------

@pytest.mark.parametrize("text,expected", [
    ("aprobado", ("approve", "")),
    ("Aprobar", ("approve", "")),
    ("ok aprobado", ("approve", "")),
    ("APPROVE", ("approve", "")),
    ("pausa", ("pause", "")),
    ("pausar el proyecto", ("pause", "")),
    ("para", ("pause", "")),
    ("stop", ("pause", "")),
    ("reanuda", ("resume", "")),
    ("continúa", ("resume", "")),
    ("resume", ("resume", "")),
    ("directriz: usa postgres 16", ("redirect", "usa postgres 16")),
    ("redirige: prioriza el login", ("redirect", "prioriza el login")),
    ("nota: el cliente quiere azul", ("redirect", "el cliente quiere azul")),
])
def test_parse_known_commands(text, expected):
    assert dl.parse_command(text) == expected


@pytest.mark.parametrize("text", [
    "hola equipo, ¿cómo va?",
    "me gusta cómo quedó lo aprobado ayer",   # command word NOT at start
    "",
    "el proyecto va genial",
])
def test_parse_ignores_normal_chat(text):
    assert dl.parse_command(text) is None


def test_channel_id_extraction():
    assert dl._channel_id_from_target("discord:123") == "123"
    assert dl._channel_id_from_target("discord:123:456") == "456"   # thread wins
    assert dl._channel_id_from_target("discord:#ops") is None       # names unsupported
    assert dl._channel_id_from_target("") is None


# --- check_interventions (fetch + send mocked) --------------------------------

def make_project(tmp):
    p = Project(name="li", path=tmp / "projects" / "li", discord_channel="discord:111:222")
    p.save()
    p.transition("pm")
    return p


def fake_msgs(*contents, bot=False):
    return [{"id": str(1000 + i), "content": c, "author": {"bot": bot, "username": "g"}}
            for i, c in enumerate(contents)]


def test_pause_and_resume_applied(isolated_dirs, monkeypatch):
    p = make_project(isolated_dirs)
    monkeypatch.setattr(dl, "listener_available", lambda: True)
    monkeypatch.setattr(dl, "send", None, raising=False)
    import devteam.discord_bridge as bridge
    monkeypatch.setattr(bridge, "send", lambda *a, **k: True)

    monkeypatch.setattr(dl, "fetch_messages", lambda cid, after=None, limit=25: fake_msgs("pausa"))
    actions = dl.check_interventions(p)
    assert actions == [f"pause({p.name})"]
    assert Project.load(p.path).paused is True

    monkeypatch.setattr(dl, "fetch_messages", lambda cid, after=None, limit=25: fake_msgs("reanuda"))
    p = Project.load(p.path)
    dl.check_interventions(p)
    assert Project.load(p.path).paused is False


def test_bot_messages_are_never_obeyed(isolated_dirs, monkeypatch):
    p = make_project(isolated_dirs)
    monkeypatch.setattr(dl, "listener_available", lambda: True)
    monkeypatch.setattr(dl, "fetch_messages",
                        lambda cid, after=None, limit=25: fake_msgs("pausa", bot=True))
    assert dl.check_interventions(p) == []
    assert Project.load(p.path).paused is False


def test_cursor_prevents_reprocessing(isolated_dirs, monkeypatch):
    p = make_project(isolated_dirs)
    monkeypatch.setattr(dl, "listener_available", lambda: True)
    import devteam.discord_bridge as bridge
    monkeypatch.setattr(bridge, "send", lambda *a, **k: True)
    seen_after = []

    def fetch(cid, after=None, limit=25):
        seen_after.append(after)
        return fake_msgs("pausa") if after is None else []

    monkeypatch.setattr(dl, "fetch_messages", fetch)
    dl.check_interventions(p)
    # cursor is persisted in the ENGINE data dir, NOT in the project repo
    from devteam.storage import load_json_safe
    cursors = load_json_safe(dl.config.DATA_DIR / "listener-cursors.json", {})
    assert cursors.get(p.name) == "1000"
    dl.check_interventions(p)            # second pass: cursor passed, nothing new
    assert seen_after[1] == "1000"


def test_unauthorized_author_is_ignored(isolated_dirs, monkeypatch):
    p = make_project(isolated_dirs)
    monkeypatch.setattr(dl, "listener_available", lambda: True)
    monkeypatch.setattr(dl, "_authorized_admin_ids", lambda: {"999"})  # only id 999
    import devteam.discord_bridge as bridge
    monkeypatch.setattr(bridge, "send", lambda *a, **k: True)
    # message author has id "g"/default, not in allowlist -> ignored
    monkeypatch.setattr(dl, "fetch_messages",
                        lambda cid, after=None, limit=25: [
                            {"id": "1", "content": "pausa",
                             "author": {"bot": False, "id": "123", "username": "intruso"}}])
    assert dl.check_interventions(p) == []
    assert Project.load(p.path).paused is False   # command NOT obeyed


def test_redirect_writes_directive_to_notes(isolated_dirs, monkeypatch):
    p = make_project(isolated_dirs)
    monkeypatch.setattr(dl, "listener_available", lambda: True)
    import devteam.discord_bridge as bridge
    monkeypatch.setattr(bridge, "send", lambda *a, **k: True)
    monkeypatch.setattr(dl, "fetch_messages",
                        lambda cid, after=None, limit=25: fake_msgs("directriz: solo postgres"))
    actions = dl.check_interventions(p)
    assert actions == [f"redirect({p.name})"]
    notes = (p.path / ".project-memory" / "NOTES.md").read_text(encoding="utf-8")
    assert "HUMAN DIRECTIVE" in notes and "solo postgres" in notes
