from flask import render_template, g, jsonify

from info.common import user_login_data
from info.modules.user import user_blu
from info.utils.response_code import RET, error_map


@user_blu.route('/user_info')
@user_login_data
def user_info():
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg=error_map[RET.SESSIONERR])

    return render_template("user.html", user=user)