import cx_Oracle
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GridSearchCV
from sklearn.ensemble import GradientBoostingRegressor
from xgboost import XGBRegressor
import joblib
import numpy as np
import json


# 1. Oracle 데이터베이스에서 데이터 가져오기
def fetch_data_from_oracle():
    conn = cx_Oracle.connect("book", "book", "192.168.0.19:1521/xe")
    query = """
        SELECT a.b_isbn
             , a.b_page
             , a.b_category
             , ROUND(AVG(b.r_page), 2) AS read_speed
             , MIN(b.r_date) AS start_dt
             , MAX(b.r_date) AS end_dt
             , COUNT(  b.r_date) AS days_since_last_read
        FROM tb_book a
           , tb_bookrecord b
        WHERE a.b_isbn = b.b_isbn
        GROUP BY a.b_isbn
               , a.b_page
               , a.b_category
        ORDER BY start_dt
    """

    df = pd.read_sql(query, conn)
    conn.close()
    return df


# 2. 데이터 불러오기 및 전처리
df = fetch_data_from_oracle()

# 날짜 변환 및 총 일수 계산
df['START_DT'] = pd.to_datetime(df['START_DT'])
df['END_DT'] = pd.to_datetime(df['END_DT'])
df['TOTAL_DAYS'] = (df['END_DT'] - df['START_DT']).dt.days  # 책 완독까지 걸린 총 기간

# 라벨 인코딩 적용
label_encoder = LabelEncoder()
df['B_CATEGORY_ENCODED'] = label_encoder.fit_transform(df['B_CATEGORY'])

# 3. 특징과 타겟 변수 분리
X = df[['B_CATEGORY_ENCODED', 'B_PAGE']]
y = df['TOTAL_DAYS']

# 4. 학습/테스트 데이터 분할
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.5, random_state=42)

# 5. 모델 학습
# 회귀모델
# model = LinearRegression()
# model.fit(X_train, y_train)

# 랜덤 포레스트 모델 정의
# model = RandomForestRegressor()
# model.fit(X_train, y_train)

# Gradient Boosting Regressor 모델 정의 및 학습
# model = GradientBoostingRegressor(n_estimators=500, learning_rate=0.01, max_depth=6, random_state=42)
# model.fit(X_train, y_train)

model = XGBRegressor(n_estimators=100, random_state=1)
model.fit(X_train, y_train)

# 6. 예측 및 평가
y_pred = model.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
r2 = r2_score(y_test, y_pred)

print("Mean Absolute Error (MAE):", mae)
print("Root Mean Squared Error (RMSE):", rmse)
print("R-squared (R^2) Score:", r2)

# 6. 모델과 라벨 인코더 저장
joblib.dump(model, 'linear_model.pkl')          # 모델 저장
joblib.dump(label_encoder, 'label_encoder.pkl')  # 라벨 인코더 저장
print("모델과 라벨 인코더가 저장되었습니다.")
