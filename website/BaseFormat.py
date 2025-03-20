""" from flask import Blueprint,render_template,request
BaseFormat = Blueprint('BaseFormat', __name__)

@BaseFormat.route('/home',__name__)
def BaseFormat():

 """