import os

SUPPORTED_EXTENSIONS = [".py", ".js", ".ts", ".java", ".cpp"]

#  Default data folder
DEFAULT_DATA_PATH = "data"


def load_codebase(repo_path=DEFAULT_DATA_PATH):
    code_files = []

    #  If folder doesn't exist → clear error
    if not os.path.exists(repo_path):
        print(f" Folder not found: {repo_path}")
        return code_files

    print(f" Loading files from: {repo_path}")

    for root, _, files in os.walk(repo_path):
        for file in files:
            if any(file.endswith(ext) for ext in SUPPORTED_EXTENSIONS):
                full_path = os.path.join(root, file)

                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                        if content.strip():  #  avoid empty files
                            code_files.append({
                                "path": full_path,
                                "content": content
                            })

                except Exception as e:
                    print(f" Error reading {full_path}: {e}")

    print(f" Total files loaded: {len(code_files)}")

    return code_files
