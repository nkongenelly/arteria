import os
from aiohttp import web
from pathlib import Path
from arteria.models.state import State
from arteria.models.config import Config
from arteria.handlers.base import base_routes
from arteria.models.runfolder_utils import Runfolder, list_runfolders


routes = base_routes


@routes.post("/runfolders/path/{runfolder}")
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


@routes.get("/runfolders/path/{runfolder}")
async def get_runfolders(request):
    """
    Returns some information about the runfolder as json
    """
    runfolder_path = get_runfolders_path_from_query(request)
    runfolder_dict = serialize_runfolder_path(Runfolder(runfolder_path, request))

    return web.json_response(
        data=runfolder_dict,
        status=200
    )


@routes.get("/runfolders/next")
async def get_next_runfolder(request):
    """
    Finds unprocessed runfolder (state=ready) and then
    returns some information about this runfolder.
    """
    runfolder_cls = list_runfolders(
        Config()['monitored_directories'],
        filter_key=lambda r: r.state == State.READY,
        request=request
    )

    if len(runfolder_cls) > 0:
        runfolder_dict0 = serialize_runfolder_path(runfolder_cls[0])
        return web.json_response(
            data=runfolder_dict0,
            status=200
        )
    else:
        raise web.HTTPNoContent(
            reason="No ready runfolders available."
        )


@routes.get("/runfolders/pickup")
async def get_pickup_runfolder(request):
    """
    Used to start processing runfolders and also sets the runfolder to PENDING state.
    """
    runfolder_cls = list_runfolders(
        Config()['monitored_directories'],
        filter_key=lambda r: r.state == State.READY,
        request=request
    )

    if len(runfolder_cls) > 0:
        runfolder_cls[0].state = State.PENDING.name
        runfolder_dict0 = serialize_runfolder_path(runfolder_cls[0])
        return web.json_response(
            data=runfolder_dict0,
            status=200
        )
    else:
        raise web.HTTPNoContent(
            reason="No ready runfolders available."
        )


@routes.get("/runfolders")
async def get_all_runfolders(request):
    """
    Returns information about all the runfolders that
    match the state specified (or all runfolders when state
    is not specified)
    """
    runfolders = list_runfolders(
        Config()['monitored_directories'],
        filter_key=lambda r: r.state == State.READY,
        request=request
    )

    for runfolder_count, runfolder in enumerate(runfolders):
        runfolders[runfolder_count] = serialize_runfolder_path(runfolder)

    return web.json_response(
        data={"runfolders": runfolders},
        status=200
    )


def get_runfolders_path_from_query(request):
    """
    Returns directory of the runfolder
    """
    return os.path.join(
        Path(Config()['monitored_directories'][0]),
        request.match_info['runfolder']
    )


def serialize_runfolder_path(runfolder_cls):
    """
    Get the path uri as web.json_response gives an error when
    self.path is of type Path
    """
    runfolder_dict = runfolder_cls.__repr__()
    runfolder_dict['path'] = Path(runfolder_dict['path']).as_uri()

    return runfolder_dict
