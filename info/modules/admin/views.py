from flask import render_template, g, redirect, url_for, request, jsonify, current_app, session

from info.common import user_login_data
from info.constants import ADMIN_USER_PAGE_MAX_COUNT
from info.modes import User
from info.modules.admin import admin_blu

from info.utils.response_code import RET, error_map


# 登录
@admin_blu.route('/login', methods=["POST", "GET"])
@user_login_data
def login():
    user = g.user
    if user and user.is_admin == 1:
        return redirect(url_for("admin.index"))

    if request.method == "GET":
        return render_template("admin_login.html")

    # 获取校验参数
    username = request.form.get("username")
    password = request.form.get("password")
    if not all([username, password]):
        return render_template("admin_login.html", errmsg=error_map[RET.PARAMERR])

    # 用户是否存在
    try:
        user = User.query.filter(User.mobile == username, User.is_admin == 1).first()
    except BaseException as e:
        current_app.logger.error(e)
        return render_template("admin_login.html", errmsg=error_map[RET.DBERR])

    if not user:
        return render_template("admin_login.html", errmsg=error_map[RET.USERERR])

    # 校验密码
    if not user.check_password(password):
        return render_template("admin_login.html", errmsg=error_map[RET.PWDERR])

    # 状态保持
    session["user_id"] = user.id

    return redirect(url_for("admin.index"))


# 退出登录
@admin_blu.route('/logout')
def logout():
    session.pop("user_id", None)
    return redirect(url_for("admin.login"))


# 主页
@admin_blu.route('/index')
@user_login_data
def index():

    user = g.user

    # 未登录跳转登录界面
    if not (user and user.is_admin == 1):
        return redirect(url_for("admin.login"))

    return render_template("admin_index.html", user=user.to_dict())


# 用户统计
@admin_blu.route('/user_count')
@user_login_data
def user_count():

    user = g.user

    # 未登录跳转登录界面
    if not (user and user.is_admin == 1):
        return redirect(url_for("admin.login"))

    return render_template("admin_user_count.html")


# 用户列表
@admin_blu.route('/user_list')
@user_login_data
def user_list():

    user = g.user

    # 未登录跳转登录界面
    if not (user and user.is_admin == 1):
        return redirect(url_for("admin.login"))

    # 分页显示用户列表
    # 获取校验参数
    cp = request.args.get("p")
    cp = cp if cp else 1

    try:
        cp = int(cp)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 查询我发布的新闻
    try:
        all_user = User.query.paginate(cp, ADMIN_USER_PAGE_MAX_COUNT)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])

    data = {
        "user_list": [user.to_admin_dict() for user in all_user.items],
        "cur_page": all_user.page,
        "total_page": all_user.pages
    }

    return render_template("admin_user_list.html", data=data)


# 新闻审核
@admin_blu.route('/news_review')
def news_review():

    return render_template("admin_user_count.html")  # todo


# 新闻版式编辑
@admin_blu.route('/news_edit')
def news_edit():

    return render_template("admin_user_count.html")  # todo


# 新闻分类管理
@admin_blu.route('/news_type')
def news_type():

    return render_template("admin_user_count.html")  # todo