from flask import Blueprint

home_blu = Blueprint('home', __name__)

from .views import *
