import logging

from flask import session, current_app

from . import home_blu


@home_blu.route('/')
def index():
    session['name'] = 'zs'
    # logging.error('抛出异常！')
    current_app.logger.error('抛出异常！')
    return 'index'