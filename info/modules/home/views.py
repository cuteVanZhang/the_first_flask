import logging

from flask import session, current_app, render_template

from . import home_blu


@home_blu.route('/')
def index():
    return render_template('index.html')


@home_blu.route('/favicon.ico')
def favicon():
    return current_app.send_static_file('news/images/favicon.ico')