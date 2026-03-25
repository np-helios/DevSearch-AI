import ast

def chunk_python_file(file_content):
    chunks = []

    try:
        tree = ast.parse(file_content)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                chunks.append({
                    "type": "function",
                    "name": node.name,
                    "code": ast.get_source_segment(file_content, node)
                })

            elif isinstance(node, ast.ClassDef):
                chunks.append({
                    "type": "class",
                    "name": node.name,
                    "code": ast.get_source_segment(file_content, node)
                })

    except Exception:
        chunks.append({
            "type": "raw",
            "name": "unknown",
            "code": file_content[:1000]
        })

    return chunks
