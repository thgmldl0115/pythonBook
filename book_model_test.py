import joblib
import pandas as pd
import json
# 1. 저장된 모델과 라벨 인코더 로드
model = joblib.load('linear_model.pkl')
label_encoder = joblib.load('label_encoder.pkl')
# 2. 새로운 책에 대한 예측
# 예: 카테고리 800, 페이지 수 350인 책에 대한 예측
new_category = '800'
new_pages = 164
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

print(result)
