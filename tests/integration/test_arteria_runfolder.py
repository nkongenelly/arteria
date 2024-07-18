import pytest
import tempfile

from pathlib import Path
from arteria import __version__
from arteria.models.state import State
from arteria.services.arteria_runfolder import get_app


@pytest.fixture()
def config():
    """
    Setup a temporary directory to be monitored by the service.
    """
    with tempfile.TemporaryDirectory() as monitored_dir:
        config = {
            "monitored_directories": [monitored_dir],
            "port": 8080,
            "completed_marker_grace_minutes": 10,
            "logger_config_file": "../resources/config/logger.config"
        }

        yield config


@pytest.fixture()
def runfolder(request, config):
    """
    Create a dummy runfolder in the first monitored directory.
    """
    state = request.param.get("state", State.DONE.value)

    monitored_dir = config["monitored_directories"][0]
    runfolder = Path(monitored_dir) / "200624_A00834_0183_BHMTFYDRXX"
    (runfolder / ".arteria").mkdir(parents=True)
    (runfolder / ".arteria/state").write_text(state)

    return {
        "host": "test-host",
        "link": "http://test-host/api/1.0/runfolders/path/200624_A00834_0183_BHMTFYDRXX",
        "metadata": {
                "reagent_kit_barcode": "MS6728155 - 600V3",
        },
        "path": f"{config['monitored_directories'][0]}/200624_A00834_0183_BHMTFYDRXX",
        "service_version": __version__,
        "state": state,
    }


@pytest.fixture()
async def client(aiohttp_client, config):
    """
    Instantiate a web client with a specific config.
    """
    return await aiohttp_client(get_app(config))


async def test_version(client, caplog):
    async with client.request("GET", "/version") as resp:
        assert resp.status == 200
        content = await resp.json()

    assert content == {"version": __version__}
    # Test logger is initialized and used
    assert 'INFO' in caplog.text
    assert 'GET /version' in caplog.text


@pytest.mark.parametrize("runfolder", [{"state": State.READY.name}], indirect=True)
async def test_post_runfolders_path(client, config, runfolder):
    async with client.request(
            "POST",
            "/runfolders/path/200624_A00834_0183_BHMTFYDRXX",
            data={"state": "STARTED"}) as resp:
        assert resp.status == 200

        state = Path(config["monitored_directories"][0]) / ".arteria/state"
        state.write_text(State.STARTED.name)


@pytest.mark.parametrize("runfolder", [{"state": State.READY.name}], indirect=True)
async def test_post_runfolders_path_invalid_state(client, config, runfolder):
    async with client.request(
            "POST",
            "/runfolders/path/200624_A00834_0183_BHMTFYDRXX",
            data={"state": "INVALID"}) as resp:

        assert resp.status == 400
        assert resp.text == "The state 'INVALID' is not valid"


@pytest.mark.parametrize("runfolder", [{"state": State.READY.name}], indirect=True)
async def test_post_runfolders_path_missing_runfolder(client, config, runfolder):
    async with client.request(
            "POST",
            "/runfolders/path/200624_A00834_0183_FAKE_RUNFOLDER",
            data={"state": "STARTED"}) as resp:

        assert resp.status == 404
        assert resp.text == "Runfolder '200624_A00834_0183_FAKE_RUNFOLDER' does not exist"


@pytest.mark.parametrize("runfolder", [{"state": State.READY.name}], indirect=True)
async def test_get_runfolder_path(client, config, runfolder):
    async with client.request("GET", "/runfolders/path/200624_A00834_0183_BHMTFYDRXX") as resp:
        assert resp.status == 200
        assert resp.json() == runfolder


@pytest.mark.parametrize("runfolder", [{"state": State.READY.name}], indirect=True)
async def test_get_runfolders_path_missing_runfolder(client, config, runfolder):
    async with client.request(
            "GET",
            "/runfolders/path/200624_A00834_0183_FAKE_RUNFOLDER") as resp:

        assert resp.status == 404
        assert resp.text == "Runfolder '200624_A00834_0183_FAKE_RUNFOLDER' does not exist"


@pytest.mark.parametrize("runfolder", [{"state": State.READY.name}], indirect=True)
async def test_runfolders_next(client, config, runfolder):
    async with client.request("GET", "/runfolders/next") as resp:
        assert resp.status == 200
        assert resp.json() == runfolder
        assert resp.json()["state"] == State.READY.value


@pytest.mark.parametrize("runfolder", [{"state": State.STARTED.name}], indirect=True)
async def test_runfolders_next_not_found(client, config, runfolder):
    async with client.request("GET", "/runfolders/next") as resp:
        assert resp.status == 204
        assert resp.text == "No ready runfolders available."


@pytest.mark.parametrize("runfolder", [{"state": State.READY.name}], indirect=True)
async def test_runfolders_pickup(client, config, runfolder):
    async with client.request("GET", "/runfolders/pickup") as resp:
        assert resp.status == 200
        assert resp.json() == runfolder
        assert resp.json()["state"] == "pending"

        state = Path(config["monitored_directories"][0]) / ".arteria/state"
        assert state.read_text() == "pending"


@pytest.mark.parametrize("runfolder", [{"state": State.STARTED.name}], indirect=True)
async def test_runfolders_pickup_not_found(client, config, runfolder):
    async with client.request("GET", "/runfolders/pickup") as resp:
        assert resp.status == 204
        assert resp.text == "No ready runfolders available."


async def test_get_runfolders(client, config, runfolder):
    async with client.request("GET", "/runfolders") as resp:
        assert resp.status == 200
        assert resp.json() == {"runfolders": [runfolder]}

@pytest.mark.parametrize("runfolder", [{"state": State.DONE.name}], indirect=True)
async def test_get_runfolders_filtered(client, config, runfolder):
    async with client.request("GET", "/runfolders") as resp:
        assert resp.status == 200
        assert resp.json() == {"runfolders": [runfolder]}