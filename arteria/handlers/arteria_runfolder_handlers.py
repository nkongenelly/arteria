from aiohttp import web
from pathlib import Path
from arteria import __version__
import logging
from arteria.models.state import State
from arteria.models.config import Config
from arteria.handlers.base import base_routes
from arteria.models.runfolder_utils import Runfolder, list_runfolders


routes = base_routes
log = logging.getLogger(__name__)


@routes.post("/runfolders/path/{runfolder:.*}")
async def post_runfolders(request):
    """
    When this is called with payload {"state": "STARTED"},
    the state of the runfolder is set to STARTED
    """

    data = await request.post()
    runfolder_path = Path(request.match_info['runfolder'])

    if not any([
        runfolder_path.parent == Path(monitored_directory)
        for monitored_directory in Config()['monitored_directories']
    ]):
        raise web.HTTPBadRequest(
            reason=f"{runfolder_path} does not belong to a monitored directory")

    try:
        runfolder = Runfolder(runfolder_path)
    except AssertionError as exc:
        log.exception(exc)
        raise web.HTTPNotFound(reason=exc) from exc

    state = data["state"]
    try:
        runfolder.state = State[state]
    except KeyError as exc:
        raise web.HTTPBadRequest(reason=f"The state '{state}' is not valid") from exc

    return web.Response(status=200)


@routes.get("/runfolders/path/{runfolder:.*}")
async def get_runfolders(request):
    """
    Returns some information about the runfolder as json
    """
    runfolder_path = Path(request.match_info['runfolder'])

    if not any([
        runfolder_path.parent == Path(monitored_directory)
        for monitored_directory in Config()['monitored_directories']
    ]):
        raise web.HTTPBadRequest(
            reason=f"{runfolder_path} does not belong to a monitored directory")

    try:
        runfolder = Runfolder(runfolder_path)
    except AssertionError as exc:
        log.exception(exc)
        raise web.HTTPNotFound(reason=exc) from exc

    return web.json_response(
        data=serialize_runfolder_path(runfolder, request),
        status=200
    )


@routes.get("/runfolders/next")
async def get_next_runfolder(request):
    """
    Finds unprocessed runfolder (state=ready) and then
    returns some information about this runfolder.
    """
    try:
        runfolders = list_runfolders(
            Config()['monitored_directories'],
            filter_key=lambda r: r.state == State.READY
        )

        if len(runfolders) > 0:
            runfolder_dict = serialize_runfolder_path(runfolders[0], request)

            return web.json_response(
                data=runfolder_dict,
                status=200
            )
        else:
            raise web.HTTPNoContent(
                reason="No ready runfolder found."
            )
    except AssertionError as exc:
        log.exception(exc)
        raise web.HTTPNotFound(reason=exc) from exc


@routes.get("/runfolders/pickup")
async def get_pickup_runfolder(request):
    """
    Used to start processing runfolders and also sets the runfolder to PENDING state.
    """
    try:
        runfolders = list_runfolders(
            Config()['monitored_directories'],
            filter_key=lambda r: r.state == State.READY
        )

        if runfolders:
            runfolders[0].state = State.PENDING
            runfolder_dict = serialize_runfolder_path(runfolders[0], request)
            return web.json_response(
                data=runfolder_dict,
                status=200
            )
        else:
            raise web.HTTPNoContent(
                reason="No ready runfolders available."
            )
    except AssertionError as exc:
        log.exception(exc)
        raise web.HTTPNotFound(reason=exc) from exc


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

        runfolders = [
            serialize_runfolder_path(runfolder, request)
            for runfolder in runfolders
        ]

        return web.json_response(
            data={"runfolders": runfolders},
            status=200
        )
    except AssertionError as exc:
        log.exception(exc)
        raise web.HTTPNotFound(reason=exc) from exc


def get_host_link(request, runfolder_path, ):
    host = request.url.raw_host
    link = f"{request.scheme}://{host}/api/1.0/runfolders/path{runfolder_path}"

    return host, link


def serialize_runfolder_path(runfolder_cls, request):
    """
    Get the path uri as web.json_response gives an error when
    self.path is of type Path
    """
    runfolder_dict = runfolder_cls.to_dict()
    runfolder_dict['service_version'] = __version__
    runfolder_path = Path(runfolder_dict['path'])
    runfolder_dict['path'] = runfolder_path.as_uri()
    runfolder_dict['host'], runfolder_dict['link'] = get_host_link(request, runfolder_path)

    return runfolder_dict
