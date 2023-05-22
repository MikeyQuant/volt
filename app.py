from flask import session,Flask, render_template, request, redirect, url_for, flash,json
import pandas as pd
import uuid
import json
import pymysql
pymysql.install_as_MySQLdb()
import math
from werkzeug.utils import secure_filename
from werkzeug.datastructures import  FileStorage
import sqlalchemy as sql
import requests
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
    def get_poll_ans(self,pid):
        polls=pd.read_sql("select * from polls where poll_id ='{}'".format(pid),self.engine)
        n=polls["n"][0]

        df=pd.read_sql("select * from answers where poll_id ='{}'".format(pid),self.engine)
        lst=[]
        for i in range(1,n+1):
            lst += df[~df[f"A{i}"].isin(lst)][f"A{i}"].to_list()
        res = [*set(lst)]
        res={"n":str(n),"array":res}
        return res
    def get_all_users(self):
        return pd.read_sql('SELECT * from users;', self.engine)
    def set_keys(self,uid,papi,papis,dapi,dapis):
        self.engine.execute(f"update users set papi='{papi}',papis='{papis}',dapi='{dapi}',dapis='{dapis}' where user_id ='{uid}';")
    def add_poll(self,question,n,type,uid):

        self.engine.execute(f"insert into polls values ('{uuid.uuid1().hex}','{question}',{n},'{type}','{uid}',now(),0);")
    def get_polls(self,uid):
        df=self.get_answers_user(uid)
        ids=df["poll_id"].to_list()
        ids="','".join(ids)
        return pd.read_sql(f"select * from polls ;",self.engine)#where poll_id not in ('{ids}')",self.engine)

    def get_answers_user(self,uid):
        return pd.read_sql(f"select * from answers where user_id = '{uid}'",self.engine)

    def add_answer(self,uid,pid,ans):
        n=len(ans)
        print(ans)
        ans_str="','".join(ans)
        ans_col=",A".join([str(x) for x in range(1,n+1)])
        self.engine.execute(f"insert into answers (poll_id, user_id,A{ans_col}) values ('{pid}','{uid}','{ans_str}')")
        n=len(pd.read_sql("select * from answers where poll_id = '{}'".format(pid),self.engine))
        self.engine.execute("update polls set na = {} where poll_id = '{}'; ".format(n,pid))
    def view_poll(self,pid):
        ans=pd.read_sql("select * from answers where poll_id = '{}'".format(pid),self.engine)
        poll=pd.read_sql("select * from polls where poll_id = '{}'".format(pid),self.engine)
        return ans,poll
    def get_users(self,users):
        users="','".join(users)
        return pd.read_sql("select * from users where user_id in ('{}');".format(users),self.engine)

class Users(UserMixin, sdb.Model):
    user_id = sdb.Column(sdb.String(100), primary_key=True)
    username = sdb.Column(sdb.String(50), unique=True)
    email = sdb.Column(sdb.String(100), unique=True)
    pw = sdb.Column(sdb.String(150))
    cpw = sdb.Column(sdb.String(150))

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

@app.route('/',methods=["POST","GET"])
def index():
    try:
        current_user.user_id
    except:
        return render_template("accounts/register.html",config=Config())
    df=db.get_polls(current_user.user_id)
    items=[]
    tt={"tr":"Top","br":"Bottom","q":""}
    for i in range(36):

        g={}
        try:
            for col in df:
                if col=="t":
                    g[col]=tt[df[col][i]]
                else:
                    g[col]=df[col][i]
        except:

            items.append(g)
            break
        items.append(g)
        print(items)

    return render_template('home/dashboard.html',user=current_user,items=items)
@app.route("/viewPoll/<pid>",methods=["GET"])
def view_poll(pid):
    ans,polls=db.view_poll(pid)
    anso=ans
    question=polls["question"][0]
    n=polls["n"][0]
    uans=ans[ans["user_id"]==current_user.user_id].reset_index(drop=True)

    ans=ans[ans["user_id"]!=current_user.user_id].reset_index(drop=True)
    print(len(uans))
    uans=[uans["A{}".format(nn)][0] for nn in range(1,n+1)]
    mdf=pd.DataFrame()
    for x in range(1,n+1):
        dff = ans[ans["A{}".format(x)].isin(uans)]

        if mdf.empty:
            mdf=dff
        else:
            mdf=pd.concat([mdf,dff])
    scores={}
    for user in pd.unique(mdf["user_id"]):
        scores[user]=0
        mdff=mdf[mdf["user_id"]==user].reset_index(drop=True)
        for i,answer in enumerate(uans):
            if answer in mdff["A{}".format(i+1)].to_list():
                scores[user]+= (n+1-i)*10
    sdf=pd.DataFrame.from_dict(scores.items())
    sdf.columns = ["uid", "points"]
    ndf = sdf.sort_values(by="points", ascending=False).nlargest(
        5, "points").reset_index(drop=True)
    print(ndf)
    items = []
    users=db.get_users(ndf["uid"].to_list())
    for i, uid in enumerate(ndf['uid']):
        code = {}
        usersf = users[users["user_id"] == uid].reset_index(drop=True)
        print(uid)
        ansf = ans[ans["user_id"] == uid].reset_index(drop=True)
        print(ansf)
        u2_ans = []
        for x in range(1, n + 1):
            u2_ans.append(ansf["A{x}".format(x=x)][len(ansf) - 1])
        ua = []
        u2a = []
        ii = 0
        for u1, u2 in zip(uans, u2_ans):
            #u1,u2=u1.upper(),u2.upper()
            if u1 == u2:
                u1 = "<p style=\"background-color:green;\">" + u1 + "</p>"
                u2 = "<p style=\"background-color:green;\">" + u2 + "</p>"
                ua.append("Green")
                u2a.append("Green")

                continue
            elif u1 in u2_ans or u2 in uans:
                if u1 in u2_ans:
                    u1 = "yellow"
                else:
                    u1 = "red"
                if u2 in uans:
                    u2 = "yellow"
                else:
                    u2 = "red"
                ua.append(u1)

                u2a.append(u2)
                continue
            else:
                u1 = "<p style=\"background-color:red;\">" + u1 + "</p>"
                u2 = "<p style=\"background-color:red;\">" + u2 + "</p>"
                ua.append("red")
                u2a.append("red")

        code = {"uname": usersf['username'][0],
                "id":usersf['user_id'][0],
                "points": ndf["points"][i],
                "index": i + 1,

                "u_resp": uans,
                "col1": ua,
                "col2": u2a,
                "u2_resp": u2_ans}

        items.append(code)
    print(sdf)
    d1=[]
    d2=[]
    for x in range(1, n+1):

        [d1.append(y) for y in anso["A{x}".format(x=x)]]
        [d2.append(6-x) for y in anso["A{x}".format(x=x)]]

    print(d2, d1)
    df = pd.DataFrame([d1, d2]).transpose()
    df.columns = ["Ans", "Score"]
    dfs,dft= pd.DataFrame(df.groupby(["Ans"])["Score"].sum()),pd.DataFrame(df.groupby(["Ans"]).count())
    dfs["Total Answers"]=dft["Score"]
    dfs=dfs.reset_index()
    print(dfs.index)
    ans=[]
    for i,x in enumerate(dfs["Ans"]):
        ans.append({"ans":x,"score":dfs["Score"][i],"ta":dfs["Total Answers"][i]})
    return render_template("home/view3.html",items=items,ans=ans,config=Config())
@app.route("/matches",methods=["GET"])
def matches():
    try:
        current_user.user_id
    except:
        return render_template("accounts/register.html",config=Config())
@app.route("/fetch/<pid>",methods=["POST","GET"])
def fetch(pid):

    return (db.get_poll_ans(pid))
@app.route("/addPoll",methods=["POST"])
def add_poll():
    db.add_poll(request.form["question"],request.form["n"],request.form["type"],current_user.user_id)

    return redirect("/")
@app.route("/answer/<pid>",methods=["POST"])
def answer(pid):

    ans=[]
    for a in range(0,11):
        try:
            ans.append(request.form[f"A{a}"])
            print(ans)
        except:
            break



    db.add_answer(current_user.user_id,pid,ans)
    return redirect("/")
@app.route("/setKeys",methods=["POST"])
def set_keys():
    uid=current_user.user_id
    db.set_keys(uid,request.form["papi"],request.form["papis"],request.form["dapi"],request.form["dapis"])
    return redirect(BASE)

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
            return redirect("/")

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
        print(user)
        if user:
            if check_password_hash(user.pw, request.form["password"]):
                login_user(user, force=True, remember=True)
                return redirect(BASE)

        return render_template("accounts/login.html", email=request.form["email"], pw=request.form["password"], BASE=BASE, config=Config())
    else:
        return render_template('accounts/login.html',config=Config())

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)

