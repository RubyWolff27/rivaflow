"""Tests for voice-extraction normalization + movement resolution (Wave 3, MA-F4).

The extraction LLM historically emitted class_type spellings the ClassType enum
doesn't contain ("nogi", "open_mat", "private") — stored verbatim, those
sessions silently vanished from Game Distribution and every class filter. And
technique names were saved as free strings, never glossary movement IDs.
"""

from unittest.mock import patch

from rivaflow.core.services.grapple.session_extraction_service import (
    EXTRACTION_SYSTEM_PROMPT,
    normalize_class_type,
    resolve_movements,
)

_GLOSSARY = "rivaflow.db.repositories.GlossaryRepository"

_MOVEMENTS = [
    {"id": 3, "name": "Armbar", "aliases": '["Juji Gatame", "Arm Bar"]'},
    {"id": 7, "name": "Triangle Choke", "aliases": '["Triangle", "Sankaku"]'},
    {"id": 12, "name": "De La Riva Guard", "aliases": "[]"},
]


class TestClassTypeNormalization:
    def test_llm_spellings_map_to_canonical(self):
        assert normalize_class_type("nogi") == "no-gi"
        assert normalize_class_type("No Gi") == "no-gi"
        assert normalize_class_type("no_gi") == "no-gi"
        assert normalize_class_type("open_mat") == "open-mat"
        assert normalize_class_type("Open Mat") == "open-mat"
        assert normalize_class_type("comp") == "competition"

    def test_private_maps_to_gi(self):
        """'private' isn't in the enum — a private is a gi lesson."""
        assert normalize_class_type("private") == "gi"

    def test_canonical_values_pass_through(self):
        for v in ("gi", "no-gi", "open-mat", "drilling", "competition", "s&c"):
            assert normalize_class_type(v) == v

    def test_unknown_and_empty_default_to_gi(self):
        assert normalize_class_type("underwater basket weaving") == "gi"
        assert normalize_class_type(None) == "gi"
        assert normalize_class_type("") == "gi"

    def test_prompt_emits_canonical_enum(self):
        """The extraction prompt itself must ask for canonical values (fix at
        the source; normalization stays as the safety net)."""
        assert "no-gi" in EXTRACTION_SYSTEM_PROMPT
        assert "nogi" not in EXTRACTION_SYSTEM_PROMPT.replace("no-gi", "")
        assert "private" not in EXTRACTION_SYSTEM_PROMPT


class TestMovementResolution:
    def _resolve(self, names):
        with patch(_GLOSSARY) as repo:
            repo.list_all.return_value = _MOVEMENTS
            return resolve_movements(names)

    def test_exact_and_case_insensitive_match(self):
        resolved, unresolved = self._resolve(["armbar", "Triangle Choke"])
        assert [r["movement_id"] for r in resolved] == [3, 7]
        assert unresolved == []

    def test_alias_match(self):
        resolved, unresolved = self._resolve(["juji gatame", "sankaku"])
        assert [r["movement_id"] for r in resolved] == [3, 7]
        assert unresolved == []

    def test_punctuation_folded(self):
        resolved, _ = self._resolve(["de-la-riva guard", "arm bar"])
        assert [r["movement_id"] for r in resolved] == [12, 3]

    def test_unmatched_stays_free_string_never_guessed(self):
        resolved, unresolved = self._resolve(["berimbolo"])
        assert resolved == []
        assert unresolved == ["berimbolo"]

    def test_duplicates_resolve_once(self):
        resolved, unresolved = self._resolve(["Armbar", "juji gatame", "arm bar"])
        assert [r["movement_id"] for r in resolved] == [3]
        assert unresolved == []

    def test_mixed_batch(self):
        resolved, unresolved = self._resolve(
            ["Armbar", "flying wizard lock", "triangle"]
        )
        assert [r["movement_id"] for r in resolved] == [3, 7]
        assert unresolved == ["flying wizard lock"]
