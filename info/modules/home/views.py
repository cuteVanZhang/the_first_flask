import logging

from flask import session, current_app, render_template, jsonify

from info.modes import User
from info.utils.response_code import RET, error_map
from . import home_blu


@home_blu.route('/')
def index():
    # 获取session 中的user_id
    user_id = session.get("user_id")
    user = None
    if user_id:
        try:
            user = User.query.get(user_id)
        except BaseException as e:
            current_app.logger.errno(e)
    user = user.to_dict() if user else None
    return render_template('index.html', user=user)


@home_blu.route('/favicon.ico')
def favicon():
    return current_app.send_static_file('news/images/favicon.ico')

