import shutil
import tempfile
from pathlib import Path

import pytest

from arteria import __version__
from arteria.models.state import State
from arteria.models.config import Config
from arteria.services.arteria_runfolder import get_app


@pytest.fixture()
def config():
    """
    Setup a temporary directory to be monitored by the service.
    """
    with tempfile.TemporaryDirectory() as monitored_dir:
        config_dict = {
            "monitored_directories": [monitored_dir],
            "port": 8080,
            "completed_marker_grace_minutes": 0,
            "logger_config_file": "tests/resources/config/logger.config"
        }

        yield config_dict


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
    (runfolder / "RTAComplete.txt").touch()
    shutil.copyfile(
        "tests/resources/RunParameters_MiSeq.xml",
        runfolder / "RunParameters.xml",
    )

    return {
        "host": "test-host",
        "link": "http://test-host/api/1.0/runfolders/path/200624_A00834_0183_BHMTFYDRXX",
        "metadata": {
            "reagent_kit_barcode": "MS6728155-600V3",
        },
        "path": Path(config['monitored_directories'][0]) / "200624_A00834_0183_BHMTFYDRXX",
        "service_version": __version__,
        "state": state,
    }


@pytest.fixture()
async def client(aiohttp_client, config):
    """
    Instantiate a web client with a specific config.
    """
    try:
        yield await aiohttp_client(get_app(config))
    finally:
        Config.clear()


def get_expected_runfolder(runfolder, resp, state=None):
    runfolder['host'] = resp.url.raw_host
    runfolder['link'] = f"{resp.url.scheme}://{resp.url.raw_host}/api/1.0/runfolders/path{runfolder["path"]}"
    runfolder['state'] = state if state else runfolder['state']
    runfolder['path'] = runfolder['path'].as_uri()

    return runfolder


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

        state = runfolder.get('path') / ".arteria/state"
        assert state.read_text() == State.STARTED.value


@pytest.mark.parametrize("runfolder", [{"state": State.READY.name}], indirect=True)
async def test_post_runfolders_path_invalid_state(client, config, runfolder):
    async with client.request(
            "POST",
            "/runfolders/path/200624_A00834_0183_BHMTFYDRXX",
            data={"state": "INVALID"}) as resp:
        assert resp.status == 400
        assert resp.reason == "The state 'INVALID' is not valid"


@pytest.mark.parametrize("runfolder", [{"state": State.READY.name}], indirect=True)
async def test_post_runfolders_path_missing_runfolder(client, config, runfolder):
    async with client.request(
            "POST",
            "/runfolders/path/200624_A00834_0183_FAKE_RUNFOLDER",
            data={"state": "STARTED"}) as resp:
        assert resp.status == 404
        assert resp.reason == "Runfolder '200624_A00834_0183_FAKE_RUNFOLDER' does not exist"


@pytest.mark.parametrize("runfolder", [{"state": State.READY.name}], indirect=True)
async def test_get_runfolder_path(client, config, runfolder):
    async with client.request("GET", "/runfolders/path/200624_A00834_0183_BHMTFYDRXX") as resp:
        assert resp.status == 200
        expected_runfolder = get_expected_runfolder(runfolder, resp)
        content = await resp.json()
        content[0]['path'] = expected_runfolder.get("path")

        assert content == [expected_runfolder]


@pytest.mark.parametrize("runfolder", [{"state": State.READY.name}], indirect=True)
async def test_get_runfolders_path_missing_runfolder(client, config, runfolder):
    async with client.request(
            "GET",
            "/runfolders/path/200624_A00834_0183_FAKE_RUNFOLDER") as resp:
        assert resp.status == 404
        assert resp.reason == "Runfolder '200624_A00834_0183_FAKE_RUNFOLDER' does not exist"


@pytest.mark.parametrize("runfolder", [{"state": State.READY.name}], indirect=True)
async def test_runfolders_next(client, config, runfolder):
    async with client.request("GET", "/runfolders/next") as resp:
        assert resp.status == 200
        expected_runfolder = get_expected_runfolder(runfolder, resp)

        content = await resp.json()
        assert content == expected_runfolder
        assert content["state"] == State.READY.name


@pytest.mark.parametrize("runfolder", [{"state": State.STARTED.name}], indirect=True)
async def test_runfolders_next_not_found(client, config, runfolder):
    async with client.request("GET", "/runfolders/next") as resp:
        assert resp.status == 204
        assert resp.reason == "No ready runfolders available."


@pytest.mark.parametrize("runfolder", [{"state": State.READY.name}], indirect=True)
async def test_runfolders_pickup(client, config, runfolder):
    async with client.request("GET", "/runfolders/pickup") as resp:
        content = await resp.json()

        state = runfolder.get("path") / ".arteria/state"
        assert state.read_text() == "pending"

        expected_runfolder = get_expected_runfolder(runfolder, resp, State.PENDING.name)
        content['path'] = expected_runfolder.get("path")
        assert resp.status == 200
        assert content == expected_runfolder
        assert content["state"] == State.PENDING.name


@pytest.mark.parametrize("runfolder", [{"state": State.STARTED.name}], indirect=True)
async def test_runfolders_pickup_not_found(client, config, runfolder):
    async with client.request("GET", "/runfolders/pickup") as resp:
        assert resp.status == 204
        assert resp.reason == "No ready runfolders available."


@pytest.mark.parametrize("runfolder", [{"state": State.READY.name}], indirect=True)
async def test_get_runfolders(client, config, runfolder):
    async with client.request("GET", "/runfolders") as resp:
        expected_runfolder = get_expected_runfolder(runfolder, resp)

        contents = await resp.json()
        for content in contents.get("runfolders"):
            content['path'] = expected_runfolder.get("path")
        assert resp.status == 200
        assert contents == {"runfolders": [expected_runfolder]}


@pytest.mark.parametrize("runfolder", [{"state": State.DONE.name}], indirect=True)
async def test_get_runfolders_filtered(client, config, runfolder):
    async with client.request("GET", "/runfolders") as resp:
        contents = await resp.json()
        assert len(contents.get("runfolders")) == 0
