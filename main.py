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
        user = User.query.filter(User.mobile==username).first()
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


if __name__ == '__main__':
    # print(app.url_map)
    # print(app.url_map.converters)
    # print(app.template_filter)
    mgr.run()
