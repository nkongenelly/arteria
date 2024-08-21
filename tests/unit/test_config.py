import yaml
import pytest
import tempfile
import jsonschema

from arteria.models.config import Config
from jsonschema.exceptions import ValidationError
from arteria.config_schemas.schema_arteria_runfolder import runfolder_schema


@pytest.fixture()
def config_dict():
    return {
        "port": 8080,
        "completed_marker_grace_minutes": 10,
        "monitored_directories": ["/tmp/path1", "/tmp/path2"],
        "logger_config_file": "/tmp/path3"
    }


@pytest.fixture()
def config(config_dict):
    config_object = Config.new(config_dict, exist_ok=False, schema=runfolder_schema)

    yield config_object

    Config.clear()


def test_config_init(config):
    """
    Tests Config() always returns the same object in memory
    """
    assert Config() == config 


def test_config_exist_ok(config):
    new_config = {"abc": "123"}

    Config.new(new_config, exist_ok=True)
    assert config.to_dict() == new_config
    assert Config().to_dict() == new_config


def test_config_to_dict(config, config_dict):
    assert config.to_dict() == config_dict


def test_config_getitem(config, config_dict):
    for key, value in config_dict.items():
        assert config[key] == value


def test_config_get(config, config_dict):
    for key, value in config_dict.items():
        assert config.get(key) == value

    assert config.get("port", "123") == config_dict["port"]
    assert config.get("new_key", "123") == "123"


def test_config_immutable(config, config_dict):
    with pytest.raises(TypeError):
        config["url"] = "http://fakeurl.com"

    with pytest.raises(TypeError):
        config["port"] = "1337"

    config.to_dict()["port"] = 0
    assert config["port"] == config_dict["port"]


def test_config_validation():
    new_config = {"abc": "123"}

    with pytest.raises(ValidationError):
        Config.new(new_config, schema=runfolder_schema)


def test_default_config_from_scratch():
    defaults = {"default_variable": 1}
    config = Config(defaults)
    assert config.to_dict() == defaults

    assert config["default_variable"] == defaults["default_variable"]
    defaults["default_variable"] = 0
    assert config["default_variable"] != defaults["default_variable"]


def test_default_config_from_existing_config(config, config_dict):
    defaults = {"default_variable": 1, "port": 0}
    config = Config(defaults)

    expected_dict = {k: v for k, v in defaults.items()}
    expected_dict.update(config_dict)

    assert config.to_dict() == expected_dict

    config = Config()
    assert config.to_dict() == config_dict
