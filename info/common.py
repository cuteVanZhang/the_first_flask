# from flask import current_app


# @current_app.template_filter("index_convert")  没有加进去
def index_convert(index):
    index_dict = {1: "first", 2: "second", 3: "third"}
    return index_dict.get(index, "")