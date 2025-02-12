from fastapi import FastAPI, Request, Query
from fastapi.templating import Jinja2Templates
import pandas as pd
import re
import uvicorn

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# 엑셀 파일 로드
file_path = "마인크래프트 픽셀몬모드 도감.xlsx"
df = pd.read_excel(file_path, sheet_name="픽셀몬 도감")

# ✅ 포켓몬_대표 컬럼 생성 (이름을 공백 기준으로 앞부분만 저장)
if "포켓몬_대표" not in df.columns:
    df["포켓몬_대표"] = df["포켓몬"].astype(str).apply(lambda x: x.split(" ")[0])

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/search")
def api_search_pokemon(query: str):
    """ 검색 API: 같은 도감번호의 대표 폼만 반환 (중복 제거) """
    column_name = "포켓몬"

    # ✅ 개행문자 제거 + 소문자 변환하여 검색 가능하게 처리
    df[column_name] = df[column_name].astype(str).str.replace(r"\n", " ", regex=True).str.strip().str.lower()

    # ✅ 포켓몬_대표 컬럼이 없으면 다시 생성 (공백 기준 앞부분만 저장)
    if "포켓몬_대표" not in df.columns:
        df["포켓몬_대표"] = df[column_name].apply(lambda x: x.split(" ")[0])

    # ✅ 검색어도 공백이 포함된 경우, 첫 번째 단어만 사용
    query_cleaned = query.strip().lower().split(" ")[0]

    # ✅ 같은 도감번호의 모든 폼을 가져옴
    filtered_df = df[
        (df["포켓몬_대표"].str.contains(query_cleaned, na=False, case=False)) |
        (df[column_name].str.contains(query_cleaned, na=False, case=False))
    ]

    # ✅ 도감번호 기준으로 대표 폼만 선택 (가장 먼저 등장하는 폼 유지)
    results = filtered_df.sort_values(by=["도감번호"]).drop_duplicates(subset=["도감번호"])[["도감번호", "포켓몬"]]

    return results.to_dict(orient="records")

@app.get("/search")
def search_pokemon(request: Request, query: str = Query(...)):
    """ 검색 결과 페이지: 같은 도감번호를 가진 포켓몬만 표시 (정확한 검색 적용) """
    column_name = "포켓몬"

    # ✅ 개행문자 제거 + 소문자 변환하여 검색 가능하게 처리
    df[column_name] = df[column_name].astype(str).str.replace(r"\n", " ", regex=True).str.strip().str.lower()

    # ✅ 포켓몬_대표 컬럼이 없으면 다시 생성 (공백 기준 앞부분만 저장)
    if "포켓몬_대표" not in df.columns:
        df["포켓몬_대표"] = df[column_name].apply(lambda x: x.split(" ")[0])

    # ✅ 검색어도 공백이 포함된 경우, 첫 번째 단어만 사용
    query_cleaned = query.strip().lower().split(" ")[0]

    # ✅ 1. 정확한 일치 검색
    exact_match = df[df["포켓몬_대표"] == query_cleaned]

    if not exact_match.empty:
        # ✅ 정확한 일치하는 포켓몬이 있다면, 해당 도감번호의 모든 폼을 검색
        dex_number = exact_match.iloc[0]["도감번호"]
        results = df[df["도감번호"] == dex_number]
    else:
        # ✅ 2. 부분 검색 (contains) 수행
        results = df[df["포켓몬_대표"].str.contains(query_cleaned, na=False, case=False)]

    return templates.TemplateResponse("result.html", {
        "request": request,
        "results": results.to_dict(orient="records")
    })

@app.get("/routes")
def get_routes():
    """ FastAPI에 등록된 모든 라우트 확인 """
    return [{"path": route.path, "name": route.name} for route in app.routes]
