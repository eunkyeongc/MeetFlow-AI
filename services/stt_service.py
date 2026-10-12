"""음성 → 텍스트 변환 (Gemini 오디오 입력 사용)"""
import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import HTTPException, UploadFile
from google import genai

load_dotenv()

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads/audio"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXT = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".webm", ".aac"}
MAX_SIZE_MB = int(os.getenv("MAX_AUDIO_MB", "100"))
STT_MODEL = os.getenv("GEMINI_STT_MODEL", "gemini-2.5-flash")

_client = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise HTTPException(500, "GEMINI_API_KEY가 설정되지 않았습니다.")
        _client = genai.Client(api_key=api_key)
    return _client


def save_audio_file(file: UploadFile) -> str:
    """업로드된 오디오를 디스크에 저장하고 경로를 반환."""
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(400, f"지원하지 않는 형식입니다. 허용: {', '.join(sorted(ALLOWED_EXT))}")

    path = UPLOAD_DIR / f"{uuid.uuid4().hex}{ext}"
    size = 0
    with open(path, "wb") as f:
        while chunk := file.file.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_SIZE_MB * 1024 * 1024:
                f.close()
                path.unlink(missing_ok=True)
                raise HTTPException(413, f"파일이 너무 큽니다 (최대 {MAX_SIZE_MB}MB).")
            f.write(chunk)
    return str(path)


def transcribe_audio(audio_path: str, language: str = "한국어") -> str:
    """오디오 파일을 텍스트로 변환."""
    if not os.path.exists(audio_path):
        raise HTTPException(404, "오디오 파일을 찾을 수 없습니다.")

    client = _get_client()
    uploaded = None
    try:
        uploaded = client.files.upload(file=audio_path)
        prompt = (
            f"이 회의 녹음을 {language}로 정확하게 받아 적어 주세요. "
            "화자가 구분되면 '화자1:', '화자2:' 형식으로 표시하고, "
            "요약이나 설명 없이 전사 텍스트만 출력하세요."
        )
        response = client.models.generate_content(model=STT_MODEL, contents=[prompt, uploaded])
        text = (response.text or "").strip()
        if not text:
            raise HTTPException(422, "음성에서 텍스트를 추출하지 못했습니다.")
        return text
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(502, f"STT 처리 중 오류가 발생했습니다: {e}")
    finally:
        if uploaded is not None:
            try:
                client.files.delete(name=uploaded.name)
            except Exception:
                pass


def delete_audio_file(audio_path: str | None) -> None:
    if audio_path:
        Path(audio_path).unlink(missing_ok=True)