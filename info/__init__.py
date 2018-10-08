import logging
from logging.handlers import RotatingFileHandler

from flask import Flask
from flask_migrate import Migrate
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from redis import StrictRedis

from config import config_dict

db = None  # type: SQLAlchemy
sr = None  # type: StrictRedis


def setup_log(config_name):
    """配置日志"""

    # 设置日志的记录等级
    logging.basicConfig(level=config_name)  # 调试debug级
    # 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
    file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024 * 1024 * 100, backupCount=10)
    # 创建日志记录的格式 日志等级 输入日志信息的文件路径名 行数 日志信息
    formatter = logging.Formatter('%(levelname)s %(pathname)s:%(lineno)d %(message)s')
    # 为刚创建的日志记录器设置日志记录格式
    file_log_handler.setFormatter(formatter)
    # 为全局的日志工具对象（flask app使用的）添加日志记录器
    logging.getLogger().addHandler(file_log_handler)


def creat_app(config_type):
    config_class = config_dict[config_type]
    app = Flask(__name__)
    app.config.from_object(config_class)
    global db, sr
    db = SQLAlchemy(app)
    sr = StrictRedis(host=config_class.REDIS_HOST, port=config_class.REDIS_PORT, decode_responses=True)
    Session(app)
    Migrate(app, db)

    # CSRFProtect(app)

    from .modules.home import home_blu
    app.register_blueprint(home_blu)
    from info.modules.passport import passport_blu
    app.register_blueprint(passport_blu)
    from info.modules.news import news_blu
    app.register_blueprint(news_blu)
    from info.modules.user import user_blu
    app.register_blueprint(user_blu)

    setup_log(config_class.LOG_LEVEL)
    # from .modes import *
    import info.modes

    from info.common import index_convert
    app.add_template_filter(index_convert, "index_convert")

    return app
