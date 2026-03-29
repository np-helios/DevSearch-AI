import base64
import json
import re
from pathlib import Path

from fastapi import FastAPI, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ingest import run_ingestion
from src.audit import log_event, read_recent_logs
from src.auth import authenticate_user, clear_session, create_session, get_user_from_token
from src.ingestion.parsers import parse_document_bytes
from src.llm.llm import FALLBACK_ANSWER, generate_answer, has_grounded_results
from src.retrieval.search import search

app = FastAPI()
UPLOADS_DIR = Path("data/uploads")
VALID_ROLES = {"employee", "manager", "hr", "finance", "legal", "admin"}


def select_display_sources(results):
    if not results:
        return []

    best_score = results[0]["score"]
    minimum_score = max(0.18, best_score * 0.45)
    strong_sources = [result for result in results if result["score"] >= minimum_score]
    return strong_sources[:3]


def sanitize_filename(filename):
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(filename).name)
    return cleaned or "uploaded_document.txt"


def get_current_user(x_auth_token: str | None):
    return get_user_from_token(x_auth_token)


class LoginRequest(BaseModel):
    username: str
    password: str


class QueryRequest(BaseModel):
    query: str


class UploadRequest(BaseModel):
    filename: str
    content_base64: str
    title: str
    department: str
    classification: str
    allowed_roles: list[str] = Field(default_factory=list)
    summary: str = ""


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {"message": "DevSearch AI is running"}


@app.post("/auth/login")
def login(req: LoginRequest):
    user = authenticate_user(req.username, req.password)
    if not user:
        log_event("login", "failed", username=req.username, details={"reason": "invalid_credentials"})
        return {"status": "error", "error": "Invalid username or password."}

    token = create_session(user)
    log_event("login", "success", username=user["username"], role=user["role"])
    return {"status": "success", "token": token, "user": user}


@app.post("/auth/logout")
def logout(x_auth_token: str | None = Header(default=None)):
    user = get_current_user(x_auth_token)
    if user:
        clear_session(x_auth_token)
        log_event("logout", "success", username=user["username"], role=user["role"])
    return {"status": "success"}


@app.get("/auth/me")
def me(x_auth_token: str | None = Header(default=None)):
    user = get_current_user(x_auth_token)
    if not user:
        return {"status": "error", "error": "Not authenticated."}
    return {"status": "success", "user": user}


@app.post("/chat")
def chat(req: QueryRequest, x_auth_token: str | None = Header(default=None)):
    user = get_current_user(x_auth_token)
    if not user:
        return {
            "status": "error",
            "answer": "",
            "grounded": False,
            "sources": [],
            "error": "Authentication required.",
        }

    try:
        results = search(req.query, user_role=user["role"])
        answer = generate_answer(req.query, results)
        grounded = has_grounded_results(results) and answer != FALLBACK_ANSWER

        sources = []
        if grounded:
            sources = [
                {
                    "document_id": r["document_id"],
                    "title": r["title"],
                    "document_type": r["document_type"],
                    "name": r["name"],
                    "chunk_type": r["chunk_type"],
                    "path": r["path"],
                    "score": round(r["score"], 3),
                    "start_line": r["start_line"],
                    "end_line": r["end_line"],
                    "department": r["department"],
                    "classification": r["classification"],
                }
                for r in select_display_sources(results)
            ]

        status = "success" if grounded else "not_found"
        log_event(
            "query",
            status,
            username=user["username"],
            role=user["role"],
            details={"query": req.query, "sources": len(sources)},
        )

        return {
            "query": req.query,
            "role": user["role"],
            "username": user["username"],
            "status": status,
            "answer": answer,
            "grounded": grounded,
            "sources": sources,
        }

    except Exception as exc:
        log_event(
            "query",
            "error",
            username=user["username"],
            role=user["role"],
            details={"query": req.query, "error": str(exc)},
        )
        return {
            "query": req.query,
            "role": user["role"],
            "status": "error",
            "answer": "",
            "grounded": False,
            "sources": [],
            "error": str(exc),
        }


@app.post("/admin/upload")
def upload_document(req: UploadRequest, x_auth_token: str | None = Header(default=None)):
    user = get_current_user(x_auth_token)
    if not user or user["role"] != "admin":
        log_event("upload", "denied", username=user["username"] if user else None, role=user["role"] if user else None)
        return {"status": "error", "error": "Admin access required."}

    invalid_roles = [role for role in req.allowed_roles if role not in VALID_ROLES]
    if invalid_roles:
        return {"status": "error", "error": f"Invalid allowed roles: {', '.join(invalid_roles)}"}

    try:
        raw_bytes = base64.b64decode(req.content_base64)
        _, document_type = parse_document_bytes(req.filename, raw_bytes)

        UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        safe_name = sanitize_filename(req.filename)
        file_path = UPLOADS_DIR / safe_name
        metadata_path = Path(f"{file_path}.meta.json")

        file_path.write_bytes(raw_bytes)
        metadata_path.write_text(
            json.dumps(
                {
                    "title": req.title,
                    "department": req.department.lower(),
                    "classification": req.classification.lower(),
                    "allowed_roles": [role.lower() for role in req.allowed_roles],
                    "summary": req.summary,
                    "document_type": document_type,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        run_ingestion()
        log_event(
            "upload",
            "success",
            username=user["username"],
            role=user["role"],
            details={"filename": safe_name, "department": req.department, "classification": req.classification},
        )
        return {"status": "success", "message": f"Uploaded and indexed {safe_name}."}
    except Exception as exc:
        log_event(
            "upload",
            "error",
            username=user["username"],
            role=user["role"],
            details={"filename": req.filename, "error": str(exc)},
        )
        return {"status": "error", "error": str(exc)}


@app.get("/admin/audit-logs")
def audit_logs(x_auth_token: str | None = Header(default=None)):
    user = get_current_user(x_auth_token)
    if not user or user["role"] != "admin":
        return {"status": "error", "error": "Admin access required."}

    return {"status": "success", "logs": read_recent_logs()}
