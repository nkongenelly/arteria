from aiohttp import web
from arteria.handlers.base import base_routes

archive_services_routes = web.RouteTableDef()



routes = [base_routes, archive_services_routes]
