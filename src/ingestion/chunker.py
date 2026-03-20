import ast


def chunk_python_file(file_content):
    chunks = []

    try:
        tree = ast.parse(file_content)

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                chunk = ast.get_source_segment(file_content, node)
                if chunk:
                    chunks.append(chunk)

        # 🔥 fallback if no chunks found
        if not chunks:
            chunks.append(file_content)

    except Exception as e:
        print(f"AST parsing failed: {e}")
        chunks.append(file_content)

    return chunks
