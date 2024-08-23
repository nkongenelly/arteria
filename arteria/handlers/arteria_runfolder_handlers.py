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
    try:
        runfolder_name = request.match_info['runfolder']
        for runfolder_path in Config().get('monitored_directories'):
            runfolder_cls = Runfolder(Path(runfolder_path) / runfolder_name)
            state = data["state"]
            if state not in State.__members__:
                raise web.HTTPBadRequest(reason=f"The state '{state}' is not valid")

            runfolder_cls.state = [s for s in State if s.name == state][0]

        return web.json_response(status=200)
    except Exception as e:
        set_exceptions(e, kwargs={"state": data["state"]})


@routes.get("/runfolders/path/{runfolder}")
async def get_runfolders(request):
    """
    Returns some information about the runfolder as json
    """
    try:
        runfolder_name = request.match_info['runfolder']
        runfolders = [

            serialize_runfolder_path(Runfolder(Path(runfolder_path) / runfolder_name), request)
            for runfolder_path in Config().get('monitored_directories')
        ]

        return web.json_response(
            data=runfolders,
            status=200
        )
    except Exception as e:
        set_exceptions(e)


@routes.get("/runfolders/next")
async def get_next_runfolder(request):
    """
    Finds unprocessed runfolder (state=ready) and then
    returns some information about this runfolder.
    """
    try:
        runfolder_cls = list_runfolders(
            Config()['monitored_directories'],
            filter_key=lambda r: r.state == State.READY
        )

        if len(runfolder_cls) > 0:
            runfolder_dict0 = serialize_runfolder_path(runfolder_cls[0], request)

            return web.json_response(
                data=runfolder_dict0,
                status=200
            )
        else:
            raise web.HTTPNoContent(
                reason="No ready runfolders available."
            )
    except Exception as e:
        set_exceptions(e)


@routes.get("/runfolders/pickup")
async def get_pickup_runfolder(request):
    """
    Used to start processing runfolders and also sets the runfolder to PENDING state.
    """
    try:
        runfolder_cls = list_runfolders(
            Config()['monitored_directories'],
            filter_key=lambda r: r.state == State.READY
        )

        if len(runfolder_cls) > 0:
            runfolder_cls[0].state = State.PENDING
            runfolder_dict0 = serialize_runfolder_path(runfolder_cls[0], request)
            return web.json_response(
                data=runfolder_dict0,
                status=200
            )
        else:
            raise web.HTTPNoContent(
                reason="No ready runfolders available."
            )
    except Exception as e:
        set_exceptions(e)


@routes.get("/runfolders")
async def get_all_runfolders(request):
    """
    Returns information about all the runfolders that
    match the state specified (or all runfolders when state
    is not specified)
    """
    try:
        runfolders = list_runfolders(
            Config()['monitored_directories'],
            filter_key=lambda r: r.state == State.READY
        )

        for runfolder_count, runfolder in enumerate(runfolders):
            runfolders[runfolder_count] = serialize_runfolder_path(runfolder, request)

        return web.json_response(
            data={"runfolders": runfolders},
            status=200
        )
    except Exception as e:
        set_exceptions(e)


def get_host_link(request):
    host = request.url.raw_host
    link = f"{request.scheme}://{host}/api/1.0"
    link_path = f"{link}{request.path}"

    return host, link_path


def serialize_runfolder_path(runfolder_cls, request):
    """
    Get the path uri as web.json_response gives an error when
    self.path is of type Path
    """
    runfolder_dict = runfolder_cls.to_dict()
    runfolder_dict['path'] = Path(runfolder_dict['path']).as_uri()
    runfolder_dict['host'], runfolder_dict['link'] = get_host_link(request)

    return runfolder_dict


def set_exceptions(e, kwargs=None):
    if type(e) is AssertionError:
        raise web.HTTPNotFound(reason=e.args[0] if len(e.args) > 0 else e)
    else:
        raise e
