import functools

from flask import session, current_app, g

from info.modes import User


def index_convert(index):
    index_dict = {1: "first", 2: "second", 3: "third"}
    return index_dict.get(index, "")


def status_convert(status):
    # 0代表审核通过，1代表审核中，-1代表审核不通过
    status_dic = {0: "已通过", 1: "未审核", 2: "未通过"}
    return status_dic.get(status, "1")


def user_login_data(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        user_id = session.get("user_id")
        user = None
        if user_id:
            try:
                user = User.query.get(user_id)
            except BaseException as e:
                current_app.logger.error(e)
        g.user = user
        return func(*args, **kwargs)

    return wrapper


access_key = "kJ8wVO7lmFGsdvtI5M7eQDEJ1eT3Vrygb4SmR00E"
secret_key = "rGwHyAvnlLK7rU4htRpNYzpuz0OHJKzX2O1LWTNl"
bucket_name = "infonews"  # 存储空间名称


def img_upload(data):
    import qiniu
    q = qiniu.Auth(access_key, secret_key)
    # key = 'hello'  # 自定义文件名
    key = None  # 系统随机生成文件名扩展
    token = q.upload_token(bucket_name)
    ret, info = qiniu.put_data(token, key, data)
    if ret is not None:
        # print('All is OK')
        return ret.get("key")
    else:
        # print(info)  # error message in info
        raise BaseException(info)
