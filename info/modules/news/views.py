from flask import render_template, current_app, abort, session, request, jsonify, g

from info import db
from info.common import user_login_data
from info.constants import CLICK_RANK_MAX_NEWS
from info.modes import News, User, Comment, CommentLike
from info.modules.news import news_blu
from info.utils.response_code import RET, error_map


# 新闻详情页面
@news_blu.route('/<int:news_id>')
@user_login_data
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

    if not news:
        return abort(404)

    # 新闻点击排行榜的渲染
    try:
        news_list = News.query.order_by(News.clicks.desc()).limit(CLICK_RANK_MAX_NEWS).all()
    except BaseException as e:
        current_app.logger.error(e)
        news_list = []
    news_list = [news.to_basic_dict() for news in news_list]

    # 是否收藏该新闻
    is_collected = False

    # 判断登录状态，渲染页面
    user = g.user

    if user:
        try:
            user_collect_list = [news.to_dict().get("id") for news in user.collection_news]
        except BaseException as e:
            current_app.logger.error(e)
        else:
            is_collected = True if news_id in user_collect_list else False

    user = user.to_dict() if user else None

    # 获取评论列表
    try:
        comments = news.comments.order_by(Comment.create_time.desc()).all()
    except BaseException as e:
        current_app.logger.error(e)
        jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])

    # 获取用户评论列表
    if user:
        try:
            user_comment_list = CommentLike.query.filter(CommentLike.user_id == user.get("id")).all()
            user_comment_list = [commentlike.comment_id for commentlike in user_comment_list]
        except BaseException as e:
            current_app.logger.error(e)
            jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])
    else:
        user_comment_list = []

    comment_list = []
    for comment in comments:
        comment_dict = comment.to_dict()
        is_like = False
        if comment.id in user_comment_list:
            is_like = True
        comment_dict["is_like"] = is_like
        comment_list.append(comment_dict)

    # 模板渲染返回
    return render_template("detail.html", news=news.to_dict(), news_list=news_list, user=user,
                           is_collected=is_collected, comment_list=comment_list)


# 新闻收藏
@news_blu.route('/news_collect', methods=["GET", "POST"])
@user_login_data
def news_collect():
    # 获取用户状态/详情，未登录跳转到登录界面
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg=error_map[RET.SESSIONERR])

    # 获取校验参数
    news_id = request.json.get("news_id")
    action = request.json.get("action")
    if not all([news_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # int转换
    try:
        news_id = int(news_id)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 获取新闻对象
    try:
        news = News.query.get(news_id)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])

    if not news:
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])

    # 修改数据库数据
    if action == "collect":
        user.collection_news.append(news)
    elif action == "cancel_collect":
        user.collection_news.remove(news)
    else:
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])


# 评论/回复评论
@news_blu.route('/news_comment', methods=["POST"])
@user_login_data
def news_comment():
    # 获取用户信息
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    # 获取校验参数 news_id/comment
    news_id = request.json.get("news_id")
    comment_content = request.json.get("comment")
    parent_id = request.json.get("parent_id")
    if not all([news_id, comment_content]):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # int转换
    try:
        news_id = int(news_id)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 校验是否存在
    try:
        news = News.query.get(news_id)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])

    if not news:
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 数据库增加数据
    comment = Comment()
    comment.news_id = news_id
    comment.user_id = user.id
    comment.content = comment_content

    if parent_id:
        # int转换
        try:
            parent_id = int(parent_id)
        except BaseException as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

        # 校验是否存在
        try:
            pcm = Comment.query.get(parent_id)
        except BaseException as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])

        if not pcm:
            return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

        comment.parent_id = parent_id

    try:
        db.session.add(comment)
        db.session.commit()
    except BaseException as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])
    # 返回评论对象的数据
    date = comment.to_dict()

    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK], data=date)


# 点赞
@news_blu.route('/comment_like', methods=["POST"])
@user_login_data
def comment_like():
    # 获取用户状态/详情，未登录跳转到登录界面
    user = g.user

    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg=error_map[RET.SESSIONERR])

    # 获取校验参数
    comment_id = request.json.get("comment_id")
    action = request.json.get("action")
    if not all([comment_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 修改数据库
    try:
        comment = Comment.query.get(comment_id)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])

    if not comment:
        return jsonify(errno=RET.NODATA, errmsg=error_map[RET.NODATA])

    if action == "add":
        # user.like_comment.append(comment)

        comment.like_count += 1
        # 更改用户点赞数据修改comment_like 表中数据
        commentLike = CommentLike()
        commentLike.comment_id = comment_id
        commentLike.user_id = user.id
        db.session.add(commentLike)
    elif action == "remove":
        # user.like_comment.remove(comment)
        try:
            commentLike = CommentLike.query.filter(CommentLike.comment_id == comment_id,
                                                   CommentLike.user_id == user.id).first()
        except BaseException as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])

        comment.like_count -= 1
        db.session.delete(commentLike)
    else:
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    try:
        db.session.commit()
    except BaseException as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])

    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])
