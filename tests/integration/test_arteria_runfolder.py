import importlib.metadata
from pathlib import Path
import tempfile

import pytest

from arteria.services.arteria_runfolder import get_app


@pytest.fixture()
def config_runfolder_ready():
    with tempfile.TemporaryDirectory() as monitored_dir:
        runfolder = Path(monitored_dir) / "200624_A00834_0183_BHMTFYDRXX"
        runfolder.mkdir()
        (runfolder / ".arteria").mkdir()
        with open(runfolder / ".arteria/state", "w") as state_file:
            state_file.write("ready")

        config = {
            "monitored_directories": [monitored_dir],
        }

        runfolder = {
            "host": "test-host",
            "link": "http://test-host/api/1.0/runfolders/path/200624_A00834_0183_BHMTFYDRXX",
            "metadata": {
                    "reagent_kit_barcode": "MS6728155 - 600V3",
            },
            "path": f"{config['monitored_directories'][0]}/200624_A00834_0183_BHMTFYDRXX",
            "service_version": importlib.metadata.version("arteria"),
            "state": "ready"
        }

        yield (config, runfolder)


@pytest.fixture()
def config_runfolder_started():
    with tempfile.TemporaryDirectory() as monitored_dir:
        runfolder = Path(monitored_dir) / "200624_A00834_0183_BHMTFYDRXX"
        runfolder.mkdir()
        (runfolder / ".arteria").mkdir()
        with open(runfolder / ".arteria/state", "w") as state_file:
            state_file.write("started")

        config = {
            "monitored_directories": [monitored_dir],
        }

        runfolder = {
            "host": "test-host",
            "link": "http://test-host/api/1.0/runfolders/path/200624_A00834_0183_BHMTFYDRXX",
            "metadata": {
                    "reagent_kit_barcode": "MS6728155 - 600V3",
            },
            "path": f"{config['monitored_directories'][0]}/200624_A00834_0183_BHMTFYDRXX",
            "service_version": importlib.metadata.version("arteria"),
            "state": "started"
        }

        yield (config, runfolder)


async def test_version(aiohttp_client, config_runfolder_ready):
    config, runfolder = config_runfolder_ready
    client = await aiohttp_client(get_app(config))
    async with client.request("GET", "/version") as resp:
        assert resp.status == 200
        content = await resp.json()

    assert content == {"version": importlib.metadata.version("arteria")}


async def test_post_runfolders_path(aiohttp_client, config_runfolder_ready):
    config, runfolder = config_runfolder_ready
    client = await aiohttp_client(get_app(config))
    async with client.request(
            "POST",
            "/runfolders/path/200624_A00834_0183_BHMTFYDRXX",
            data={"state": "STARTED"}) as resp:
        assert resp.status == 200

        state = Path(config["monitored_directories"][0]) / ".arteria/state"

        with open(state) as state_file:
            assert state_file.read() == "started"


async def test_post_runfolders_path_invalid_state(aiohttp_client, config_runfolder_ready):
    config, runfolder = config_runfolder_ready
    client = await aiohttp_client(get_app(config))
    async with client.request(
            "POST",
            "/runfolders/path/200624_A00834_0183_BHMTFYDRXX",
            data={"state": "INVALID"}) as resp:

        assert resp.status == 400
        assert resp.text == "The state 'INVALID' is not valid"


async def test_post_runfolders_path_missing_runfolder(aiohttp_client, config_runfolder_ready):
    config, runfolder = config_runfolder_ready
    client = await aiohttp_client(get_app(config))
    async with client.request(
            "POST",
            "/runfolders/path/200624_A00834_0183_FAKE_RUNFOLDER",
            data={"state": "STARTED"}) as resp:

        assert resp.status == 404
        assert resp.text == "Runfolder '200624_A00834_0183_FAKE_RUNFOLDER' does not exist"

async def test_get_runfolder_path(aiohttp_client, config_runfolder_ready):
    config, runfolder = config_runfolder_ready
    client = await aiohttp_client(get_app(config))
    async  with client.request("GET", "/runfolders/path/200624_A00834_0183_BHMTFYDRXX") as resp:
        assert resp.status == 200
        assert resp.json() == runfolder

async def test_get_runfolders_path_missing_runfolder(aiohttp_client, config_runfolder_ready):
    config, runfolder = config_runfolder_ready
    client = await aiohttp_client(get_app(config))
    async with client.request(
            "GET",
            "/runfolders/path/200624_A00834_0183_FAKE_RUNFOLDER") as resp:

        assert resp.status == 404
        assert resp.text == "Runfolder '200624_A00834_0183_FAKE_RUNFOLDER' does not exist"


async def test_runfolders_next(aiohttp_client, config_runfolder_ready):
    config, runfolder = config_runfolder_ready
    client = await aiohttp_client(get_app(config))
    async with client.request("GET", "/runfolders/next") as resp:
        assert resp.status == 200
        assert resp.json() == runfolder
        assert resp.json()["state"] == "ready"


async def test_runfolders_next(aiohttp_client, config_runfolder_started):
    config, runfolder = config_runfolder_started
    client = await aiohttp_client(get_app(config))
    async with client.request("GET", "/runfolders/next") as resp:
        assert resp.status == 204
        assert resp.text == "No ready runfolders available."



async def test_runfolders_pickup(aiohttp_client, config_runfolder_ready):
    config, runfolder = config_runfolder_ready
    client = await aiohttp_client(get_app(config))
    async with client.request("GET", "/runfolders/pickup") as resp:
        assert resp.status == 200
        assert resp.json() == runfolder
        assert resp.json()["state"] == "pending"
        state = Path(config["monitored_directories"][0]) / ".arteria/state"

        with open(state) as state_file:
            assert state_file.read() == "pending"


async def test_runfolders_pickup(aiohttp_client, config_runfolder_started):
    config, runfolder = config_runfolder_started
    client = await aiohttp_client(get_app(config))
    async with client.request("GET", "/runfolders/pickup") as resp:
        assert resp.status == 204
        assert resp.text == "No ready runfolders available."
