from devteam import catalog


def test_register_and_get(isolated_dirs):
    catalog.register("auth-jwt", "Login + JWT + refresh", capabilities=["auth", "jwt"],
                     dependencies=["bcrypt"], stack="fastapi", origin_project="notes")
    c = catalog.get("auth-jwt")
    assert c["summary"].startswith("Login")
    assert "auth" in c["capabilities"]
    assert c["origin_project"] == "notes"


def test_register_is_idempotent_and_merges_caps(isolated_dirs):
    catalog.register("pay", "Stripe payments", capabilities=["payments"])
    catalog.register("pay", "Stripe payments v2", capabilities=["stripe"])
    c = catalog.get("pay")
    assert set(c["capabilities"]) == {"payments", "stripe"}
    assert c["summary"] == "Stripe payments v2"
    assert len(catalog.all_components()) == 1   # same name -> one entry


def test_search_by_capability_and_name(isolated_dirs):
    catalog.register("auth-jwt", "login", capabilities=["auth"])
    catalog.register("admin-panel", "dashboard", capabilities=["admin", "ui"])
    assert {c["name"] for c in catalog.search("auth")} == {"auth-jwt"}
    assert {c["name"] for c in catalog.search("admin")} == {"admin-panel"}
    assert catalog.search("nonexistent") == []
    assert len(catalog.search("")) == 2          # empty -> all


def test_mark_used_tracks_projects(isolated_dirs):
    catalog.register("auth-jwt", "login")
    catalog.mark_used("auth-jwt", "proj1")
    catalog.mark_used("auth-jwt", "proj1")       # dedup
    catalog.mark_used("auth-jwt", "proj2")
    assert catalog.get("auth-jwt")["used_in"] == ["proj1", "proj2"]


def test_format_report(isolated_dirs):
    assert "vacío" in catalog.format_report()
    catalog.register("auth-jwt", "login seguro", capabilities=["auth"])
    rep = catalog.format_report()
    assert "auth-jwt" in rep and "login seguro" in rep
