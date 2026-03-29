import ast

CHUNK_SIZE = 900
CHUNK_OVERLAP = 150


def _base_chunk(document, chunk_type, name, content, chunk_index, start_line=None, end_line=None):
    return {
        "document_id": document["document_id"],
        "title": document["title"],
        "document_type": document["document_type"],
        "department": document["department"],
        "classification": document["classification"],
        "allowed_roles": document["allowed_roles"],
        "path": document["path"],
        "summary": document.get("summary", ""),
        "chunk_type": chunk_type,
        "name": name,
        "content": content,
        "chunk_index": chunk_index,
        "start_line": start_line,
        "end_line": end_line,
    }


def _chunk_python_document(document):
    chunks = []
    file_content = document["content"]

    try:
        tree = ast.parse(file_content)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                source = ast.get_source_segment(file_content, node)
                if source:
                    chunks.append(
                        _base_chunk(
                            document,
                            "function",
                            node.name,
                            source,
                            len(chunks),
                            getattr(node, "lineno", None),
                            getattr(node, "end_lineno", None),
                        )
                    )
            elif isinstance(node, ast.ClassDef):
                source = ast.get_source_segment(file_content, node)
                if source:
                    chunks.append(
                        _base_chunk(
                            document,
                            "class",
                            node.name,
                            source,
                            len(chunks),
                            getattr(node, "lineno", None),
                            getattr(node, "end_lineno", None),
                        )
                    )
    except Exception:
        return []

    return chunks


def _chunk_text_document(document):
    text = document["content"].strip()
    chunks = []
    start = 0

    while start < len(text):
        end = min(len(text), start + CHUNK_SIZE)
        chunk_text = text[start:end].strip()
        if chunk_text:
            chunks.append(
                _base_chunk(
                    document,
                    "document_section",
                    document["title"],
                    chunk_text,
                    len(chunks),
                )
            )

        if end >= len(text):
            break

        start = max(0, end - CHUNK_OVERLAP)

    return chunks


def chunk_document(document):
    if document["document_type"] == "py":
        python_chunks = _chunk_python_document(document)
        if python_chunks:
            return python_chunks

    return _chunk_text_document(document)


def chunk_python_file(file_content, file_path="unknown"):
    document = {
        "document_id": file_path,
        "title": file_path,
        "document_type": "py",
        "department": "engineering",
        "classification": "internal",
        "allowed_roles": ["employee", "manager", "admin"],
        "path": file_path,
        "content": file_content,
        "summary": "",
    }
    return chunk_document(document)
