from flask import session

from . import home_blu


@home_blu.route('/')
def index():
    session['name'] = 'zs'
    return 'index'