import yaml
import argparse
import logging.config

from aiohttp import web
from arteria.models.config import Config
from arteria.handlers.arteria_runfolder_handlers import routes


parser = argparse.ArgumentParser(description="arteria-runfolder server")
parser.add_argument('--config_file')


def main():
    config = get_config()
    app = get_app(config)

    web.run_app(app, port=config.get("port"))


def get_config():
    """
    Retrieves passed config file name
    Loads the config dictionary to Config
    """
    args = parser.parse_args()
    config_file = args.config_file
    return Config().from_yaml(config_file)


def get_app(config):
    """
    Creates an Application instance
    Sets up logger from configuration file specified in the config
    Registers the request handler
    """
    app = web.Application()
    inistialize_logger(config)
    [app.router.add_routes(route) for route in routes]
    return app


def inistialize_logger(config):
    """
    Sets up logger from configuration file
    """
    logger_file = config.get("logger_config_file")
    try:
        # When config file has section headers i.e [version]..
        logging.config.fileConfig(logger_file)
    except RuntimeError:
        # When config file has yaml format (without section headers)
        with open(logger_file, 'r') as stream:
            config = yaml.load(stream, Loader=yaml.FullLoader)
            logging.config.dictConfig(config)
