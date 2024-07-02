from aiohttp import web

from arteria.handlers.base import base_routes as routes


def get_app(config):
    app = web.Application()
    app.router.add_routes(routes)
    return app


def main():
    app = get_app({})
    web.run_app(app)
