from aiohttp.test_utils import AioHTTPTestCase
import importlib.metadata
from pathlib import Path

import tempfile

from arteria.services.arteria_runfolder import get_app


class ArteriaRunfolderTestCase(AioHTTPTestCase):
    async def get_application(self):
        monitored_dir = tempfile.TemporaryDirectory()
        TODO clean up this temporary file after the tests are done

        runfolder = (
                Path(monitored_dir.name)
                / "200624_A00834_0183_BHMTFYDRXX"
        )
        runfolder.mkdir()

        self.config = {
            "monitored_directories": [
                monitored_dir.name
            ]
        }

        return get_app(self.config)

    async def test_version(self):
        async with self.client.request("GET", "/version") as resp:
            assert resp.status == 200
            content = await resp.json()

        assert content == {"version": importlib.metadata.version("arteria")}

    async def test_post_runfolders_path(self):
        async with self.client.request(
                "POST",
                "/runfolders/path/200624_A00834_0183_BHMTFYDRXX",
                data={"state": "STARTED"}) as resp:
            assert resp.status == 200

            state = (
                Path(self.config["monitored_directories"][0])
                / ".arteria/state"
            )

            with open(state) as state_file:
                assert state_file.read() == "started"

    async def test_post_runfolders_path_invalid_state(self):
        async with self.client.request(
                "POST",
                "/runfolders/path/200624_A00834_0183_BHMTFYDRXX",
                data={"state": "INVALID"}) as resp:

            assert resp.status == 400
            assert resp.text == "The state 'INVALID' is not valid"

    async def test_post_runfolders_path_missing_runfolder(self):
        async with self.client.request(
                "POST",
                "/runfolders/path/200624_A00834_0183_FAKE_RUNFOLDER",
                data={"state": "STARTED"}) as resp:

            assert resp.status == 404
            assert resp.text == "Runfolder '200624_A00834_0183_FAKE_RUNFOLDER' does not exist"
            
