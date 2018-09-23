from flask import Blueprint

home_blu = Blueprint('home', __name__, url_prefix='/home')

from .views import *
