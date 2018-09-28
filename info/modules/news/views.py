from flask import render_template, current_app, abort, session

from info.constants import CLICK_RANK_MAX_NEWS
from info.modes import News, User
from info.modules.news import news_blu


@news_blu.route('/<int:news_id>')
def get_news_detail(news_id):
    # 数据库查询数据
    try:
        news = News.query.get(news_id)
    except BaseException as e:
        current_app.logger.error(e)
        return abort(404)

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

    # 模板渲染返回
    return render_template("detail.html", news=news.to_dict(), news_list=news_list, user=user)