import yaml
import argparse
import logging.config

from aiohttp import web

from arteria.models.config import Config
from arteria.handlers.base import base_routes as routes
from arteria.config_schemas.schema_arteria_runfolder import runfolder_schema


def get_app(config_dict):
    """
    Creates an Application instance
    Sets up logger from configuration file specified in the config
    Registers the request handler
    """
    config = Config.new(config_dict, schema=runfolder_schema)

    with open(config["logger_config_file"], "r", encoding="utf-8") as logger_config_file:
        logger_config = yaml.safe_load(logger_config_file.read())
    logging.config.dictConfig(logger_config)

    app = web.Application()
    app.router.add_routes(routes)

    return app


def main():
    parser = argparse.ArgumentParser(description="arteria-runfolder server")
    parser.add_argument('--config_file')

    args = parser.parse_args()
    with open(args.config_file, "r", encoding="utf-8") as config_file:
        config_dict = yaml.safe_load(config_file.read())

    app = get_app(config_dict)
    web.run_app(app, port=config.get("port"))
