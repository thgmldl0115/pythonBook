from flask import Flask, render_template, request, send_file
import requests
import json
import pandas as pd
import time
from datetime import datetime

from flask_cors import CORS

app = Flask(__name__)
# 모두 허용
CORS(app)

@app.route("/")
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True) # 디폴트 포트 지정 5000, 단순로컬호스트
    # app.run(debug=True, port=5500, host="0.0.0.0") # 로컬 호스트로도, 휴대폰 ip로도 접근 가능. 즉, 배포가능