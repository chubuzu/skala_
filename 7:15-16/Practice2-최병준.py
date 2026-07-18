"""
======================================================================
프로그램명 : [실습 2] 파일 I/O 및 Pydantic 검증 파이프라인
설명       : 1~4단계를 모두 통합하여 JSON 검증 및 결과 파일 분리 저장 수행
작성일자   : 2026-07-15
======================================================================
"""

import json
import logging
from typing import Optional
from pydantic import BaseModel, Field, ValidationError

# 0. 로거(Logger) 설정
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


# ==========================================
# [1단계] 예외 처리 + 파일 읽기 함수
# ==========================================
def safe_load_csv(file_path: str) -> Optional[list[dict]]:
    """
    지정한 경로의 데이터를 안전하게 로드하여 dict 리스트로 반환합니다.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info(f"데이터 로드 성공: {file_path}")
        return data

    except FileNotFoundError:
        logger.error(f"파일을 찾을 수 없습니다: {file_path}")
        return None

    except json.JSONDecodeError:
        logger.error(f"데이터 디코딩 실패: {file_path}")
        return None

    finally:
        print("로딩 종료")


# ==========================================
# [2단계] Pydantic v2 스키마 정의 (month 전용)
# ==========================================
class SalesRecord(BaseModel):
    """
    거래 기록 데이터 검증을 위한 Pydantic 모델 클래스
    """

    month: str = Field(description="거래 월 (필수)")
    region: str = Field(description="거래 지역 (필수)")
    amount: float = Field(gt=0, description="거래 금액 (0 초과 필수)")
    category: Optional[str] = Field(default=None, description="거래 카테고리 (선택)")


# ==========================================
# [3단계] 검증 파이프라인 (valid / errors 분리)
# ==========================================
def validate_sales_pipeline(raw_data: list[dict]) -> tuple[list, list]:
    """
    원본 데이터 리스트를 검증하여 성공(valid)과 에러(errors)로 분리합니다.
    """
    valid_records = []
    error_records = []

    for row in raw_data:
        try:
            validated_record = SalesRecord(**row)
            valid_records.append(validated_record)

        except ValidationError as ve:
            error_records.append({"row": row, "error": str(ve)})

    return valid_records, error_records


# ==========================================
# [4단계] 결과 파일 저장 및 역검증 함수
# ==========================================
def save_validation_results(
    valid_records: list[SalesRecord],
    error_records: list[dict],
    valid_path: str,
    error_path: str,
) -> None:
    """
    검증 결과 데이터를 파일로 안전하게 내보냅니다.
    - Pydantic 객체는 .model_dump()를 사용하여 직렬화가 가능한 일반 dict로 변환합니다.
    """
    # 1. 성공 데이터 직렬화 및 저장
    valid_to_save = [record.model_dump() for record in valid_records]

    with open(valid_path, "w", encoding="utf-8") as f:
        json.dump(valid_to_save, f, indent=4, ensure_ascii=False)
    logger.info(f"성공 데이터 저장 완료: {valid_path}")

    # 2. 에러 데이터 저장 (이미 dict 형태이므로 바로 저장 가능)
    with open(error_path, "w", encoding="utf-8") as f:
        json.dump(error_records, f, indent=4, ensure_ascii=False)
    logger.info(f"에러 데이터 저장 완료: {error_path}")


# ==========================================
# 통합 실행 및 마스터 검증 구역
# ==========================================
if __name__ == "__main__":
    print("=== [파일 I/O 및 Pydantic 검증 파이프라인] ===")

    # 1. 원본 데이터 로드
    file_name = "Python_Practice2_Data.json"
    raw_data = safe_load_csv(file_name)

    if raw_data is not None:
        # 2. 검증 파이프라인 가동 (3단계)
        valid, errors = validate_sales_pipeline(raw_data)

        print(f"■ 성공(Valid) 데이터 개수  : {len(valid)}건")
        print(f"■ 실패(Errors) 데이터 개수 : {len(errors)}건")

        # 3. 결과 파일 물리 저장 (4단계)
        valid_out_path = "valid_records.json"
        error_out_path = "error_records.json"

        save_validation_results(valid, errors, valid_out_path, error_out_path)

        # 4. 저장 결과 역검증 (Double Check)
        print("\n=== [역검증] ===")
        reloaded_valid = safe_load_csv(valid_out_path)
        reloaded_errors = safe_load_csv(error_out_path)

        if reloaded_valid is not None and reloaded_errors is not None:
            # 원본 결과와 파일 저장 후 읽어온 개수가 정확히 일치하는지 교차 검증
            assert len(reloaded_valid) == len(valid), (
                "오류: 저장된 성공 데이터 개수가 다릅니다."
            )
            assert len(reloaded_errors) == len(errors), (
                "오류: 저장된 에러 데이터 개수가 다릅니다."
            )

            print("[역검증 성공] 모든 데이터가 정상적으로 파일에 물리 저장되었으며,")
            print(
                f"검증한 결과 개수({len(reloaded_valid)}건 / {len(reloaded_errors)}건)도 일치합니다!"
            )
