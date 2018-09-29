from flask import render_template, current_app, abort, session, request, jsonify, redirect, url_for

from info import db
from info.constants import CLICK_RANK_MAX_NEWS
from info.modes import News, User, Comment
from info.modules.news import news_blu
from info.utils.response_code import RET, error_map


# 新闻详情页面
@news_blu.route('/<int:news_id>')
def get_news_detail(news_id):
    # 数据库查询数据
    try:
        news = News.query.get(news_id)
        news.clicks += 1
        db.session.commit()
    except BaseException as e:
        db.session.rollback()
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

    # 新闻点击排行榜的渲染
    try:
        news_list = News.query.order_by(News.clicks.desc()).limit(CLICK_RANK_MAX_NEWS).all()
    except BaseException as e:
        current_app.logger.error(e)
        news_list = []
    news_list = [news.to_basic_dict() for news in news_list]

    # 是否收藏该新闻
    is_collected = 0
    if user:
        try:
            user_collect_list = [news.to_dict().get("id") for news in user.collection_news]
        except BaseException as e:
            current_app.logger.error(e)
        else:
            is_collected = news_id if news_id in user_collect_list else 0

    user = user.to_dict() if user else None

    # 获取评论列表
    comment_list = [comment.to_dict() for comment in news.comments][::-1]

    # 模板渲染返回
    return render_template("detail.html", news=news.to_dict(), news_list=news_list, user=user,
                           is_collected=is_collected, comment_list=comment_list)


# 新闻收藏
@news_blu.route('/news_collect', methods=["GET", "POST"])
def news_collect():
    # 获取校验参数
    news_id = request.json.get("news_id")
    action = request.json.get("action")
    if not all([news_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 获取用户状态/详情，未登录跳转到登录界面
    user_id = session.get("user_id")
    user = None
    if user_id:
        try:
            user = User.query.get(user_id)
        except BaseException as e:
            current_app.logger.error(e)

    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg=error_map[RET.SESSIONERR])

    # 修改数据库数据
    if action == "collect":
        try:
            news = News.query.get(news_id)
            user.collection_news.append(news)
            db.session.commit()
        except BaseException as e:
            current_app.logger.error(e)
            db.session.rollback()
            return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])

    else:
        try:
            news = News.query.get(news_id)
            user.collection_news.remove(news)
            db.session.commit()
        except BaseException as e:
            current_app.logger.error(e)
            db.session.rollback()
            return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])

    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])


# 评论
@news_blu.route('/news_comment', methods=["POST"])
def news_comment():
    # 获取校验参数 news_id/comment
    news_id = request.json.get("news_id")
    comment_content = request.json.get("comment")
    if not all([news_id, comment_content]):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 获取用户信息
    user_id = session.get("user_id")

    if not user_id:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    # 数据库增加数据
    comment = Comment()
    comment.news_id = news_id
    comment.user_id = user_id
    comment.content = comment_content
    try:
        db.session.add(comment)
        db.session.commit()
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])
    # 返回评论对象的数据
    date = comment.to_dict()

    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK], data=date)
