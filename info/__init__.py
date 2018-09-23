from flask import Flask
from flask_migrate import Migrate
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from redis import StrictRedis

from config import config_dict


def creat_app(config_type):
    config_class = config_dict[config_type]
    app = Flask(__name__)
    app.config.from_object(config_class)
    db = SQLAlchemy(app)
    sr = StrictRedis(host=config_class.REDIS_HOST, port=config_class.REDIS_PORT)
    Session(app)
    Migrate(app, db)
    from .modules.home import home_blu
    app.register_blueprint(home_blu)
    return app

