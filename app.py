from flask import Flask, render_template, request, send_file, redirect, session, url_for
import requests
import json
import pandas as pd
import time
from datetime import datetime
import re

from flask_cors import CORS

app = Flask(__name__)
# 모두 허용
CORS(app)

app.secret_key = "ABCDEFG"

from OracleDB import DBManager
db = DBManager()

# 회원가입
@app.route("/register")
def register():
    return render_template('index-register.html')

@app.route("/registerDo", methods=['POST'])
def registerDo():
    print(request)
    userId = request.form['userId']
    userNm = request.form['userNm']
    userEmail = request.form['userEmail']
    userPw = request.form['userPw']
    sql = "INSERT INTO tb_user (user_id, user_nm, user_email, user_pw) VALUES (:1, :2, :3, :4)"
    db.execute_query(sql, (userId, userNm, userEmail, userPw))
    return render_template('index-login.html')

# 로그인
@app.route("/login")
def login():
    return render_template('index-login.html')

@app.route("/loginDo", methods=['POST'])
def loginDo():
    print(request)
    userId = request.form['userId']
    userPw = request.form['userPw']
    sql1 = "SELECT user_pw FROM tb_user WHERE user_id = (:1)"
    pw = db.fetch_one(sql1, [userId])
    if(pw[0] == userPw):
        sql2 = "SELECT user_nm, user_email FROM tb_user WHERE user_id = (:1)"
        userNm, userEmail = db.fetch_one(sql2, [userId])
        user = {'userId': userId, 'userNm':userNm, 'userEmail':userEmail}
        print(user)
        session['user'] = user
        return render_template('main.html')
    else:
        return render_template('index-login.html')
# 로그아웃
@app.route('/logout')
def logout():
    session.pop('user', None)
    return render_template('index-login.html')

@app.route("/")
def index():
    return render_template('index.html')

# 메인
@app.route("/main")
def main():
    if 'user' in session:
        userNm = session['user']['userNm']
        return render_template('main.html', userNm=userNm)
    return redirect("/login")

# 읽을 책 목록
@app.route("/goals")
def goals():
    if 'user' in session:
        userNm = session['user']['userNm']
        return render_template('index-goals.html', userNm=userNm, idx=0)
    return redirect("/login")

from searchBookAPI import get_naver
@app.route("/findbook", methods=['POST'])
def findbook():
    searchBook = request.form['searchBook']
    booklists = get_naver(searchBook)
    print(booklists)
    userNm = session['user']['userNm']
    return render_template('index-goals.html', userNm=userNm, booklists=booklists, idx=1)

# 읽은 책 목록
@app.route("/list")
def list():
    if 'user' in session:
        userNm = session['user']['userNm']
        return render_template('index-list.html', userNm=userNm)
    return redirect("/login")

# 상세 기록
@app.route("/tables")
def tables():
    if 'user' in session:
        userNm = session['user']['userNm']
        return render_template('index-tables.html', userNm=userNm)
    return redirect("/login")

# 마이페이지
@app.route("/mypage")
def mypage():
    if 'user' in session:
        user = session['user']

        userId = user['userId']
        userNm = user['userNm']
        userEmail = user['userEmail']
        return render_template('index-mypage.html',
                               userId=userId, userNm=userNm, userEmail=userEmail)
    else:
        return render_template('index-login.html')

@app.route("/mypageEditDo", methods=['POST'])
def mypageEditDo():
    userId = request.form['userId']
    userNm = request.form['userNm']
    userEmail = request.form['userEmail']
    sql = "UPDATE tb_user SET user_nm=:nm, user_email=:em WHERE user_id=:id"
    db.execute_query(sql, {"nm":userNm, "em":userEmail, "id":userId})
    session.pop('user', None)
    user = {'userId': userId, 'userNm': userNm, 'userEmail': userEmail}
    session['user'] = user
    return redirect(url_for('mypage'))

if __name__ == '__main__':
    app.run(debug=True) # 디폴트 포트 지정 5000, 단순로컬호스트
    # app.run(debug=True, port=5500, host="0.0.0.0") # 로컬 호스트로도, 휴대폰 ip로도 접근 가능. 즉, 배포가능