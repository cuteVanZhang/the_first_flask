from flask_script import Manager
from flask_migrate import MigrateCommand

from info import creat_app

app = creat_app('dev')
mgr = Manager(app)
mgr.add_command('mc', MigrateCommand)


if __name__ == '__main__':
    # print(app.url_map)
    # print(app.url_map.converters)
    # print(app.template_filter)
    mgr.run()
