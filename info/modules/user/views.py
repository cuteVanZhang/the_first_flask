from flask import render_template, g, jsonify, redirect, url_for, request, current_app

from info.common import user_login_data
from info.modes import User
from info.modules.user import user_blu
from info.utils.response_code import RET, error_map


# 个人中心主页
@user_blu.route('/user_info')
@user_login_data
def user_info():
    user = g.user
    if not user:
        return redirect(url_for("home.index"))

    return render_template("user.html", user=user.to_dict())


# 基本信息
@user_blu.route('/base_info', methods=["POST", "GET"])
@user_login_data
def base_info():

    user = g.user
    if not user:
        return redirect(url_for("home.index"))

    if request.method == "GET":
        return render_template("user_base_info.html", user=user.to_dict())

    # 点击保存，提交post请求
    # 获取校验参数
    signature = request.json.get("signature")
    nick_name = request.json.get("nick_name")
    gender = request.json.get("gender")

    if not all([signature, nick_name, gender]):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    if gender not in ["MAN", "WOMAN"]:
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 操作数据库数据
    # 昵称字段唯一，需判断是否已存在
    try:
        is_existed_nick_name = User.query.filter_by(nick_name=nick_name).first()
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])

    if is_existed_nick_name:
        return jsonify(errno=RET.DATAEXIST, errmsg="该昵称已存在!")

    user.signature = signature
    user.nick_name = nick_name
    user.gender = gender

    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])

