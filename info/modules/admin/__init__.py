from flask import Blueprint

from info.common import user_login_data

admin_blu = Blueprint("admin", __name__, url_prefix="/admin")


# 蓝图请求勾子函数
@admin_blu.before_request
@user_login_data
def check_superuser():
    user = g.user
    if (not (user and user.is_admin == 1)) and (not request.url.endswith("admin/login")):
        return redirect(url_for("home.index"))


from .views import *
