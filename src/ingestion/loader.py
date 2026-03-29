import json
import os
from pathlib import Path

from src.ingestion.parsers import SUPPORTED_EXTENSIONS, parse_document_file

DEFAULT_DATA_PATH = "data"
DEFAULT_ALLOWED_ROLES = ["employee", "manager", "hr", "finance", "legal", "admin"]
SIDECAR_SUFFIX = ".meta.json"


def _infer_department(path_obj):
    parts = [part.lower() for part in path_obj.parts]
    for candidate in ("hr", "finance", "legal", "engineering", "operations", "sales", "uploads"):
        if candidate in parts:
            return candidate if candidate != "uploads" else "general"
    return "general"


def _infer_allowed_roles(department):
    department_role_map = {
        "hr": ["hr", "manager", "admin"],
        "finance": ["finance", "manager", "admin"],
        "legal": ["legal", "manager", "admin"],
        "engineering": ["employee", "manager", "admin"],
        "operations": ["employee", "manager", "admin"],
        "sales": ["employee", "manager", "admin"],
        "general": DEFAULT_ALLOWED_ROLES,
    }
    return department_role_map.get(department, DEFAULT_ALLOWED_ROLES)


def _infer_classification(allowed_roles):
    if allowed_roles == ["admin"]:
        return "confidential"
    if any(role in allowed_roles for role in ("hr", "finance", "legal")) and "employee" not in allowed_roles:
        return "restricted"
    if "employee" in allowed_roles:
        return "internal"
    return "restricted"


def _load_sidecar_metadata(path_obj):
    sidecar_path = Path(f"{path_obj}{SIDECAR_SUFFIX}")
    if not sidecar_path.exists():
        return {}

    try:
        with sidecar_path.open("r", encoding="utf-8") as sidecar_file:
            data = json.load(sidecar_file)
            return data if isinstance(data, dict) else {}
    except Exception as exc:
        print(f"Error reading metadata for {path_obj}: {exc}")
        return {}


def _normalize_allowed_roles(raw_roles, department):
    if not raw_roles:
        return _infer_allowed_roles(department)

    if isinstance(raw_roles, str):
        raw_roles = [raw_roles]

    normalized = [str(role).strip().lower() for role in raw_roles if str(role).strip()]
    return normalized or _infer_allowed_roles(department)


def _build_document_record(full_path, content, document_type):
    path_obj = Path(full_path)
    sidecar = _load_sidecar_metadata(path_obj)
    department = str(sidecar.get("department") or _infer_department(path_obj)).lower()
    allowed_roles = _normalize_allowed_roles(sidecar.get("allowed_roles"), department)
    classification = str(sidecar.get("classification") or _infer_classification(allowed_roles)).lower()

    return {
        "document_id": sidecar.get("document_id") or path_obj.stem,
        "title": sidecar.get("title") or path_obj.stem.replace("_", " ").replace("-", " ").title(),
        "document_type": sidecar.get("document_type") or document_type,
        "department": department,
        "classification": classification,
        "allowed_roles": allowed_roles,
        "path": full_path,
        "content": content,
        "summary": sidecar.get("summary", ""),
    }


def load_documents(repo_path=DEFAULT_DATA_PATH):
    documents = []

    if not os.path.exists(repo_path):
        print(f"Folder not found: {repo_path}")
        return documents

    print(f"Loading files from: {repo_path}")

    for root, _, files in os.walk(repo_path):
        for file_name in files:
            if file_name.endswith(SIDECAR_SUFFIX):
                continue

            if not any(file_name.endswith(ext) for ext in SUPPORTED_EXTENSIONS):
                continue

            full_path = os.path.join(root, file_name)

            try:
                content, document_type = parse_document_file(full_path)
                if not content.strip():
                    continue

                documents.append(_build_document_record(full_path, content, document_type))
            except Exception as exc:
                print(f"Error reading {full_path}: {exc}")

    print(f"Total files loaded: {len(documents)}")
    return documents


def load_codebase(repo_path=DEFAULT_DATA_PATH):
    return load_documents(repo_path)
