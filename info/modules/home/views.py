import logging

from flask import session, current_app, render_template, jsonify

from info.constants import CLICK_RANK_MAX_NEWS
from info.modes import User, News
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

    return render_template('index.html', user=user, news_list=news_list)


@home_blu.route('/favicon.ico')
def favicon():
    return current_app.send_static_file('news/images/favicon.ico')
