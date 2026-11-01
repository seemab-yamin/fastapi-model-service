import pytest

from app.config import ConfigError, load_config


def write(tmp_path, text):
    p = tmp_path / "config.yaml"
    p.write_text(text)
    return p


def test_defaults_when_file_empty(tmp_path):
    s = load_config(write(tmp_path, ""))
    assert s.model.task == "detection"


def test_missing_file(tmp_path):
    with pytest.raises(ConfigError, match="not found"):
        load_config(tmp_path / "nope.yaml")


def test_rejects_non_onnx(tmp_path):
    with pytest.raises(ConfigError, match="onnx"):
        load_config(write(tmp_path, "model:\n  path: models/m.pt\n"))


def test_rejects_unknown_key(tmp_path):
    with pytest.raises(ConfigError):
        load_config(write(tmp_path, "modle:\n  path: x.onnx\n"))


def test_rejects_bad_threshold(tmp_path):
    with pytest.raises(ConfigError, match="confidence_threshold"):
        load_config(write(tmp_path, "inference:\n  confidence_threshold: 2\n"))
