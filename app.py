from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
from typing import List, Dict
import os
import json
import psycopg2
import urllib.parse as urlparse
from dotenv import load_dotenv

# ✅ 환경 변수 로드
load_dotenv("")

# ✅ PostgreSQL 설정
db_url = os.getenv("DATABASE_URL")
parsed_url = urlparse.urlparse(db_url)

PG_DB = parsed_url.path[1:]
PG_USER = parsed_url.username
PG_PASSWORD = parsed_url.password
PG_HOST = parsed_url.hostname
PG_PORT = parsed_url.port

# ✅ FastAPI 앱 생성
app = FastAPI()

# ✅ Pydantic 모델 정의
class Recommendation(BaseModel):
    name: str
    description: str

class AnswerData(BaseModel):
    question: str
    answer: List[Recommendation]
    keywords: List[str]

def get_db_connection():
    return psycopg2.connect(
        dbname=PG_DB,
        user=PG_USER,
        password=PG_PASSWORD,
        host=PG_HOST,
        port=PG_PORT
    )

# ✅ 테이블 초기화용 엔드포인트 (선택적으로 사용)
@app.post("/init-db")
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DROP TABLE IF EXISTS graphrag_answers;")
        cursor.execute("""
            CREATE TABLE graphrag_answers (
                id SERIAL PRIMARY KEY,
                question TEXT,
                recommendations JSONB,
                keywords TEXT[]
            );
        """)
        conn.commit()
    finally:
        cursor.close()
        conn.close()
    return {"message": "✅ 테이블 초기화 완료"}

# ✅ 본 데이터 저장용 엔드포인트
@app.post("/load-data")
def load_data(data: List[AnswerData] = Body(...)):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        for item in data:
            question = item.question
            recommendations = [r.dict() for r in item.answer]
            keywords = item.keywords

            cursor.execute(
                "INSERT INTO graphrag_answers (question, recommendations, keywords) VALUES (%s, %s, %s);",
                (question, json.dumps(recommendations), keywords)
            )
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"DB 저장 실패: {str(e)}")
    finally:
        cursor.close()
        conn.close()

    return {"message": "✅ 데이터 저장 완료"}
