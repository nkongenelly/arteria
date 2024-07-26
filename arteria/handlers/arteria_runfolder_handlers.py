import os
from aiohttp import web
from pathlib import Path
from arteria.models.state import State
from arteria.models.config import Config
from arteria.handlers.base import base_routes
from arteria.models.runfolder_utils import Runfolder, list_runfolders

arteria_runfolder_routes = web.RouteTableDef()


@arteria_runfolder_routes.post("/runfolders/path/{runfolder}")
async def post_runfolders(request):
    """
    When this is called with payload {"state": "STARTED"},
    the state of the runfolder is set to STARTED
    """
    data = await request.post()

    runfolder_path = get_runfolders_path_from_query(request)
    runfolder_cls = Runfolder(runfolder_path, request)

    runfolder_cls.state = data["state"]
    return web.json_response(status=200)


@arteria_runfolder_routes.get("/runfolders/path/{runfolder}")
async def get_runfolders(request):
    """
    Returns some information about the runfolder as json
    """
    runfolder_path = get_runfolders_path_from_query(request)

    runfolder_cls = Runfolder(runfolder_path, request)

    return web.json_response(
        data=runfolder_cls.__repr__(),
        status=200
    )


@arteria_runfolder_routes.get("/runfolders/next")
async def get_next_runfolder(request):
    """
    Finds unprocessed runfolder (state=ready) and then
    returns some information about this runfolder.
    """
    runfolder_cls = list_runfolders(
        Config().config_dict.get('monitored_directories'),
        filter_key=lambda r: r.state == State.READY,
        request=request
    )
    if len(runfolder_cls) > 0:
        return web.json_response(
            data=runfolder_cls[0].__repr__(),
            status=200
        )
    else:
        raise web.HTTPNoContent(
            reason="No ready runfolders available."
        )


@arteria_runfolder_routes.get("/runfolders/pickup")
async def get_pickup_runfolder(request):
    """
    Used to start processing runfolders and also sets the runfolder to PENDING state.
    """
    runfolder_cls = list_runfolders(
        Config().config_dict.get('monitored_directories'),
        filter_key=lambda r: r.state == State.READY,
        request=request
    )

    if len(runfolder_cls) > 0:
        runfolder_cls[0].state = State.PENDING.name
        return web.json_response(
            data=runfolder_cls[0].__repr__(),
            status=200
        )
    else:
        raise web.HTTPNoContent(
            reason="No ready runfolders available."
        )


@arteria_runfolder_routes.get("/runfolders")
async def get_all_runfolders(request):
    """
    Returns information about all the runfolders that
    match the state specified (or all runfolders when state
    is not specified)
    """
    runfolders = list_runfolders(
        Config().config_dict.get('monitored_directories'),
        filter_key=lambda r: r.state == State.READY,
        request=request
    )

    return web.json_response(
        data={"runfolders": [
            runfolder.__repr__() for runfolder in runfolders
        ]},
        status=200
    )


def get_runfolders_path_from_query(request):
    """
    Returns directory of the runfolder
    """
    return os.path.join(
        Path(Config().config_dict.get('monitored_directories')[0]),
        request.match_info['runfolder']
    )


routes = list()
routes.append(base_routes)
routes.append(arteria_runfolder_routes)
