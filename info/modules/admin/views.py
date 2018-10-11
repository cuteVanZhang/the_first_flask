import datetime
import time

from flask import render_template, g, redirect, url_for, request, jsonify, current_app, session, abort

from info import db
from info.common import img_upload
from info.constants import ADMIN_USER_PAGE_MAX_COUNT, ADMIN_NEWS_PAGE_MAX_COUNT, QINIU_DOMIN_PREFIX
from info.modes import User, News, Category
from info.modules.admin import admin_blu

from info.utils.response_code import RET, error_map


# 登录
@admin_blu.route('/login', methods=["POST", "GET"])
def login():
    user = g.user
    if user and user.is_admin == 1:
        return redirect(url_for("admin.index"))

    if request.method == "GET":
        return render_template("admin/admin_login.html")

    # 获取校验参数
    username = request.form.get("username")
    password = request.form.get("password")
    if not all([username, password]):
        return render_template("admin/admin_login.html", errmsg=error_map[RET.PARAMERR])

    # 用户是否存在
    try:
        user = User.query.filter(User.mobile == username, User.is_admin == 1).first()
    except BaseException as e:
        current_app.logger.error(e)
        return render_template("admin/admin_login.html", errmsg=error_map[RET.DBERR])

    if not user:
        return render_template("admin/admin_login.html", errmsg=error_map[RET.USERERR])

    # 校验密码
    if not user.check_password(password):
        return render_template("admin/admin_login.html", errmsg=error_map[RET.PWDERR])

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
def index():

    return render_template("admin/admin_index.html", user=g.user.to_dict())


# 用户统计
@admin_blu.route('/user_count')
def user_count():

    # 用户总数
    try:
        users_count = User.query.filter(User.is_admin == False).count()
    except BaseException as e:
        users_count = "**数**据**库**异**常**"

    ct = time.localtime()
    mon_one_day = "%d-%02d-01" % (ct.tm_year, ct.tm_mon)
    mon_1 = datetime.datetime.strptime(mon_one_day, "%Y-%m-%d")

    today = "%d-%02d-%02d" % (ct.tm_year, ct.tm_mon, ct.tm_mday)
    today_0 = datetime.datetime.strptime(today, "%Y-%m-%d")

    # 月新增
    try:
        mon_add_user = User.query.filter(User.create_time > mon_1).count()
    except BaseException as e:
        mon_add_user = "**数**据**库**异**常**"

    # 日新增
    try:
        day_add_user = User.query.filter(User.create_time > today_0).count()
    except BaseException as e:
        day_add_user = "**数**据**库**异**常**"

    # 数据列表
    time_list = []
    data_list = []

    for i in range(30):
        b_day = today_0 - datetime.timedelta(days=i)
        f_day = b_day + datetime.timedelta(days=1)
        try:
            everyday_add = User.query.filter(User.create_time >= b_day, User.create_time < f_day).count()
        except BaseException as e:
            everyday_add = 9999999
        everyday_date = b_day.strftime("%Y-%m-%d")
        time_list.append(everyday_date)
        data_list.append(everyday_add)

    data = {
        "users_count": users_count,
        "mon_add_user": mon_add_user,
        "day_add_user": day_add_user,
        "time_list": time_list[::-1],
        "data_list": data_list[::-1]
    }

    return render_template("admin/admin_user_count.html", date=data)


# 用户列表
@admin_blu.route('/user_list')
def user_list():

    # 分页显示用户列表
    # 获取校验参数
    cp = request.args.get("p", 1)

    try:
        cp = int(cp)
    except BaseException as e:
        current_app.logger.error(e)
        cp = 1

    # 查询我发布的新闻
    try:
        all_user = User.query.paginate(cp, ADMIN_USER_PAGE_MAX_COUNT)
    except BaseException as e:
        current_app.logger.error(e)
        user_list = []
        cur_page = 1
        total_page = 1
    else:
        user_list = [user.to_admin_dict() for user in all_user.items]
        cur_page = all_user.page
        total_page = all_user.pages

    data = {
        "user_list": user_list,
        "cur_page": cur_page,
        "total_page": total_page
    }

    return render_template("admin/admin_user_list.html", data=data)


# 新闻审核
@admin_blu.route('/news_review')
def news_review():

    # 分页显示用户列表
    # 获取校验参数
    cp = request.args.get("p", 1)

    try:
        cp = int(cp)
    except BaseException as e:
        current_app.logger.error(e)
        cp = 1

    filter_list = []
    keywords = request.args.get("keywords")
    if keywords:
        filter_list.append(News.title.contains(keywords))
    # 查询我发布的新闻
    try:
        reveiw_news = News.query.filter(*filter_list).order_by(News.create_time.desc()).paginate(cp,
                                                                                                 ADMIN_NEWS_PAGE_MAX_COUNT)
    except BaseException as e:
        current_app.logger.error(e)
        news_list = []
        cur_page = 1
        total_page = 1
    else:
        news_list = [news.to_review_dict() for news in reveiw_news.items]
        cur_page = reveiw_news.page
        total_page = reveiw_news.pages

    data = {
        "news_list": news_list,
        "cur_page": cur_page,
        "total_page": total_page
    }

    return render_template("admin/admin_news_review.html", data=data)


# 新闻审核详情页
@admin_blu.route('/news_review_detail/<int:news_id>')
def news_review_detail(news_id):

    try:
        news = News.query.get(news_id)
    except BaseException as e:
        current_app.logger.error(e)
        return abort(404)

    if not news:
        return abort(404)

    # try:
    #     cates = Category.query.filter(Category.id != 1).all()
    # except BaseException as e:
    #     current_app.logger.error(e)
    #     cates = []
    # cates = [cate.to_dict() for cate in cates]

    return render_template("admin/admin_news_review_detail.html", news=news.to_dict())


# 提交审核
@admin_blu.route('/news_review_action', methods=["POST"])
def news_review_action():

    action = request.json.get("action")
    news_id = request.json.get("news_id")
    reason = request.json.get("reason")
    if not all([action, news_id]):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    if action not in ["reject", "accept"]:
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    try:
        news_id = int(news_id)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    try:
        news = News.query.get(news_id)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])

    if not news:
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    if action == "accept":
        news.status = 0
    else:
        news.status = -1
        news.reason = reason

    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])


# 新闻版式编辑
@admin_blu.route('/news_edit')
def news_edit():

    # 分页显示用户列表
    # 获取校验参数
    cp = request.args.get("p", 1)

    try:
        cp = int(cp)
    except BaseException as e:
        current_app.logger.error(e)
        cp = 1

    filter_list = []
    keywords = request.args.get("keywords")
    if keywords:
        filter_list.append(News.title.contains(keywords))
    # 查询新闻
    try:
        edit_news = News.query.filter(*filter_list).order_by(News.id).paginate(cp, ADMIN_NEWS_PAGE_MAX_COUNT)
    except BaseException as e:
        current_app.logger.error(e)
        news_list = []
        cur_page = 1
        total_page = 1
    else:
        news_list = [news.to_review_dict() for news in edit_news.items]
        cur_page = edit_news.page
        total_page = edit_news.pages

    data = {
        "news_list": news_list,
        "cur_page": cur_page,
        "total_page": total_page
    }

    return render_template("admin/admin_news_edit.html", data=data)


# 新闻版式详情页
@admin_blu.route('/news_edit_detail/<int:news_id>')
def news_edit_detail(news_id):

    try:
        news = News.query.get(news_id)
    except BaseException as e:
        current_app.logger.error(e)
        return abort(404)

    if not news:
        return abort(404)

    try:
        cates = Category.query.filter(Category.id != 1).all()
    except BaseException as e:
        current_app.logger.error(e)
        cates = []
    cates = [cate.to_dict() for cate in cates]

    return render_template("admin/admin_news_edit_detail.html", news=news.to_dict(), cates=cates)


# 提交编辑
@admin_blu.route('/news_edit_detail', methods=["POST"])
def news_edit_action():

    title = request.form.get("title")
    category_id = request.form.get("category_id")
    digest = request.form.get("digest")
    content = request.form.get("content")
    news_id = request.form.get("news_id")
    index_image = request.files.get("index_image")
    if not all([title, news_id, category_id, digest, content]):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    try:
        news_id = int(news_id)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    try:
        news = News.query.get(news_id)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])
    if not news:
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    try:
        category_id = int(category_id)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    try:
        cate = News.query.get(category_id)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])
    if not cate:
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    news.title = title
    news.category_id = category_id
    news.digest = digest
    news.content = content

    if index_image:
        img_bytes = index_image.read()
        try:
            file_name = img_upload(img_bytes)
        except BaseException as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.THIRDERR, errmsg=error_map[RET.THIRDERR])
        news.index_image_url = QINIU_DOMIN_PREFIX + file_name

    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])


# 新闻分类管理
@admin_blu.route('/news_type', methods=["GET", "POST"])
def news_type():

    # 获取分类
    try:
        cates = Category.query.order_by(Category.id).all()
    except BaseException as e:
        current_app.logger.error(e)
        cates = []
    cates = [cate.to_dict() for cate in cates if cate.id != 1]

    if request.method == "GET":
        return render_template("admin/admin_news_type.html", cates=cates)

    name = request.json.get("name")
    cate_id = request.json.get("id")
    if not name:
        return jsonify(errno=RET.PARAMERR, errmsg="分类名称不能为空")

    if name in [cate.get("name") for cate in cates]:
        return jsonify(errno=RET.PARAMERR, errmsg="分类名称已存在")

    if cate_id:
        # 修改分类

        try:
            cate_id = int(cate_id)
        except BaseException as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

        if cate_id not in [cate.get("id") for cate in cates]:
            return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

        try:
            modify_cate = Category.query.get(cate_id)
        except BaseException as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])

        modify_cate.name = name

    else:
        # 新增分类
        new_cate = Category()
        new_cate.name = name
        db.session.add(new_cate)

    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])
