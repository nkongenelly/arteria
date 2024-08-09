import tempfile

import pytest

from arteria.services.base_service import BaseService


@pytest.fixture()
async def client(aiohttp_client, config):
    """
    Instantiate a web client with a specific config.
    """
    base_service = BaseService()
    return await aiohttp_client(base_service.get_app(config))
