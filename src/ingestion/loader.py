import os

SUPPORTED_EXTENSIONS = [".py", ".js", ".ts", ".java", ".cpp"]


def load_codebase(repo_path):
    code_files = []

    for root, _, files in os.walk(repo_path):
        for file in files:
            if any(file.endswith(ext) for ext in SUPPORTED_EXTENSIONS):
                full_path = os.path.join(root, file)
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        code_files.append({
                            "path": full_path,
                            "content": content
                        })
                except Exception as e:
                    print(f"Error reading {full_path}: {e}")

    return code_files
