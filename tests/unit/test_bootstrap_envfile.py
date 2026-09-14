"""``.env`` editing keeps the operator's comments and order."""
from __future__ import annotations

from pathlib import Path

from scripts.bootstrap.envfile import read_values, set_values
from scripts.bootstrap.steps.dotenv import FIXED, REFERENCE, configure_env, is_placeholder


def test_known_keys_are_replaced_in_place_and_new_ones_appended(tmp_path: Path) -> None:
    path = tmp_path / ".env"
    path.write_text("# provider\nPROVIDER=openai   # roster\nexport OPENAI_API_KEY=sk-...\n"
                    "PLATFORM_PORT=8000\n", encoding="utf-8")
    set_values(path, {"PROVIDER": "openrouter", "OPENAI_API_KEY": "", "NEW_KEY": "a b"})
    text = path.read_text(encoding="utf-8")
    assert text.startswith("# provider\nPROVIDER=openrouter\nOPENAI_API_KEY=\nPLATFORM_PORT=8000\n")
    assert '# --- Set by python bootstrap.py ---\nNEW_KEY="a b"\n' in text
    assert read_values(path) == {"PROVIDER": "openrouter", "OPENAI_API_KEY": "",
                                 "PLATFORM_PORT": "8000", "NEW_KEY": "a b"}


def test_placeholders_are_recognised() -> None:
    assert all(is_placeholder(v) for v in ("", "  ", "sk-...", "nvapi-...", "changeme",
                                           "changeme-salt", "0" * 64, None))
    assert not any(is_placeholder(v) for v in ("sk-or-v1-abc", "pk-lf-1", "admin"))


def test_a_fresh_env_gets_one_provider_and_provisioned_langfuse(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    example = tmp_path / ".env.example"
    example.write_text("PROVIDER=openai\nOPENAI_API_KEY=sk-...\nOPENROUTER_API_KEY=sk-or-v1-...\n"
                       "LANGFUSE_PUBLIC_KEY=\nLANGFUSE_SECRET_KEY=\nLANGFUSE_INIT_USER_PASSWORD=\n"
                       "LANGFUSE_ENCRYPTION_KEY=" + "0" * 64 + "\nEMBEDDINGS_REGULATORY=openai\n",
                       encoding="utf-8")
    env = tmp_path / ".env"
    values = configure_env(env, example, key="sk-or-v1-real", mock=False)
    for key, want in FIXED.items():
        assert values[key] == want, key
    assert values["OPENROUTER_API_KEY"] == "sk-or-v1-real"
    assert values["OPENAI_API_KEY"] == ""
    assert values["LANGFUSE_PUBLIC_KEY"].startswith("pk-lf-")
    assert values["LANGFUSE_SECRET_KEY"].startswith("sk-lf-")
    assert len(values["LANGFUSE_ENCRYPTION_KEY"]) == 64 and set(values["LANGFUSE_ENCRYPTION_KEY"]) != {"0"}
    assert values["LANGFUSE_INIT_USER_PASSWORD"]


def test_an_existing_env_keeps_its_key_and_langfuse_settings(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    example = tmp_path / ".env.example"
    example.write_text("PROVIDER=openai\n", encoding="utf-8")
    env = tmp_path / ".env"
    env.write_text("PROVIDER=nvidia\nOPENROUTER_API_KEY=sk-or-v1-mine\nLANGFUSE_PUBLIC_KEY=pk-lf-keep\n"
                   "LANGFUSE_SECRET_KEY=sk-lf-keep\n", encoding="utf-8")
    values = configure_env(env, example, key=None, mock=False)
    assert values["PROVIDER"] == "openrouter"
    assert values["OPENROUTER_API_KEY"] == "sk-or-v1-mine"
    assert values["LANGFUSE_PUBLIC_KEY"] == "pk-lf-keep"
    assert values["LANGFUSE_SECRET_KEY"] == "sk-lf-keep"


def test_mock_mode_tolerates_a_missing_key(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    example = tmp_path / ".env.example"
    example.write_text("OPENROUTER_API_KEY=sk-or-v1-...\n", encoding="utf-8")
    values = configure_env(tmp_path / ".env", example, key=None, mock=True)
    assert values["OPENROUTER_API_KEY"] == ""


def test_the_reference_model_configuration_fills_blanks_only(tmp_path: Path, monkeypatch) -> None:
    """A clone audits on the configuration the reference Mariposa result used (T-20260914-066)."""
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    example = tmp_path / ".env.example"
    example.write_text("OPENROUTER_API_KEY=sk-or-v1-...\nOPENROUTER_MODEL=\nOPENROUTER_PROVIDER=\n",
                       encoding="utf-8")
    fresh = configure_env(tmp_path / ".env", example, key="sk-or-v1-real", mock=False)
    assert {k: fresh[k] for k in REFERENCE} == REFERENCE
    chosen = tmp_path / "chosen.env"
    chosen.write_text("OPENROUTER_API_KEY=sk-or-v1-real\nOPENROUTER_MODEL=other/model\n"
                      "OPENROUTER_PROVIDER=other/endpoint\n", encoding="utf-8")
    kept = configure_env(chosen, example, key=None, mock=False)
    assert (kept["OPENROUTER_MODEL"], kept["OPENROUTER_PROVIDER"]) == ("other/model", "other/endpoint")
