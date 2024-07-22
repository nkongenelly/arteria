"""
Base routes that should be included in all services
"""
import os
from aiohttp import web
from pathlib import Path
from arteria import __version__
from arteria.models.state import State
from arteria.models.config import Config
from arteria.models.runfolder_utils import Runfolder, list_runfolders


base_routes = web.RouteTableDef()


@base_routes.get("/version")
async def version(request):
    """
    Returns service version in use
    """
    return web.json_response(
        {"version": __version__}
    )


@base_routes.post("/runfolders/path/{runfolder}")
async def post_runfolders_path(request):
    runfolder_path = os.path.join(
        Path(Config().config_dict.get('monitored_directories')[0]),
        request.match_info['runfolder']
    )

    runfolder_cls = Runfolder(runfolder_path)
    data = await request.post()
    runfolder_cls.state = data["state"]
    return web.Response(text='Hello, world')


@base_routes.get("/runfolders/path/{runfolder}")
async def get_runfolders_path(request):
    runfolder_path = os.path.join(
        Path(Config().config_dict.get('monitored_directories')[0]),
        request.match_info['runfolder']
    )

    runfolder_cls = Runfolder(runfolder_path)
    return web.json_response(runfolder_cls)


@base_routes.get("/runfolders/next")
async def get_next_runfolder(request):
    return  web.json_response(
        list_runfolders(
            Config().config_dict.get('monitored_directories')[0],
            filter_key=lambda r: r.state == State.READY
        )[0]
    )


@base_routes.get("/runfolders/pickup")
async def get_pickup_runfolder(request):
    runfolder = list_runfolders(
            Config().config_dict.get('monitored_directories')[0],
            filter_key=lambda r: r.state == State.READY
        )[0]
    runfolder.state = State.PENDING

    return  web.json_response(runfolder)


@base_routes.get("/runfolders")
async def get_runfolders_path(request):
    runfolder = list_runfolders(
        Config().config_dict.get('monitored_directories')[0],
        filter_key=lambda r: r.state == State.READY
    )[0]

    return web.json_response({"runfolders": runfolder})













