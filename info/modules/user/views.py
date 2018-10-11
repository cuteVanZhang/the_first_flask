from flask import render_template, g, jsonify, redirect, url_for, request, current_app, abort

from info import db
from info.common import user_login_data, img_upload
from info.constants import USER_COLLECTION_MAX_NEWS, OTHER_NEWS_PAGE_MAX_COUNT, QINIU_DOMIN_PREFIX, \
    USER_FOLLOWED_MAX_COUNT
from info.modes import User, Category, News, tb_user_collection
from info.modules.user import user_blu
from info.utils.response_code import RET, error_map


# 个人中心主页
@user_blu.route('/user_info')
def user_info():

    return render_template("news/user.html", user=g.user.to_dict())


# 基本资料
@user_blu.route('/base_info', methods=["POST", "GET"])
def base_info():

    user = g.user

    if request.method == "GET":
        return render_template("news/user_base_info.html", user=user.to_dict())

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

    # 存在且不是user
    if is_existed_nick_name and is_existed_nick_name != user:
        return jsonify(errno=RET.DATAEXIST, errmsg="该昵称已存在!")

    user.signature = signature
    user.nick_name = nick_name
    user.gender = gender

    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])


# 头像设置
@user_blu.route('/pic_info', methods=["POST", "GET"])
def pic_info():

    user = g.user

    if request.method == "GET":
        return render_template("news/user_pic_info.html", user=user.to_dict())

    # 点击保存，提交post请求
    # 获取校验参数
    img_files = request.files.get("avatar")
    if img_files:
        img_bytes = img_files.read()

        try:
            # 将文件存储在第三方服务器(七牛云)
            files_name = img_upload(img_bytes)
        except BaseException as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.THIRDERR, errmsg=error_map[RET.THIRDERR])

        user.avatar_url = files_name

    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK], data=user.to_dict())


# 密码修改
@user_blu.route('/pass_info', methods=["POST", "GET"])
def pass_info():

    user = g.user

    if request.method == "GET":
        return render_template("news/user_pass_info.html")

    # 点击保存，提交post请求
    # 获取校验参数
    old_password = request.json.get("old_password")
    new_password = request.json.get("new_password")

    if not all([old_password, new_password]):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 密码长度不能少于6位
    if len(new_password) < 6:
        return jsonify(errno=RET.PARAMERR, errmsg="密码长度不能少于6位")

    # 校验原密码是否正确
    if not user.check_password(old_password):
        return jsonify(errno=RET.PWDERR, errmsg=error_map[RET.PWDERR])

    # 操作数据库数据
    user.password = new_password

    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])


# 新闻发布
@user_blu.route('/news_release', methods=["POST", "GET"])
def news_release():

    user = g.user

    # 获取分类
    try:
        cates = Category.query.all()
    except BaseException as e:
        current_app.logger.error(e)
        cates = []
    cates = [cate.to_dict() for cate in cates if cate.id != 1]

    if request.method == "GET":
        return render_template("news/user_news_release.html", cates=cates)

    # 获取校验参数
    title = request.form.get("title")
    category_id = request.form.get("category_id")
    digest = request.form.get("digest")
    content = request.form.get("content")
    if not all([title, category_id, digest, content]):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    try:
        category_id = int(category_id)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    if category_id not in [cate.get("id") for cate in cates]:
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    my_news = News()
    my_news.title = title
    my_news.digest = digest
    my_news.category_id = category_id
    my_news.content = content
    my_news.status = 1
    my_news.source = "个人发布"
    my_news.user_id = user.id

    index_image_file = request.files.get("index_image")
    # 获取文件对象 若获取到则添加index_image_url字段，反之不添加。
    if index_image_file:
        img_bytes = index_image_file.read()

        try:
            file_name = img_upload(img_bytes)
        except BaseException as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.THIRDERR, errmsg=error_map[RET.THIRDERR])

        my_news.index_image_url = QINIU_DOMIN_PREFIX + file_name

    db.session.add(my_news)

    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])


# 我的收藏
@user_blu.route('/collection')
def collection():

    user = g.user

    # 获取校验参数
    # cp = request.args.get("p")
    # cp = cp if cp else 1
    cp = request.args.get("p", 1)

    try:
        cp = int(cp)
    except BaseException as e:
        current_app.logger.error(e)
        cp = 1  # 异常是给cp设置为1 则不会应用整体运行

    try:
        pn = user.collection_news.order_by(tb_user_collection.c.create_time.desc()).paginate(cp,
                                                                                             USER_COLLECTION_MAX_NEWS)
    except BaseException as e:
        current_app.logger.error(e)
        # 数据库异常时使用的默认值
        collection_news_list = []
        cur_page = 1
        total_page = 1
    else:
        collection_news_list = [collection_news.to_dict() for collection_news in pn.items]
        cur_page = pn.page
        total_page = pn.pages

    data = {
        "collection_news_list": collection_news_list,
        "cur_page": cur_page,
        "total_page": total_page
    }

    return render_template("news/user_collection.html", data=data)


# 我的发布
@user_blu.route('/news_list')
def news_list():

    user = g.user

    # 获取校验参数
    cp = request.args.get("p", 1)

    try:
        cp = int(cp)
    except BaseException as e:
        current_app.logger.error(e)
        cp = 1

    # 查询我发布的新闻
    try:
        my_news = News.query.filter_by(user_id=user.id).order_by(News.create_time.desc()).paginate(cp, OTHER_NEWS_PAGE_MAX_COUNT)
    except BaseException as e:
        current_app.logger.error(e)
        my_news_list = []
        cur_page = 1
        total_page = 1
    else:
        my_news_list = [my_new.to_review_dict() for my_new in my_news.items]
        cur_page = my_news.page
        total_page = my_news.pages

    data = {
        "my_news_list": my_news_list,
        "cur_page": cur_page,
        "total_page": total_page
    }

    return render_template("news/user_news_list.html", data=data)


# 我的关注
@user_blu.route('/user_follow')
def user_follow():
    user = g.user

    cp = request.args.get("p", 1)

    try:
        cp = int(cp)
    except BaseException as e:
        current_app.logger.error(e)
        cp = 1  # 异常是给cp设置为1 则不会应用整体运行

    try:
        pn = user.followed.paginate(cp, USER_FOLLOWED_MAX_COUNT)
    except BaseException as e:
        current_app.logger.error(e)
        # 数据库异常时使用的默认值
        followed_authors = []
        cur_page = 1
        total_page = 1
    else:
        followed_authors = [author.to_dict() for author in pn.items]
        cur_page = pn.page
        total_page = pn.pages

    data = {
        "followed_authors": followed_authors,
        "cur_page": cur_page,
        "total_page": total_page
    }

    return render_template("news/user_follow.html", data=data)


@user_blu.route('/other/<int:user_id>')
def other(user_id):
    return render_template("news/other.html")