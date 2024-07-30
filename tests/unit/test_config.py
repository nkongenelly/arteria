import tempfile
import jsonschema

import yaml
import pytest
from jsonschema.exceptions import ValidationError

from arteria.models.config import Config
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

    del Config._instance


def test_config_from_yaml(config_dict):
    with tempfile.NamedTemporaryFile(mode="r+", delete=False) as config_file:
        config_file.write(yaml.dump(config_dict))
        config_file.seek(0)
        config = Config.from_yaml(config_file.name)

        assert config.to_dict() == config_dict

        config_file.close()
        del Config._instance


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


def test_config_new(config, config_dict):
    # exist_ok=True allows overwriting the Config
    assert Config().to_dict() == config_dict

    assert Config() == Config()

    new_config = {"abc": "123"}

    with pytest.raises(ValidationError):
        Config.new(new_config, exist_ok=True, schema=runfolder_schema)

    Config.new(new_config, exist_ok=True)
    assert config.to_dict() == new_config
    assert Config().to_dict() == new_config


def test_default_config_from_scratch():
    # Config properties can only be updated y callinnng new() method with exist_ok=True
    defaults = {"default_variable": 1}
    config = Config(defaults)
    assert config.to_dict() == defaults
    assert config["default_variable"] == defaults["default_variable"]

    defaults["default_variable"] = 0
    assert config["default_variable"] != defaults["default_variable"]


def test_default_config_from_existing_config(config, config_dict):
    """Config class gives same instance of the config multiple times, if not overwritten
    by calling the new() method with exist_ok=True """
    defaults = {"default_variable": 1, "port": 0}
    config = Config(defaults)

    expected_dict = dict(defaults.items())
    expected_dict.update(config_dict)

    assert config.to_dict() == expected_dict

    config = Config()  # issue, still contains default variable
    assert config.to_dict() == config_dict


def test_config_validation(config):
    wrong_config_dict = {"abc": "123"}

    # validate(instance=config_dict, schema=schema if schema else {})
    validator = jsonschema.Draft7Validator(runfolder_schema)

    errors = [error.message for error in sorted(validator.iter_errors(wrong_config_dict), key=str)]
    expected_errors = [
        "'completed_marker_grace_minutes' is a required property",
        "'logger_config_file' is a required property",
        "'monitored_directories' is a required property",
        "'port' is a required property"
    ]

    assert len(errors) == 4
    assert errors == expected_errors
