import argparse

from aiohttp import web
from arteria.services.base_service import BaseService

parser = argparse.ArgumentParser(description="archive-services server")
parser.add_argument('--config_file')

base_service = BaseService()
def main():
    config = base_service.get_config()
    app = base_service.get_app(config)

    web.run_app(app, port=config.get("port"))

