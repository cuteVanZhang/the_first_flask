import re

from flask import request, abort, jsonify, current_app, make_response, Response

from info import sr
from info.modules.passport import passport_blu
from info.utils.captcha.pic_captcha import captcha

from info.utils.response_code import RET, error_map


# 生产图片验证码
@passport_blu.route('/get_img_code')
def get_img_code():
    # 获取校验参数
    img_code_id = request.args.get('img_code_id')
    if not img_code_id:
        # return abort(403)
        return jsonify(error=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 获取图片
    img_name, img_text, img_bytes = captcha.generate_captcha()

    # 保存图片文本，图片key
    try:
        sr.set('img_code_id'+img_code_id, img_text, ex=180)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(error=RET.DBERR, errmsg=error_map[RET.DBERR])

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
        return jsonify(error=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 验证手机号码格式是否正确
    if not re.match(r'1[345789]\d{9}$', mobile):
        return jsonify(error=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 根据图片key,从数据库获取图片text
    try:
        real_img_code = sr.get('img_code_id' + img_code_id)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(error=RET.DBERR, errmsg=error_map[RET.DBERR])

    # 验证码和图片text 是否过期/一致
    if not real_img_code:
        return jsonify(error=RET.PARAMERR, errmsg='验证码过期')
    if real_img_code != img_code.upper():
        return jsonify(error=RET.PARAMERR, errmsg='验证码错误')

    # 发送短信

    # 保存短信验证码

    # 返回结果
    return jsonify(error=RET.OK, errmsg=error_map[RET.OK])
