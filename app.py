from flask import session,Flask, render_template, request, redirect, url_for, flash,json
import pandas as pd
import uuid
import pymysql
pymysql.install_as_MySQLdb()
import math
from werkzeug.utils import secure_filename
from werkzeug.datastructures import  FileStorage
import sqlalchemy as sql

import sys
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms.validators import InputRequired, Email, Length
from wtforms import StringField, PasswordField, BooleanField
from flask_wtf import FlaskForm
from flask_sqlalchemy import SQLAlchemy
from email.mime.multipart import MIMEMultipart
import smtplib
from flask_bootstrap import Bootstrap
from datetime import datetime, timedelta
import os


import boto3
import botocore

app = Flask(__name__,static_folder='' )#,
    #template_folder= os.path.abspath(r"C:\Users\MIKEB\Desktop\Python\Fuhnance\disciprin\templates"),
    #template_folder= os.path.abspath(r"/Users/mikebelliveau/Desktop/Python/disciprin/templates"),
    #static_folder=os.path.abspath(r"C:\Users\MIKEB\Desktop\Python\Fuhnance\disciprin\static"))

    #static_folder=os.path.abspath(r"/Users/mikebelliveau/Desktop/Python/disciprin/static"))
app.config['SECRET_KEY'] = 'Skinnybelly23!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:Skinnybelly23!@database-1.cfawyq16sqrt.us-east-2.rds.amazonaws.com:3306/kb'

sdb = SQLAlchemy(app)
BASE = "http://127.0.0.1:5000/"
#BASE="http://54.87.214.247:5000/"
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

bootstrap = Bootstrap(app)
app.secret_key = 'sansal54'

class Config(object):
    ASSETS_ROOT = '/static/assets'


class DB:

    def __init__(self, engine='mysql://root:Skinnybelly23!@database-1.cfawyq16sqrt.us-east-2.rds.amazonaws.com:3306/kb'):
        self.engine = sql.create_engine(engine)
        self.get_all_users()

    def get_all_users(self):
        return pd.read_sql('SELECT * from users;', self.engine)


class Users(UserMixin, sdb.Model):
    user_id = sdb.Column(sdb.String(100), primary_key=True)
    username = sdb.Column(sdb.String(50), unique=True)
    email = sdb.Column(sdb.String(50), unique=True)
    pw = sdb.Column(sdb.String(100))
    cpw = sdb.Column(sdb.String(100))

    def check_password(self,pw):
        return check_password_hash(self.pw,pw)
    def validate(self, unames, emails, valids):
        punc = '''!()-[]{};:'"\,<>./?@#$%^&*_~'''

        valids.append("")
        name = self.user_name
        for ele in name:
            if ele in punc:
                name = name.replace(ele, "")
        if len(name) != len(self.user_name):
            valids.append("Invalid Username, must not contain any punctuation")
        elif name in unames:
            valids.append("Username already exists.")
        else:
            valids.append("")
        return valids

    def get_id(self):
        return self.user_id

    def get_un(self):
        return self.u_name

db = DB()

@app.route('/')
def index():
    return render_template('home/dashboard.html')

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(user_id)

@app.route("/SignUp", methods=["POST", "GET"])
def signup():
    if request.method=='POST':
        users = db.get_all_users()

        hashed_password = generate_password_hash(
            request.form['password'])
        #emails = [x for x in pd.unique(users['email'])]
        invalids=[]
        """if request.form["email"] in emails:
            invalids.append("Email is already in use!")

        if request.form['password'] != request.form['cpassword']:
            invalids.append("Passwords do not match!")"""


         # print(invalids)
        if len(invalids) == 0:
            new_user = Users(user_id=uuid.uuid1(
            ).hex, email=request.form['email'], pw=hashed_password,
                             cpw=hashed_password,username=request.form["username"])

            sdb.session.add(new_user)
            sdb.session.commit()

            login_user(new_user,force=True)
            return redirect(BASE)

        else:

            html=render_template("sign-up.html", valids=invalids, email=request.form["email"],
                                        cpw=request.form['cpassword'], pw=request.form['password'])
            return html
    else:
        return render_template('accounts/register.html', config=Config())

@app.route("/LogOut", methods=["POST", "GET"])
def logout():
    logout_user()
    return redirect(BASE)


@app.route("/Login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        #username = request.form['username']
        user = Users.query.filter_by(email=request.form["email"]).first()
        if user:
            if check_password_hash(user.pw, request.form["password"]):
                login_user(user, force=True, remember=True)
                return redirect(BASE)
        return render_template("accounts/login.html", email=request.form["email"], pw=request.form["password"], BASE=BASE, config=Config())
    else:
        return render_template('accounts/login.html', email=request.form["email"], pw=request.form["password"], BASE=BASE, config=Config())

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)


