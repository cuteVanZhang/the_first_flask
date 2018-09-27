import logging
from datetime import timedelta

from redis import StrictRedis


class Config:
    SQLALCHEMY_DATABASE_URI = 'mysql://root:mysql@127.0.0.1:3306/my_info'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379
    SESSION_TYPE = 'redis'
    SESSION_REDIS = StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
    SESSION_USE_SIGNER = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=31)
    SECRET_KEY = '2wEI27BBgH2D+jRCHoO994df0CKlBe5azbYdiDX9JaN2I3vO'
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True


class DevelopmentConfig(Config):
    DEBUG = True
    LOG_LEVEL = logging.DEBUG


class ProductConfig(Config):
    DEBUG = False
    LOG_LEVEL = logging.ERROR


config_dict = {
    'dev': DevelopmentConfig,
    'pro': ProductConfig
}