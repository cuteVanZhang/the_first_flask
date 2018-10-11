from flask import Blueprint

from info.common import user_login_data

user_blu = Blueprint("user", __name__, url_prefix="/user")


@user_blu.before_request
@user_login_data
def check_login():
    user = g.user
    if not user:
        if request.url.endswith("user/user_info"):
            return redirect(url_for("home.index"))
        elif "user/other/" not in request.url:
            return abort(403)

from .views import *
