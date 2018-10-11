import random
import datetime

from flask import current_app
from flask_script import Manager
from flask_migrate import MigrateCommand

from info import creat_app

app = creat_app('dev')
mgr = Manager(app)
mgr.add_command('mc', MigrateCommand)


# 创建管理员账号函数封装到命令行调用
@mgr.option("-u", dest="username")
@mgr.option("-p", dest="pwd")
def create_superuser(username, pwd):
    if not all([username, pwd]):
        print("参数不完整: -u username -p pwd")
        return

    from info.modes import User
    from info import db
    try:
        user = User.query.filter(User.mobile == username).first()
    except BaseException as e:
        current_app.logger.error(e)
        print("数据库异常")
        return
    if user:
        print("用户名已存在!")
        return

    super_user = User()
    super_user.mobile = username
    super_user.password = pwd
    super_user.is_admin = True
    super_user.nick_name = username

    try:
        db.session.add(super_user)
        db.session.commit()
    except BaseException as e:
        db.session.rollback()
        current_app.logger.error(e)
        print("数据库异常")
        return

    print("管理员创建成功")


def create_test_user_data():
    '''
    创建用户账号测试数据
    '''
    from info.modes import User
    from info import db
    user_list = []
    for num in range(0, 10000):
        user = User()
        user.nick_name = "%06d" % num
        user.mobile = "%06d" % num
        user.password_hash = "pbkdf2:sha256:50000$1P6xtqPy$977d8a4faa9df97d180bdeac80cd1ffeecd018f92dada894399f72d259e69ed2"
        user.create_time = datetime.datetime.now() - datetime.timedelta(seconds=random.randint(0, 2678400))
        user_list.append(user)
        print(user.mobile)
    try:
        db.session.add_all(user_list)
        db.session.commit()
    except BaseException as e:
        db.session.rollback()
        print(e)

    print("OK")


if __name__ == '__main__':
    # print(app.url_map)
    # print(app.url_map.converters)
    # print(app.template_filter)
    # create_test_user_data()
    mgr.run()
