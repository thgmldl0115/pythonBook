
from flask import Flask, render_template, request, send_file, redirect, session, url_for
import requests
import json
import pandas as pd
import numpy as np
import time
from datetime import datetime
import re
import cx_Oracle

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
    userId = request.form['userId']
    userPw = request.form['userPw']
    sql1 = "SELECT user_pw FROM tb_user WHERE user_id = (:1)"
    pw = db.fetch_one(sql1, [userId])
    if(pw[0] == userPw):
        sql2 = "SELECT user_nm, user_email FROM tb_user WHERE user_id = (:1)"
        userNm, userEmail = db.fetch_one(sql2, [userId])
        user = {'userId': userId, 'userNm':userNm, 'userEmail':userEmail}
        session['user'] = user
        return redirect(url_for('main'))
    else:
        return redirect(url_for('login'))

# 로그아웃
@app.route('/logout')
def logout():
    session.pop('user', None)
    return render_template('index-login.html')

@app.route("/")
def index():
    return redirect("/main")

# 메인
@app.route("/main")
def main():
    if 'user' in session:
        userNm = session['user']['userNm']
        userId = session['user']['userId']
        print("==^^==")
        sql = """
            SELECT distinct a.b_title, a.b_author, a.b_isbn, 
                 NVL(SUM(b.r_page) OVER(PARTITION BY b.b_isbn), 0) as cur_page,
                 a.b_page,
                (a.b_page - NVL(SUM(b.r_page) OVER(PARTITION BY b.b_isbn), 0)) as to_page,
                 a.b_create_dt
            FROM tb_book a, tb_bookrecord b
            WHERE a.b_isbn = b.b_isbn(+)
            AND a.user_id = b.user_id(+)
            AND a.user_id = (:id)
            AND a.b_end_yn = 'N'
            ORDER BY a.b_create_dt
        """
        mylists = db.fetch_all(sql, {"id":userId})

        sql2 = """
            SELECT sum(b_dicount) as yrmoney
            FROM tb_book
            WHERE user_id=(:id)
        """
        yrmoney = db.fetch_one(sql2, {"id":userId})

        sql3 = """  
            SELECT sum(b.r_page) as yrpage
                  ,count(distinct a.b_isbn) as yrbook
                  ,count(distinct r_date) as yrdt
            FROM tb_book a, tb_bookrecord b
            WHERE a.b_isbn = b.b_isbn(+) 
            AND a.user_id = b.user_id(+)
            AND b.b_isbn IS NOT NULL
            AND b.user_id=(:id)
        """
        yrs = db.fetch_one(sql3, {"id":userId})

        sql4 = """
            SELECT TO_CHAR(a. b_update_dt, 'YYYYMMDD') as lastday
                 , a.b_title as lastbook
            FROM tb_book a
            WHERE b_update_dt = (
                                    SELECT MAX(b.b_update_dt)
                                    FROM tb_book b
                                    WHERE b.user_id=(:id)
                                    AND a.user_id = b.user_id)
        """
        lasts = db.fetch_one(sql4, {"id":userId})

        mday, mpage = graph_data_line()

        piedata = graph_data_pie()

        page_title = userNm + '\'s BookBoard'
        return render_template('main.html', userNm=userNm
                               , mylists=mylists, yrmoney=yrmoney, yrs=yrs, lasts=lasts
                               , mday=mday, mpage=mpage, piedata=piedata, page_title=page_title)
    return redirect("/login")

def graph_data_line():
    sql = """
        SELECT SUBSTR(dt, 5,2) || '월' as mon
              ,SUM(page) OVER(ORDER BY dt
                                ROWS BETWEEN UNBOUNDED PRECEDING 
                                            AND CURRENT ROW) as page
        FROM(
        SELECT TO_CHAR(r_date, 'YYYYMM') as dt
              ,SUM(r_page)  as page
        FROM tb_bookrecord
        WHERE user_id = (:id)
        GROUP BY TO_CHAR(r_date, 'YYYYMM')
        ORDER BY dt)
    """
    df1 = db.fetch_all(sql,{"id":session['user']['userId']})
    mday = []
    mpage = []
    for i in range(len(df1)):
        mday.append(df1[i][0])
        mpage.append(df1[i][1])
    page_main = [
        {
            'name' : 'page',
            'data' : mpage,
        }
    ]
    return mday, page_main

def graph_data_pie():
    sql = """
        SELECT CASE b_category WHEN '000' THEN '총류, 컴퓨터과학'
                             WHEN '100' THEN '철학, 심리학, 윤리학'
                             WHEN '200' THEN '종교'
                             WHEN '300' THEN '사회과학'
                             WHEN '400' THEN '자연과학'
                             WHEN '500' THEN '기술과학'
                             WHEN '600' THEN '예술'
                             WHEN '700' THEN '언어'
                             WHEN '800' THEN '문학'
                             WHEN '900' THEN '역사'
                             ELSE '기타'
                             END as b_category
              ,COUNT(b_category) as cnt
        FROM tb_book
        WHERE user_id = (:id)
        AND b_end_yn = 'Y'
        GROUP BY b_category
    """
    df1 = db.fetch_all(sql,{"id":session['user']['userId']})

    return df1

@app.route("/addBookRecord", methods=['POST'])
def addBookRecord():
    userId = session['user']['userId']
    readDate = request.form['readDate']
    isbn = request.form['mybook']
    page = request.form['today-page']

    sql = """
        INSERT INTO tb_bookrecord(user_id, b_isbn, r_date, r_page)
        VALUES(:id, :isbn, TO_DATE(:readDate, 'YYYY-MM-DD'), :page)
    """
    db.execute_query(sql,
             {"id":userId, "isbn":isbn, "readDate":readDate, "page":page})

    sql2 = """
                UPDATE tb_book a
                SET (a.b_create_dt, a.b_update_dt) = (
                                                        SELECT distinct MIN(r_date) OVER(PARTITION BY b_isbn)
                                                              ,MAX(r_date) OVER(PARTITION BY b_isbn)
                                                        FROM tb_bookrecord b
                                                        WHERE b.b_isbn(+) = a.b_isbn
                                                        AND a.user_id = b.user_id(+)
                                                        AND  b.r_date IS NOT NULL
                                                        )
                WHERE a.user_id=(:id)
            """
    db.execute_query(sql2, {"id":userId})

    sql3 = """
            UPDATE tb_book a
            SET a.b_end_yn = 'Y'
            WHERE (a.b_isbn, a.b_page) IN (
                                            SELECT b.b_isbn, SUM(b.r_page) OVER(PARTITION BY b.b_isbn)
                                            FROM tb_bookrecord b
                                            WHERE b.b_isbn = a.b_isbn
                                            AND a.user_id = b.user_id
                                            )
            AND a.user_id=(:id)
    """
    db.execute_query(sql3, {"id": userId})

    return redirect(url_for('main'))


# 읽을 책 목록
@app.route("/goals")
def goals():
    if 'user' in session:
        userNm = session['user']['userNm']
        sql = """
            SELECT  distinct
                    CASE WHEN b_create_dt IS NULL THEN 'N'
                         ELSE 'Y'
                    END as read_yn
                    , b_title, b_author,  
                    CASE WHEN b_category = '000' THEN '총류, 컴퓨터과학'
                         WHEN b_category = '100' THEN '철학, 심리학, 윤리학'
                         WHEN b_category = '200' THEN '종교'
                         WHEN b_category = '300' THEN '사회과학'
                         WHEN b_category = '400' THEN '자연과학'
                         WHEN b_category = '500' THEN '기술과학'
                         WHEN b_category = '600' THEN '예술'
                         WHEN b_category = '700' THEN '언어'
                         WHEN b_category = '800' THEN '문학'
                         WHEN b_category = '900' THEN '역사'
                         ELSE '기타'
                    END as b_category, 
                    NVL(b_memo, ' '),
                    b_page, 
                    NVL(SUM(b.r_page) OVER(PARTITION BY b.b_isbn), 0) as cur_page, 
                    NVL(TO_CHAR(b_create_dt, 'YYYY-MM-DD'),' ') as b_create_dt, 
                    NVL(TO_CHAR(b_update_dt, 'YYYY-MM-DD'),' ') as b_update_dt,
                    a.b_isbn
            FROM tb_book a, tb_bookrecord b
            WHERE a.b_isbn = b.b_isbn(+)
            AND a.user_id = b.user_id(+)
            AND a.user_id= (:1)
            AND b_end_yn = 'N'
            ORDER BY b_create_dt DESC
        """
        mybooks = db.fetch_all(sql, [session['user']['userId']])
        page_title = 'Wish List'
        return render_template('index-goals.html', userNm=userNm, mybooks=mybooks, page_title=page_title)
    return redirect("/login")

@app.route("/goalDelDo", methods=['POST'])
def goalDelDo():
    id = [session['user']['userId']][0]
    isbn = request.form['gisbn']
    sql="""
        DELETE tb_book
        WHERE user_id=(:id)
        AND b_isbn=(:isbn)
    """
    db.execute_query(sql, {"id":id, "isbn":isbn})
    return redirect('/goals')

from searchBookAPI import get_naver
@app.route("/findbook", methods=['POST'])
def findbook():

    data = json.loads(request.get_data())
    booklists = get_naver(data['books'])

    return booklists

from searchBookAPI import get_detail
@app.route("/findDetail", methods=['POST'])
def findDetail():

    data = json.loads(request.get_data())
    bookdetail = get_detail(data['books'])

    return bookdetail

import joblib
@app.route("/ml",methods=['POST'])
def ml():
    # 1. 저장된 모델과 라벨 인코더 로드
    model = joblib.load('linear_model.pkl')
    label_encoder = joblib.load('label_encoder.pkl')
    # 2. 새로운 책에 대한 예측
    data = json.loads(request.get_data())
    new_category = data['category']
    new_pages = int(data['page'])
    print(new_category)
    print(new_pages)
    # 3. 새로운 데이터에 라벨 인코딩 적용
    new_category_encoded = label_encoder.transform([new_category])[0]
    # 4. 예측을 위한 DataFrame 생성
    new_book = pd.DataFrame({
        'B_CATEGORY_ENCODED': [new_category_encoded],
        'B_PAGE': [new_pages]
    })
    # 5. 예측 수행
    predicted_total_days = model.predict(new_book)[0]
    # 6. 평균 독서 횟수와 평균 회당 페이지 수 계산
    average_reading_sessions = predicted_total_days  # 일수를 독서 횟수로 가정
    average_pages_per_session = new_pages / average_reading_sessions if average_reading_sessions > 0 else 0
    # 7. 결과를 JSON 형식으로 출력
    result = {
        "predicted_total_days": round(predicted_total_days, 2),  # 예측 일수
        "average_reading_sessions": round(average_reading_sessions, 2),  # 예상 독서 횟수
        "average_pages_per_session": round(average_pages_per_session, 2)  # 회당 평균 읽을 페이지 수
    }

    for key, value in result.items():
        if isinstance(value, np.float32):
            result[key] = float(value)

    json_result = json.dumps(result)

    return json_result



@app.route("/addBookList", methods=['POST'])
def addBookList():
    userId = session['user']['userId']
    title = request.form['title']
    author = request.form['author']
    discount = request.form['discount']
    isbn = request.form['isbn']
    page = request.form['page']
    category = request.form['category']
    memo = request.form['memo']
    image = request.form['bimage']
    ml_days = request.form['ml_days']
    ml_page = request.form['ml_page']
    sql = """
        INSERT INTO tb_book(user_id, b_title, b_author, b_dicount
                            ,b_isbn, b_page, b_category, b_memo, b_image, b_mlday, b_mlpage)
        VALUES (:id, :title, :author, :discount, :isbn, :page, :category, :memo, :image, NVL(:mlday, null), NVL(:mlpage,null))
    """
    db.execute_query(sql,
             {"id":userId, "title":title, "author":author, "discount":discount,
                     "isbn":isbn, "page":page, "category":category, "memo":memo, "image":image
                    , "mlday":ml_days, "mlpage":ml_page})

    return redirect(url_for('goals'))

# 읽은 책 목록
@app.route("/list")
def list():
    if 'user' in session:
        userNm = session['user']['userNm']
        sql = """
            SELECT distinct b.b_title, b.b_author, b.b_page
                 , TO_CHAR(b.b_create_dt, 'YYYY-MM-DD') as b_create_dt
                 , TO_CHAR(b.b_update_dt, 'YYYY-MM-DD') as b_update_dt
                 , CASE WHEN b.b_category = '000' THEN '총류, 컴퓨터과학'
                         WHEN b.b_category = '100' THEN '철학, 심리학, 윤리학'
                         WHEN b.b_category = '200' THEN '종교'
                         WHEN b.b_category = '300' THEN '사회과학'
                         WHEN b.b_category = '400' THEN '자연과학'
                         WHEN b.b_category = '500' THEN '기술과학'
                         WHEN b.b_category = '600' THEN '예술'
                         WHEN b.b_category = '700' THEN '언어'
                         WHEN b.b_category = '800' THEN '문학'
                         WHEN b.b_category = '900' THEN '역사'
                         ELSE '기타'
                    END as b_category
                 , NVL(b.b_memo, ' ')
                 , b.b_isbn
            FROM tb_bookrecord a, tb_book b, tb_user c
            WHERE a.b_isbn = b.b_isbn
            AND a.user_id = b.user_id
            AND a.user_id = c.user_id
            AND b.b_end_yn = 'Y'
            AND c.user_id=(:1)
            ORDER BY b_create_dt DESC
        """
        mybooks = db.fetch_all(sql, [session['user']['userId']])
        page_title = 'Book List'
        return render_template('index-list.html', userNm=userNm, mybooks=mybooks, page_title=page_title)
    return redirect("/login")

@app.route("/showdetail", methods=['POST'])
def showdetail():
    data = json.loads(request.get_data())
    isbn = data['bookid']
    id = session['user']['userId']
    print(type(isbn))
    print(isbn)
    sql = """
        SELECT distinct b_title, b_author, b_dicount
              ,CASE b_category WHEN '000' THEN '총류, 컴퓨터과학'
                             WHEN '100' THEN '철학, 심리학, 윤리학'
                             WHEN '200' THEN '종교'
                             WHEN '300' THEN '사회과학'
                             WHEN '400' THEN '자연과학'
                             WHEN '500' THEN '기술과학'
                             WHEN '600' THEN '예술'
                             WHEN '700' THEN '언어'
                             WHEN '800' THEN '문학'
                             WHEN '900' THEN '역사'
                             ELSE '기타'
                             END as b_category
              ,NVL(b_memo,' ') as b_memo
              ,NVL(b_mlday, ' ') as b_mlday
              ,NVL(b_mlpage, ' ') as b_mlpage
              ,b_image
              ,TO_CHAR(b_create_dt, 'YYYY-MM-DD') as b_create_dt
              ,TO_CHAR(b_update_dt, 'YYYY-MM-DD') as b_update_dt
              ,COUNT(r_date) OVER(PARTITION BY b.b_isbn) as rlday
              ,ROUND(AVG(r_page) OVER(PARTITION BY b.b_isbn),2) as rlpage
        FROM tb_book a, tb_bookrecord b
        WHERE a.user_id=(:id)
        AND a.b_isbn = (:isbn)
        AND a.b_isbn = b.b_isbn
        AND a.user_id = b.user_id
    """
    details = db.fetch_one(sql, {"id":id, "isbn":isbn})
    j_details = json.dumps(details)
    return j_details

# 상세 기록
@app.route("/tables")
def tables():
    if 'user' in session:
        userNm = session['user']['userNm']
        sql = """
            SELECT b.b_title, b.b_author
                 , TO_CHAR(a.r_date, 'YYYY-MM-DD') as r_date
                 , a.r_page
                 , SUM(a.r_page) OVER(PARTITION BY a.b_isbn
                                        ORDER BY a.r_date
                                        ROWS BETWEEN UNBOUNDED PRECEDING 
                                                AND CURRENT ROW) as sum_page
                 , b.b_page
                 , b.b_isbn
            FROM tb_bookrecord a, tb_book b
            WHERE a.b_isbn = b.b_isbn
            AND a.user_id = b.user_id
            AND a.user_id = (:1)
            ORDER BY b.b_update_dt DESC, a.r_date DESC
        """
        myrecords = db.fetch_all(sql, [session['user']['userId']])

        sql2 = """
            SELECT count(*)
            FROM tb_bookrecord
            WHERE user_id = (:1)
        """
        totalrow = db.fetch_one(sql2, [session['user']['userId']])
        page_title = 'Book Record'
        return render_template('index-tables.html', userNm=userNm, myrecords=myrecords, totalrow=totalrow, page_title=page_title)
    return redirect("/login")

@app.route("/recordDelDo", methods=['POST'])
def recordDelDo():
    id = [session['user']['userId']][0]
    isbn = request.form['isbn']
    rday = request.form['rday']

    sql = """
            DELETE tb_bookrecord
            WHERE b_isbn = (:isbn)
            AND r_date = TO_DATE((:rday),'YYYY-MM-DD')
            AND user_id = (:id)
    """
    db.execute_query(sql, {"isbn":isbn, "rday":rday, "id":id})

    sql2 = """
        UPDATE tb_book a
        SET (a.b_create_dt, a.b_update_dt) = (
                                                SELECT distinct MIN(r_date) OVER(PARTITION BY b.b_isbn)
                                                      ,MAX(r_date) OVER(PARTITION BY b.b_isbn)
                                                FROM tb_bookrecord b
                                                WHERE b.b_isbn(+) = a.b_isbn
                                                AND a.user_id = b.user_id(+)
                                                AND  b.r_date IS NOT NULL
                                                )
        WHERE a.user_id=(:id)
    """
    db.execute_query(sql2, {"id": id})

    sql3 = """
                UPDATE tb_book a
                SET a.b_end_yn = 'N'
                WHERE (a.b_isbn, a.b_page) NOT IN (
                                                SELECT b.b_isbn, SUM(b.r_page) OVER(PARTITION BY b.b_isbn)
                                                FROM tb_bookrecord b
                                                WHERE b.b_isbn = a.b_isbn
                                                AND a.user_id = b.user_id
                                                )
                AND a.user_id=(:id)
        """
    db.execute_query(sql3, {"id": id})

    return redirect('/tables')

# 마이페이지
@app.route("/mypage")
def mypage():
    if 'user' in session:
        user = session['user']

        userId = user['userId']
        userNm = user['userNm']
        userEmail = user['userEmail']
        page_title = 'My page'
        return render_template('index-mypage.html',
                               userId=userId, userNm=userNm, userEmail=userEmail, page_title=page_title)
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
    # app.run(debug=True) # 디폴트 포트 지정 5000, 단순로컬호스트
    app.run(debug=True, port=5500, host="0.0.0.0") # 로컬 호스트로도, 휴대폰 ip로도 접근 가능. 즉, 배포가능