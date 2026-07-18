"""
======================================================================
프로그램명 : [종합실습1] 비동기 날씨 수집, Pydantic 검증 및 CSV/Parquet 저장·읽기, pytest 검사
설명       : open-meteo 및 timeapi.io 비동기 수집 후 Pydantic v2 검증을 거쳐
             CSV와 Parquet 두 형식으로 저장/읽기하고, 서울의 현재 기온이
             25도인지 pytest로 검사합니다.
             - 스크립트로 직접 실행(python test_weather_pipeline.py):
               2~4단계 파이프라인(수집→검증→저장→읽기)이 동작합니다.
             - pytest로 실행(pytest test_weather_pipeline.py):
               test_로 시작하는 함수만 수집되어 5단계 검사가 동작합니다.
작성일자   : 2026-07-15
======================================================================
"""

import asyncio
import os
from typing import Dict, List, Optional, Tuple

import httpx
import pandas as pd
from pydantic import BaseModel, Field, ValidationError, field_validator

# 수집 대상 도시 정보 리스트
CITIES = [
    {"name": "서울", "lat": 37.5665, "lon": 126.9780, "tz": "Asia/Seoul"},
    {"name": "도쿄", "lat": 35.6762, "lon": 139.6503, "tz": "Asia/Tokyo"},
    {"name": "뉴욕", "lat": 40.7128, "lon": -74.0060, "tz": "America/New_York"},
    {"name": "런던", "lat": 51.5074, "lon": -0.1278, "tz": "Europe/London"},
]



# ==========================================
# [1단계] 비동기 데이터 수집
# ==========================================
async def fetch_temperature(client: httpx.AsyncClient, name: str, lat: float, lon: float) -> Optional[float]:
    """
    Open-Meteo API에서 특정 위도/경도의 현재 기온을 가져옵니다.
    """
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    try:
        response = await client.get(url, timeout=10.0)
        response.raise_for_status()
        data = response.json()
        return data.get("current_weather", {}).get("temperature")
    except Exception as e:
        print(f"❌ [{name}] 날씨 수집 실패: {e}")
        return None


async def fetch_current_time(client: httpx.AsyncClient, name: str, tz: str) -> Optional[str]:
    """
    TimeAPI에서 특정 타임존의 현재 시각(dateTime)을 가져옵니다.
    """
    url = f"https://timeapi.io/api/time/current/zone?timeZone={tz}"
    try:
        response = await client.get(url, timeout=10.0)
        response.raise_for_status()
        data = response.json()
        return data.get("dateTime")
    except Exception as e:
        print(f"❌ [{name}] 시간 수집 실패 (TimeAPI 한도 초과 가능성): {e}")
        return None


async def collect_city_data(client: httpx.AsyncClient, city: Dict) -> Dict:
    """
    한 도시에 대해 날씨와 시간 API를 동시에 호출하고 결과를 결합합니다.
    """
    name = city["name"]
    lat, lon, tz = city["lat"], city["lon"], city["tz"]

    temp_task = fetch_temperature(client, name, lat, lon)
    time_task = fetch_current_time(client, name, tz)
    temp, current_time = await asyncio.gather(temp_task, time_task)

    temperature_value = temp if temp is not None else "수집 실패(오류)"
    time_value = current_time if current_time is not None else "시간 수집 실패(한도 초과)"

    if current_time and "T" in current_time:
        try:
            date_part, time_part = current_time.split("T")
            year, month, day = date_part.split("-")
            hour_minute = ":".join(time_part.split(":")[:2])
            time_value = f"{month}/{day}/{year} {hour_minute}"
        except Exception:
            pass

    return {
        "city_name": name,
        "latitude": lat,
        "longitude": lon,
        "timezone": tz,
        "temperature": temperature_value,
        "collected_at": time_value,
    }
# ==========================================
# [2단계] Weather Pydantic v2 스키마 정의
# ==========================================
class WeatherRecord(BaseModel):
    """
    도시별 수집된 날씨 및 시각 데이터를 검증하기 위한 Pydantic 모델 클래스
    """

    city_name: str = Field(description="도시 이름 (필수)")
    temperature: float | str = Field(description="현재 기온 (숫자 혹은 기온 측정 오류 메시지)")
    collected_at: str = Field(description="API 수집된 현지 시각 (필수)")

    @field_validator("temperature")
    @classmethod
    def validate_temperature_range(cls, v: float | str) -> float | str:
        # 기온 범위 제약 조건 검증: -80.0°C ~ 60.0°C 내에 있어야 함
        if isinstance(v, (int, float)) and not (-80.0 <= v <= 60.0):
            raise ValueError("기온이 지구상에서 관측 가능한 정상 범위를 벗어났습니다. (-80°C ~ 60°C)")
        return v
    

# ==========================================
# 데이터 검증 파이프라인 적용
# ==========================================
def validate_weather_data(raw_data: List[Dict]) -> Tuple[List[WeatherRecord], List[Dict]]:
    """
    비동기 수집된 원본 날씨 데이터를 Pydantic 스키마를 사용하여 검증하고 분리합니다.
    """
    valid_records: List[WeatherRecord] = []
    error_records: List[Dict] = []

    for row in raw_data:
        try:
            valid_records.append(WeatherRecord(**row))
        except ValidationError as ve:
            error_records.append({"row": row, "error": str(ve)})

    return valid_records, error_records


# ==========================================
# [3~4단계] CSV & Parquet 저장/읽기 함수
# ==========================================
def save_records_to_csv(df: pd.DataFrame, file_path: str) -> None:
    """DataFrame을 CSV 형식으로 저장합니다."""
    df.to_csv(file_path, index=False, encoding="utf-8-sig")


def save_records_to_parquet(df: pd.DataFrame, file_path: str) -> None:
    """DataFrame을 Parquet 형식으로 저장합니다."""
    df.to_parquet(file_path, index=False, engine="pyarrow", compression="snappy")


def read_records_from_csv(file_path: str) -> Optional[pd.DataFrame]:
    """
    지정한 경로의 CSV 파일을 읽어옵니다.
    - 해당 파일이 없으면 예외 처리를 수행합니다.
    """
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
        return pd.read_csv(file_path, encoding="utf-8-sig")
    except Exception as e:
        print(f"⚠️ [예외 발생] CSV 읽기 실패: {e}")
        return None


def read_records_from_parquet(file_path: str, columns: Optional[List[str]] = None) -> Optional[pd.DataFrame]:
    """
    지정한 경로의 Parquet 파일을 읽어옵니다.
    - columns 인자를 지정할 시, 해당 컬럼만 로드합니다.
    - 해당 파일이 없으면 예외 처리를 수행합니다.
    """
    try:
        absolute_path = os.path.abspath(file_path)
        if not os.path.exists(absolute_path):
            raise FileNotFoundError(f"'{absolute_path}' 경로에 Parquet 파일이 존재하지 않습니다.")
        return pd.read_parquet(absolute_path, columns=columns, engine="auto")
    except FileNotFoundError as e:
        print(f"⚠️ [예외 발생] Parquet 파일을 불러오지 못했습니다:\n   {e}")
        return None
    except Exception as e:
        print(f"❌ [읽기 기타 에러] Parquet 파일을 읽는 도중 오류가 발생했습니다: {e}")
        return None


# ==========================================
# [2~4단계] 파이프라인 실행 함수 (수집→검증→저장→읽기)
# ==========================================
async def run_pipeline() -> None:
    print("=== 1단계: 비동기 날씨 및 시각 데이터 수집 시작 ===")

    async with httpx.AsyncClient() as client:
        tasks = [collect_city_data(client, city) for city in CITIES]
        raw_results = await asyncio.gather(*tasks)

    print("[수집 완료]")

    print("\n=== 2단계: Pydantic v2 스키마 검증 시작 ===")
    valid_records, error_records = validate_weather_data(raw_results)

    print("\n" + "=" * 50)
    print(f"■ 검증 성공(Valid) 데이터 : {len(valid_records)}건")
    print(f"■ 검증 실패(Errors) 데이터: {len(error_records)}건")
    print("=" * 50 + "\n")

    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        base_dir = os.getcwd()

    csv_file_path = os.path.join(base_dir, "weather_data.csv")
    parquet_file_path = os.path.join(base_dir, "weather_data.parquet")

    data_to_save = [
        {"도시": record.city_name, "기온": record.temperature, "현지시각": record.collected_at}
        for record in valid_records
    ]
    df = pd.DataFrame(data_to_save, columns=["도시", "기온", "현지시각"])

    save_records_to_csv(df, csv_file_path)
    save_records_to_parquet(df, parquet_file_path)

    print("=== 3단계: CSV 파일 읽기 결과 ===")
    df_csv = read_records_from_csv(csv_file_path)
    if df_csv is not None:
        print(df_csv.to_string())

    print("\n=== 4단계: Parquet 파일에서 '도시', '기온'만 읽기 결과 ===")
    df_parquet = read_records_from_parquet(parquet_file_path, columns=["도시", "기온"])
    if df_parquet is not None:
        print(df_parquet.to_string())


# ==========================================
# [5단계] pytest로 검사
# ==========================================
CITY_SEOUL = {"name": "서울", "lat": 37.5665, "lon": 126.9780, "tz": "Asia/Seoul"}
EXPECTED_TEMPERATURE = 25.0


def fetch_current_temperature(lat: float, lon: float) -> float:
    """
    Open-Meteo API에서 특정 위도/경도의 현재 기온을 동기 방식으로 가져옵니다.
    """
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    with httpx.Client() as client:
        response = client.get(url, timeout=10.0)
        response.raise_for_status()
        return response.json()["current_weather"]["temperature"]


def test_seoul_temperature_is_25():
    """
    서울의 현재 기온이 25도인지 검사합니다.
    25도가 아니면 실제 조회된 기온 값을 담은 Fail 메시지를 출력합니다.
    """
    temperature = fetch_current_temperature(CITY_SEOUL["lat"], CITY_SEOUL["lon"])

    assert temperature == EXPECTED_TEMPERATURE, (
        f"❌ Fail: {CITY_SEOUL['name']}의 현재 기온은 {temperature}°C 입니다. "
        f"(기대값: {EXPECTED_TEMPERATURE}°C)"
    )


# ==========================================
# 메인 제어 흐름 (스크립트 직접 실행 시에만 동작, pytest는 무시)
# ==========================================
if __name__ == "__main__":
    asyncio.run(run_pipeline())

    print("\n=== 5단계: 서울 현재 기온 검사 (25도 기준) ===")
    temp = fetch_current_temperature(CITY_SEOUL["lat"], CITY_SEOUL["lon"])
    if temp != EXPECTED_TEMPERATURE:
        print(f"❌ Fail: {CITY_SEOUL['name']}의 현재 기온은 {temp}°C 입니다. (기대값: {EXPECTED_TEMPERATURE}°C)")
    else:
        print(f"✅ Pass: {CITY_SEOUL['name']}의 현재 기온이 {EXPECTED_TEMPERATURE}°C와 일치합니다.")