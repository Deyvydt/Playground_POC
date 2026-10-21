"""services/gateway/gateway_config.py: Langfuse se activa solo con credenciales y sin texto de mensajes."""
import importlib.util
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[3]

_spec = importlib.util.spec_from_file_location("gateway_config", REPO / "services" / "gateway" / "gateway_config.py")
gateway_config = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gateway_config)


@pytest.fixture(autouse=True)
def sin_langfuse(monkeypatch):
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)


def test_sin_credenciales_se_usa_config_yaml_sin_cambios(tmp_path):
    assert gateway_config.effective_config(tmp_path / "x.yaml") == REPO / "services" / "gateway" / "config.yaml"
    assert not (tmp_path / "x.yaml").exists()


@pytest.mark.tabla_decision
def test_con_una_sola_credencial_no_se_activa(monkeypatch, tmp_path):
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk")
    assert gateway_config.langfuse_enabled() is False


def test_con_credenciales_activa_callbacks_sin_contenido_y_conserva_el_resto(monkeypatch, tmp_path):
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk")
    destino = gateway_config.effective_config(tmp_path / "gateway-config.yaml")
    config = yaml.safe_load(destino.read_text(encoding="utf-8"))
    original = yaml.safe_load((REPO / "services" / "gateway" / "config.yaml").read_text(encoding="utf-8"))
    assert config["litellm_settings"]["success_callback"] == ["langfuse"]
    assert config["litellm_settings"]["failure_callback"] == ["langfuse"]
    assert config["litellm_settings"]["turn_off_message_logging"] is True
    assert config["model_list"] == original["model_list"]
    assert config["general_settings"] == original["general_settings"]


def test_config_del_gateway_no_contiene_secretos():
    texto = (REPO / "services" / "gateway" / "config.yaml").read_text(encoding="utf-8")
    assert "os.environ/LITELLM_MASTER_KEY" in texto
    assert "sk-" not in texto.replace("os.environ/", "")


def test_los_modelos_de_chat_locales_tienen_costo_interno_para_que_el_presupuesto_aplique():
    """Spec 002 CA-3.4: con costo 0 LiteLLM omite el chequeo de presupuesto."""
    config = yaml.safe_load((REPO / "services" / "gateway" / "config.yaml").read_text(encoding="utf-8"))
    chat = [m for m in config["model_list"] if m.get("model_info", {}).get("mode") != "embedding"]
    assert chat and all(m["model_info"]["input_cost_per_token"] > 0 for m in chat)
