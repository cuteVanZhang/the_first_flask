import random
import re
from datetime import datetime

from flask import request, abort, jsonify, current_app, make_response, Response, session

from info import sr, db
from info.lib.yuntongxun.sms import CCP
from info.modes import User
from info.modules.passport import passport_blu
from info.utils.captcha.pic_captcha import captcha

from info.utils.response_code import RET, error_map


# 生产图片验证码
@passport_blu.route('/get_img_code')
def get_img_code():
    # 获取校验参数
    img_code_id = request.args.get('img_code_id')
    if not img_code_id:
        return abort(403)
        # 此处返回图片bytes，不接受json
        # return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 获取图片
    img_name, img_text, img_bytes = captcha.generate_captcha()

    # 保存图片文本，图片key
    try:
        sr.set('img_code_id' + img_code_id, img_text, ex=180)
    except BaseException as e:
        current_app.logger.errno(e)
        return abort(500)
        # 此处返回图片bytes，不接受json
        # return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])

    # 返回图片Bytes
    response = make_response(img_bytes)  # type: Response
    response.content_type = 'image/jpeg'
    return response


# 获取验证短信
@passport_blu.route('/get_sms_code', methods=['GET', 'POST'])
def get_sms_code():
    # 获取验证参数
    mobile = request.json.get('mobile')
    img_code = request.json.get('img_code')
    img_code_id = request.json.get('img_code_id')
    if not all([mobile, img_code, img_code_id]):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 验证手机号码格式是否正确
    if not re.match(r'1[345789]\d{9}$', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 根据图片key,从数据库获取图片text
    try:
        real_img_code = sr.get('img_code_id' + img_code_id)
    except BaseException as e:
        current_app.logger.errno(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])

    # 验证码和图片text 是否过期/一致
    if not real_img_code:
        return jsonify(errno=RET.PARAMERR, errmsg='验证码过期')
    if real_img_code != img_code.upper():
        return jsonify(errno=RET.DATAERR, errmsg='验证码错误')

    # 验证客户是否已存在
    try:
        is_exist_user = User.query.filter_by(mobile=mobile).first()
    except BaseException as e:
        current_app.logger.errno(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])

    if is_exist_user:
        return jsonify(errno=RET.DATAEXIST, errmsg='用户已存在')

    # 发送短信
    sms_code = '%04d' % random.randint(0, 9999)

    # #控制台模拟发送短信
    # current_app.logger.info('短信验证码为:%s' % sms_code)

    # 第三方云通讯平台 发送短信验证码
    sms_send_res = CCP().send_template_sms('13182978726', [sms_code, 5], 1)
    if sms_send_res != 0:
        return jsonify(errno=RET.THIRDERR, errmsg=error_map[RET.THIRDERR])

    # 保存短信验证码
    try:
        sr.set("img_code_id" + mobile, sms_code, ex=300)
    except BaseException as e:
        current_app.logger.errno(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])

    # 返回结果
    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])


# 注册
@passport_blu.route('/register', methods=['GET', 'POST'])
def register():
    # 获取验证参数
    mobile = request.json.get('mobile')
    sms_code = request.json.get('sms_code')
    password = request.json.get('password')

    if not all([mobile, sms_code, password]):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 验证手机号码格式是否正确
    if not re.match(r'1[345789]\d{9}$', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 根据手机号从数据库读取real_msm_code
    try:
        real_msm_code = sr.get("img_code_id" + mobile)
    except BaseException as e:
        current_app.logger.errno(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])

    # 验证短信验证码是否 过期/一致
    if not real_msm_code:
        return jsonify(errno=RET.PARAMERR, errmsg='验证码过期')
    if real_msm_code != sms_code.upper():
        return jsonify(errno=RET.PARAMERR, errmsg='验证码错误')

    # 存储客户信息
    user = User()
    user.mobile = mobile
    user.password = password
    user.nick_name = mobile
    user.last_login = datetime.now()
    try:
        db.session.add(user)
        db.session.commit()
    except BaseException as e:
        db.session.rollback()
        current_app.logger.errno(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])

    # 状态保持
    session['user_id'] = user.id

    # 返回结果
    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])


# 登录
@passport_blu.route('/login', methods=['POST'])
def login():
    # 获取校验参数
    mobile = request.json.get("mobile")
    password = request.json.get("password")
    if not all([mobile, password]):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 验证手机号码格式是否正确
    if not re.match(r'1[345789]\d{9}$', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 判断账号是否存在
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except BaseException as e:
        current_app.logger.errno(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])

    if not user:
        return jsonify(errno=RET.USERERR, errmsg="账号不存，请先注册!")

    # 从数据库读取账号，密码，校验
    # try:
    #     pwhash = user.password_hash
    # except BaseException as e:
    #     current_app.logger.errno(e)
    #     return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])

    # 将密码验证封装到对象的方法中
    if not user.check_password(password):
        return jsonify(errno=RET.LOGINERR, errmsg="用户名/密码错误!")

    # 更新last_login
    user.last_login = datetime.now()
    # db.session.commit()  设置 "SQLALCHEMY_COMMIT_ON_TEARDOWN"属性，<请求结束前>自动提交

    # 状态保持
    session["user_id"] = user.id

    # 返回结果
    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])


@passport_blu.route('/logout')
def logout():

    session.pop("user_id", None)

    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])