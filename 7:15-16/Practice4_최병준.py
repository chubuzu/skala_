"""
========================================================================
프로그램 설명: [실습 3] 시각화4종 통계 검정 sklearn Pipeline
작성일: 2026-07-16
작성자: 최병준
========================================================================
"""



import numpy as np
import pandas as pd
import polars as pl
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
import plotly.express as px
from scipy import stats

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import Ridge
from sklearn.model_selection import train_test_split
import joblib

_installed = {f.name for f in fm.fontManager.ttflist}
_kor_font = next((f.name for f in fm.fontManager.ttflist if 'Nanum' in f.name), None)
if _kor_font:
    plt.rcParams['font.family'] = _kor_font
plt.rcParams['axes.unicode_minus'] = False


df = pd.read_csv('sales_100k.csv')
df['order_date'] = pd.to_datetime(df['order_date'])
df['month'] = df['order_date'].dt.strftime('%m월')

#IQR을 이용한 lo, hi 계산 (이상치 제거 기준) 
Q1 = df['amount'].quantile(0.25)
Q3 = df['amount'].quantile(0.75)
IQR = Q3 - Q1
lo, hi = Q1 - 1.5 * IQR, Q3 + 1.5 * IQR 
df_clean = df[(df['amount'].between(lo, hi))]

df_monthly = df_clean.groupby('month')['amount'].sum().reset_index()


#월별 라인
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

axes[0, 0].plot(df_monthly['month'], df_monthly['amount'], color='steelblue', lw=2, marker='o', label='매출')
axes[0, 0].set_title('월별 매출 추이')
axes[0, 0].set_xlabel('월'); axes[0, 0].set_ylabel('원')
axes[0, 0].legend(); axes[0, 0].grid(alpha=0.3)

#히스토그램 + KDE
sns.histplot(data=df_clean, x='amount', kde=True, ax=axes[1, 0])

#박스플롯
sns.boxplot(data=df_clean, x='region', y='amount', ax=axes[0, 1])

#상관 히트맵
corr = df_clean.select_dtypes('number').corr()
sns.heatmap(corr, annot=True, fmt='.2f', cmap='coolwarm', ax=axes[1,1])
plt.tight_layout(); plt.show()



#T-test
group_a = df_clean[df_clean['region'] == '서울']['amount']
group_b = df_clean[df_clean['region'] == '부산']['amount']
t_stat, p_val_t = stats.ttest_ind(group_a, group_b, nan_policy='omit') 
p_val_t: float = float(p_val_t)

print(f"T-test 결과: t_stat={t_stat:.3f}, p_val_t={p_val_t:.3f}")

if p_val_t < 0.05:
    print('통계적으로 유의미한 차이 있음')
else:
    print('우연일 수 있음')


#카이제곱 지역과 카테고리 독립성
from scipy.stats import chi2_contingency

ct = pd.crosstab(df_clean['region'], df_clean['category'])
chi2, p_val_chi2, dof, expected = chi2_contingency(ct)
p_val_chi2: float = float(p_val_chi2)
print(f"Chi-square 결과: chi2={chi2:.3f}, p_val_chi2={p_val_chi2:.3f}")

if p_val_chi2 < 0.05:
    print('통계적으로 유의미한 차이 있음')
else:
    print('우연일 수 있음') 


#df_clean에서 수치형 컬럼과 범주형 컬럼을 자동으로 분류하는 함수
def get_numeric_and_categorical_cols(df, target_col='amount'):
    """
    데이터프레임에서 타겟 변수를 제외하고 
    수치형(numeric) 컬럼과 범주형(categorical) 컬럼을 자동으로 분류하여 리스트로 반환합니다.
    """
    # 1. 타겟 컬럼을 제외한 분석용 데이터프레임 생성
    feature_df = df.drop(columns=[target_col], errors='ignore')
    
    # 2. 수치형 컬럼 분류 (정수형, 실수형)
    # 'datetime'이나 'period' 형식은 수치형 전처리(StandardScaler) 대상이 아니므로 제외합니다.
    num_cols = feature_df.select_dtypes(include=['int64', 'float64']).columns.tolist()
    
    # 3. 범주형 컬럼 분류 (문자열, 카테고리형)
    # 그래프를 그릴 때 쓰이는 'month'나 'order_date' 등의 날짜 관련 컬럼도 인코딩에서 제외하고 싶다면 여기에 추가합니다.
    exclude_cols = ['month', 'order_date']
    # 'string'을 명시적으로 추가하여 경고를 지워줍니다.
    cat_cols = feature_df.select_dtypes(include=['object', 'category', 'string']).columns.tolist()
    cat_cols = [col for col in cat_cols if col not in exclude_cols]
    
    return num_cols, cat_cols

num_cols, cat_cols = get_numeric_and_categorical_cols(df_clean, target_col='amount')


#sklearn Pipeline 학습
X = df_clean[num_cols + cat_cols] # 학습할 데이터
y = df_clean['amount'] #예측할 데이터

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42) #학습할 데이터 테스트 데이터 나누기

preproc = ColumnTransformer([
    ('num', StandardScaler(), num_cols),
    ('cat', OneHotEncoder(), cat_cols)
])
model = Pipeline([
    ('prep', preproc),
    ('reg', Ridge(alpha=1.0))
])

model.fit(X_train, y_train) #학습
r2score = model.score(X_test, y_test) #학습 데이터 r2값 검증
print(f'R2: {r2score:.3f}')


joblib.dump(model, 'model.pkl')
loaded = joblib.load('model.pkl')
y_pred = loaded.predict(X_test)
print(y_pred)


monthly_df = df_clean.groupby(['region', 'category'])['amount'].sum().reset_index()

fig2 = px.bar(
    monthly_df, 
    x='region', 
    y='amount', 
    color='category',  
    barmode='group',  # 누적 막대가 아닌 나란히 배치하는 스타일
    title='지역 카테고리별 총 매출'
)

fig2.update_layout(xaxis_categoryorder='category ascending')

# HTML 저장
fig2.write_html('analysis.html')
print("시각화 리포트 저장 완료: 'analysis.html'")



