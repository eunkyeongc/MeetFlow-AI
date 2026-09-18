from fastapi import FastAPI
from sqlalchemy import text

import models
from database import Base, engine
from routers import users, auth, projects

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MeetFlow AI",
    description="AI 기반 스마트 회의·업무 관리 플랫폼",
    version="0.1.0"
)

app.include_router(users.router)
app.include_router(auth.router)
app.include_router(projects.router)

@app.get("/")
def root():
    return {
        "message": "MeetFlow AI 서버가 정상적으로 실행되었습니다."
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok"
    }


@app.get("/db-test")
def db_test():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT current_database();"))
        database_name = result.scalar()

    return {
        "database": database_name,
        "status": "connected"
    }