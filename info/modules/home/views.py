import logging

from flask import session, current_app, render_template, jsonify, request

from info.constants import CLICK_RANK_MAX_NEWS, HOME_PAGE_MAX_NEWS
from info.modes import User, News, Category
from info.utils.response_code import RET, error_map
from . import home_blu


@home_blu.route('/')
def index():
    # 判断登录状态，渲染页面
    user_id = session.get("user_id")
    user = None
    if user_id:
        try:
            user = User.query.get(user_id)
        except BaseException as e:
            current_app.logger.error(e)
    user = user.to_dict() if user else None

    # 新闻点击排行榜的渲染
    try:
        news_list = News.query.order_by(News.clicks.desc()).limit(CLICK_RANK_MAX_NEWS).all()
    except BaseException as e:
        current_app.logger.error(e)
        news_list = []
    news_list = [news.to_basic_dict() for news in news_list]

    # 获取分类
    try:
        categories = Category.query.all()
    except BaseException as e:
        current_app.logger.error(e)
        categories = []
    categories = [category.to_dict() for category in categories]

    return render_template('index.html', user=user, news_list=news_list, categories=categories)


# 获取新闻列表
@home_blu.route('/get_news_list')
def get_news_list():
    # 获取校验参数
    cid = request.args.get("cid")
    cur_page = request.args.get("cur_page")
    per_count = request.args.get("per_count", HOME_PAGE_MAX_NEWS)
    if not all([cid, cur_page]):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 格式转换！！！
    try:
        cid = int(cid)
        cur_page = int(cur_page)
        per_count = int(per_count)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 从数据库操作数据
    filter_list = []
    if cid != 1:
        filter_list.append(News.category_id == cid)

    try:
        pn = News.query.filter(*filter_list).order_by(News.create_time.desc()).paginate(cur_page, per_count)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])

    data = {
        "total_page": pn.pages,
        "news_list": [news.to_basic_dict() for news in pn.items]
    }

    # 返回结果给前端
    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK], data=data)


@home_blu.route('/favicon.ico')
def favicon():
    return current_app.send_static_file('news/images/favicon.ico')
