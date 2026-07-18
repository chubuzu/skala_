"""
========================================================================
프로그램 설명: [종합실습2] 머신 러닝을 활용한 당월 매출 금액 예측
작성일: 2026-07-16
작성자: 최병준
========================================================================
"""



import pandas as pd
import plotly.express as px

selected_columns = [
    '상권_코드_명', '상권_구분_코드_명', '서비스_업종_코드', '서비스_업종_코드_명','당월_매출_금액',
    '남성_매출_금액', '여성_매출_금액', '연령대_10_매출_금액', '연령대_20_매출_금액', '연령대_30_매출_금액'
]

df = pd.read_csv('서울시 상권분석서비스(추정매출-상권).csv', encoding='cp949', usecols=selected_columns) #selected_columns만 읽어오기

#서비스 업종코드별로 묶어서 당월 매출 금액 총합 구하고 내림차순 정렬 후 상위 10개

month_amount_sum_by_category = df.groupby('서비스_업종_코드').agg(
                                sum = ('당월_매출_금액', 'sum')
).sort_values(by = 'sum', ascending = False).head(10)


print(month_amount_sum_by_category)


#연령대별 컬럼 합계 bar 그래프 작성

#차트 개요 작성
age_cols = ['연령대_10_매출_금액', '연령대_20_매출_금액', '연령대_30_매출_금액']
sum_age = df[age_cols].sum()
df_age_sum = pd.DataFrame({
    '연령대': ['10대', '20대', '30대'], 
    '매출합계': sum_age.values
})

#각 레이블에 들어갈 항목 작성
fig_age = px.bar(
    df_age_sum,
    x='연령대',
    y='매출합계',
    color='연령대',
    text_auto=True, 
    title='연령대별(10대~30대) 총 매출 금액 합계'
)

#레이아웃 작성
fig_age.update_layout(
    title_x=0.5, 
    xaxis_title='연령대',
    yaxis_title='총 매출 금액 (원)',
    showlegend=False 
)

#그래프 작성 후 파일로 저장
fig_age.write_html('age_sales_analysis.html')
print("연령대별 매출 시각화 저장 완료: 'age_sales_analysis.html'")


#파이프라인 작성 시작
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score
import joblib

#학습할 데이터를 숫자형과 카테고리형으로 구분
num_cols = ['연령대_10_매출_금액', '연령대_20_매출_금액', '연령대_30_매출_금액']
cat_cols = ['상권_구분_코드_명', '서비스_업종_코드_명']

#학습할 데이터와 만들어낼 결과값 설정
X = df[num_cols + cat_cols]
y = df['당월_매출_금액'] 

#학습할 데이터와 테스트 데이터 구분
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 결측치를 중간값(median)으로 대체 # 데이터 표준화 스케일링
numeric_features = Pipeline(steps=[
    ('imputer', SimpleImputer(strategy='median')),  
    ('scaler', StandardScaler())                    
])

# 범주형 파이프라인 (결측치('missing') + 원핫인코딩)
categorical_features = Pipeline(steps=[
    ('imputer', SimpleImputer(strategy='constant', fill_value='missing')), 
    ('onehot', OneHotEncoder(handle_unknown='ignore'))                    
])

# 위 2개의 파이프라인을 하나로 결합
preprocessor = ColumnTransformer(
    transformers=[
        ('num', numeric_features, num_cols),
        ('cat', categorical_features, cat_cols)
    ]
)

# 4) 최종 모델 파이프라인 완성 (전처리 + 모델)
model = Pipeline(steps=[
    ('preprocessor', preprocessor),
    ('regressor', Ridge(alpha=1.0))
])

# 모델 학습
model.fit(X_train, y_train) 

# R2값 검증
r2score = model.score(X_test, y_test) 
print(f'R2: {r2score:.3f}')

# 모델 저장 및 로드
joblib.dump(model, 'model.pkl')
loaded = joblib.load('model.pkl')