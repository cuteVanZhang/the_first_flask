import functools

from flask import session, current_app, g

from info.modes import User


def index_convert(index):
    index_dict = {1: "first", 2: "second", 3: "third"}
    return index_dict.get(index, "")


def user_login_data(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        user_id = session.get("user_id")
        user = None
        if user_id:
            try:
                user = User.query.get(user_id)
            except BaseException as e:
                current_app.logger.error(e)
        g.user = user
        return func(*args, **kwargs)

    return wrapper
