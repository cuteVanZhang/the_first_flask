import logging

from flask import session, current_app

from . import home_blu


@home_blu.route('/')
def index():
    session['name'] = 'zs'
    # logging.error('抛出异常！')
    current_app.logger.error('抛出异常！')
    return 'index'


@home_blu.route('/favicon.ico')
def favicon():
    print('111')
    return current_app.send_static_file('news/images/favicon.ico')