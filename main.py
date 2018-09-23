from datetime import timedelta
from flask_script import Manager
from redis import StrictRedis
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from flask_migrate import Migrate, MigrateCommand


class Config:
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'mysql://root:mysql@127.0.0.1:3306/my_info'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379
    SESSION_TYPE = 'redis'
    SESSION_REDIS = StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
    SESSION_USE_SIGNER = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=31)
    SECRET_KEY = '2wEI27BBgH2D+jRCHoO994df0CKlBe5azbYdiDX9JaN2I3vO'


app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
sr = StrictRedis(host=Config.REDIS_HOST, port=Config.REDIS_PORT)
Session(app)
mgr = Manager(app)
Migrate(app, db)
mgr.add_command('mc', MigrateCommand)


if __name__ == '__main__':
    mgr.run()