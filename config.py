from datetime import timedelta

from redis import StrictRedis


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


class DevelopmentConfig(Config):
    DEBUG = True


class ProductConfig(Config):
    DEBUG = False


config_dict = {
    'dev': DevelopmentConfig,
    'pro': ProductConfig
}