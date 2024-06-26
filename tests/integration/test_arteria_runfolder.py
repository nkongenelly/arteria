from aiohttp.test_utils import AioHTTPTestCase
import importlib.metadata

from arteria.services.arteria_runfolder import get_app

class ArteriaRunfolderTestCase(AioHTTPTestCase):
    async def get_application(self):
        return get_app()

    async def test_version(self):
        async with self.client.request("GET", "/version") as resp:
            self.assertEqual(resp.status, 200)
            content = await resp.json()

        self.assertEqual(
            content,
            {"version": importlib.metadata.version("arteria") }
        )
