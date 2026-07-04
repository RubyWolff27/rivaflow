"""Short bookmarkable cockpit URL (root /cockpit)."""

from __future__ import annotations


class TestShortCockpit:
    def test_root_cockpit_needs_key(self, client):
        r = client.get("/cockpit")
        assert r.status_code == 401
        assert "YOUR_KEY" in r.text  # the prompt to add ?key= once

    def test_root_cockpit_bad_key(self, client):
        r = client.get("/cockpit", params={"key": "rf_pk_bogus"})
        assert r.status_code == 401
