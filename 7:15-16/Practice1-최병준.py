"""
========================================================================
프로그램 설명: [실습 1] 자료구조 집계, 컴프리헨션, 제너레이터를 활용한 매출 데이터 분석
작성일: 2026-07-15
변경 내역:
    - V1.0: 외부 파일 대신 직접 입력된 내부 JSON 데이터를 활용하도록 전면 변경 (파일 로드 오류 원천 해결)
========================================================================
"""

import sys
import json
from collections import Counter, defaultdict

# ======================================================================
# [데이터 직접 매핑]
# ======================================================================

with open("Python_Practice1_Data.json", "r", encoding="utf-8")as f:
    data = json.load(f)



def main():
    sales = data
    
    print("=== 데이터 매핑 완료 ===")
    print(f"=== 총 거래 건수: {len(sales)}건 ===")
    print("-" * 60)

    # ======================================================================
    # 1) 리스트/딕셔너리 컴프리헨션
    #    - amount >= 1000 필터링 후 지역별 총매출 계산
    # ======================================================================
    print("[1] 리스트/딕셔너리 컴프리헨션 수행 중...")
    
    filtered_sales = [item for item in sales if item.get("amount", 0) >= 1000]
    unique_regions = {item["region"] for item in filtered_sales if "region" in item}
    
    region_total = {
        region: sum(item["amount"] for item in filtered_sales if item["region"] == region)
        for region in unique_regions
    }
    
    print(f"-> 필터링된 지역별 총매출 (region_total): {region_total}")
    
    try:
        assert isinstance(region_total, dict), "region_total은 dict 타입이어야 합니다."
        print("-> region_total 타입 검증 통과!")
    except AssertionError as ae:
        print(f"-> [검증 실패] {ae}")
    
    print("-" * 60)

    # ======================================================================
    # 2) Counter + defaultdict
    #    - Counter로 지역별 빈도 수집, defaultdict로 카테고리별 amount 누적
    # ======================================================================
    print("[2] Counter & defaultdict 집계 수행 중...")
    
    region_counts = Counter(item["region"] for item in sales if "region" in item)
    print(f"-> 지역별 거래 건수 (Counter): {region_counts}")
    print(f"-> 거래 건수 순위 (most_common): {region_counts.most_common()}")
    
    category_amounts = defaultdict(list)
    for item in sales:
        if "category" in item and "amount" in item:
            category_amounts[item["category"]].append(item["amount"])
            
    print(f"-> 카테고리별 매출 리스트: {dict(category_amounts)}")
    print("-" * 60)

    # ======================================================================
    # 3) 제너레이터 — 메모리 비교
    #    - sys.getsizeof()를 통한 리스트 객체와 제너레이터 객체 자체 크기 비교
    # ======================================================================
    print("[3] 제너레이터 vs 리스트 메모리 비교 수행 중...")
    
    def amount_generator(data_list):
        for item in data_list:
            if item.get("amount", 0) > 1000:
                yield item

    gen_obj = amount_generator(sales)
    list_obj = [item for item in sales if item.get("amount", 0) > 1000]
    
    gen_memory = sys.getsizeof(gen_obj)
    list_memory = sys.getsizeof(list_obj)
    
    print(f"-> 제너레이터 객체 메모리 크기: {gen_memory} bytes")
    print(f"-> 리스트 객체 메모리 크기: {list_memory} bytes")
    
    try:
        assert gen_memory < list_memory, "제너레이터의 메모리 사용량이 더 작아야 합니다."
        print("-> Generator 메모리 효율성 검증 통과!")
    except AssertionError as ae:
        print(f"-> [검증 실패] {ae}")
        
    print("-" * 60)

    # ======================================================================
    # 4) 종합 - 월별 카테고리 매출 집계
    #    - "month" 필드 값이 "2024-01" 형식이므로 뒷자리 2글자(월)만 파싱하여 그룹핑 수행
    # ======================================================================
    print("[4] 종합: 월별 카테고리 매출 집계 수행 중...")
    
    def parse_only_month(month_str):
        """'2024-01' 형태의 문자열에서 월 데이터('01')만 추출합니다."""
        try:
            return month_str.split("-")[1]
        except (IndexError, AttributeError):
            return "Unknown"

    monthly_category_sales = defaultdict(int)
    
    for item in sales:
        # month 필드로부터 월('01', '02' 등) 추출
        month = parse_only_month(item.get("month"))
        category = item.get("category", "Unknown")
        amount = item.get("amount", 0)
        
        group_key = (month, category)
        monthly_category_sales[group_key] += amount
        
    final_report = dict(monthly_category_sales)
    print(f"-> 월별 카테고리 그룹핑 매출 집계: {final_report}")
    
    # 금액 내림차순 정렬 및 상위 3개 그룹 출력 (Checkpoint 반영)
    sorted_sales = sorted(final_report.items(), key=lambda x: x[1], reverse=True)
    top_3 = sorted_sales[:3]
    
    print("\n-> Top 3 매출 그룹 (내림차순):")
    for rank, (key, value) in enumerate(top_3, start=1):
        print(f"   {rank}위: {key[0]}월 | 카테고리: {key[1]} | 총매출: {value}")
    



if __name__ == "__main__":
    main()