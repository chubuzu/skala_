"""
========================================================================
프로그램 설명: [실습 3] Pandas EDA Polars Lazy DuckDB SQL 비교
작성일: 2026-07-16
작성자: 최병준
========================================================================
"""

import pandas as pd
import polars as pl
import duckdb
import timeit

df = pd.read_csv('sales_100k.csv')

#데이터 형태와 타입 확인
df.shape
df.info()
df.describe(include='all')


#데이터 결측치 수와 비율 확인
print("결측치 수:")
print(df.isna().sum())
print("\n결측치 비율:")
print(df.isna().sum() / len(df) * 100)

#IQR을 이용한 lo, hi 계산 (이상치 제거 기준) 
Q1 = df['amount'].quantile(0.25)
Q3 = df['amount'].quantile(0.75)
IQR = Q3 - Q1
lo, hi = Q1 - 1.5 * IQR, Q3 + 1.5 * IQR 


def Run_Pandas_aggregation():

    df = pd.read_csv('sales_100k.csv')
    df_clean = df[(df['amount'].between(lo, hi))]
    #Pandas 지역별 통계
    region_statistics = df.groupby('region').agg(
        sum = ('amount', 'sum'),
        mean = ('amount', 'mean'),
        cnt = ('amount', 'count')
    ).sort_values(by='sum', ascending=False)


    #Pandas 카테고리별 통계
    category_statistics = df.groupby('category').agg(
        sum = ('amount', 'sum'),
        mean = ('amount', 'mean'),
        cnt = ('amount', 'count')
    ).sort_values(by='sum', ascending=False)

    return region_statistics, category_statistics


#Polars LazyFrame을 이용한 EDA
def Run_Polars_aggregation():
    

    #Polars LazyFrame 지역별 통계
    df_pl_region = (pl.scan_csv('sales_100k.csv',
                    schema_overrides={'amount': pl.Float64})
    .filter(pl.col('amount').is_between(lo, hi))
    .group_by('region')
    .agg([pl.col('amount').sum().alias('sum'),
        pl.count('amount').alias('cnt'),
        pl.col('amount').mean().alias('mean')])
    .sort('sum', descending=True)
    .collect()
    )


    #Polars LazyFrame 카테고리별 통계
    df_pl_category = (pl.scan_csv('sales_100k.csv',
                        schema_overrides={'amount': pl.Float64})
    .filter(pl.col('amount').is_between(lo, hi))
    .group_by('category')
    .agg([pl.col('amount').sum().alias('sum'),      
        pl.count('amount').alias('cnt'),
        pl.col('amount').mean().alias('mean')])
    .sort('sum', descending=True)
    .collect()
    )

    return df_pl_region, df_pl_category

#DuckDB SQL을 이용한 EDA
def DuckDB_aggregation():
    
    #DuckDB 지역별 통계
    duckdb_region = duckdb.sql(f"""
    SELECT region, SUM(amount) AS sum, AVG(amount) AS mean, COUNT(amount) AS cnt
    FROM 'sales_100k.csv'
    WHERE amount BETWEEN {lo} AND {hi}
    GROUP BY region
    ORDER BY sum DESC
    """).df()



    #DuckDB 카테고리별 통계
    duckdb_category = duckdb.sql(f"""
    SELECT category, SUM(amount) AS sum, AVG(amount) AS mean, COUNT(amount) AS cnt
    FROM 'sales_100k.csv'
    WHERE amount BETWEEN {lo} AND {hi}
    GROUP BY category
    ORDER BY sum DESC
    """).df()

    return duckdb_region, duckdb_category


# 1. Pandas 결과
pd_region, pd_category = Run_Pandas_aggregation()
print(f"\nPandas 지역별 통계:\n{pd_region}\n\nPandas 카테고리별 통계:\n{pd_category}")
print("-" * 50)

# 2. Polars 결과
pl_region, pl_category = Run_Polars_aggregation()
print(f"\nPolars Lazy 통계 (지역):\n{pl_region}\n\nPolars Lazy 통계 (카테고리):\n{pl_category}")
print("-" * 50)

# 3. DuckDB 결과
duck_region, duck_category = DuckDB_aggregation()
print(f"\nDuckDB SQL 통계 (지역):\n{duck_region}\n\nDuckDB SQL 통계 (카테고리):\n{duck_category}")
print("="*50 + "\n")


print("성능 비교")

RUN_NUMBER = 10

try:
    # 1. Pandas 실행 시간 측정 (이상치 처리 + Named Aggregation)
    # 실제 파일 로드 후의 변환 흐름을 비교하기 위해 결측치/이상치 정제부터 포함
    pandas_time = timeit.timeit(
        stmt="Run_Pandas_aggregation()",
        globals=globals(),
        number=RUN_NUMBER
    )

    # 2. Polars Lazy 실행 시간 측정 (scan_csv부터 collect까지의 전체 파이프라인)
    polars_time = timeit.timeit(
        stmt="Run_Polars_aggregation()",
        globals=globals(),
        number=RUN_NUMBER
    )

    # 3. DuckDB SQL 실행 시간 측정 (CSV 다이렉트 쿼리부터 DataFrame 변환까지)
    duckdb_time = timeit.timeit(
        stmt="DuckDB_aggregation()",
        globals=globals(),
        number=RUN_NUMBER
    )

    # 결과 표 형태로 깔끔하게 출력
    print(f"반복 횟수 (number): {RUN_NUMBER}회")
    print("-" * 45)
    print(f"{'Engine':<15} | {'Total Time (sec)':<20}")
    print("-" * 45)
    print(f"{'Pandas':<15} | {pandas_time:.5f} sec")
    print(f"{'Polars Lazy':<15} | {polars_time:.5f} sec")
    print(f"{'DuckDB SQL':<15} | {duckdb_time:.5f} sec")
    print("-" * 45)

except Exception as e:
    print(f"[오류] 성능 측정(timeit) 중 예외가 발생했습니다: {e}")