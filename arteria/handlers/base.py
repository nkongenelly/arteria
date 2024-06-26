"""
Base routes that should be included in all services
"""

import importlib.metadata

from aiohttp import web


base_routes = web.RouteTableDef()


@base_routes.get("/version")
async def version(request):
    """
    Returns service version in use
    """
    return web.json_response(
        {"version": importlib.metadata.version("arteria")}
    )
