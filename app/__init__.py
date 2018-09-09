from app.utils.flask_extended import Flask
from app.utils import app_utils as util
from pymessenger import Bot

config = util.absolute_path_from_project_root("config/config.yaml")

app = Flask(__name__, instance_relative_config=False)
app.config.from_yaml(config)

FB_ACCESS_TOKEN = app.config["FB_ACCESS_TOKEN"]
FB_VERIFY_TOKEN = app.config["FB_VERIFY_TOKEN"]
bot = Bot(FB_ACCESS_TOKEN)

GMAP_API_KEY = app.config["GMAP_API_KEY"]
BIKE_PATH_FILE = util.absolute_path_from_project_root(app.config["BIKE_PATH_FILE"])
BIKE_COLLISION_FILE = util.absolute_path_from_project_root(app.config["BIKE_COLLISION_FILE"])

import bot_views