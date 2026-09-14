from fastapi import FastAPI

app = FastAPI(
    title="MeetFlow AI",
    description="AI 기반 스마트 회의·업무 관리 플랫폼",
    version="0.1.0"
)


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