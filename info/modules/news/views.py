from flask import render_template, current_app, abort

from info.modes import News
from info.modules.news import news_blu


@news_blu.route('/<int:news_id>')
def get_news_detail(news_id):
    # 数据库查询数据
    try:
        news = News.query.get(news_id)
    except BaseException as e:
        current_app.logger.error(e)
        return abort(404)
    # 模板渲染返回
    return render_template("detail.html", news=news.to_dict())