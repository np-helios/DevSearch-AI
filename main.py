from src.ingestion.loader import load_codebase
from src.ingestion.chunker import chunk_python_file

if __name__ == "__main__":
    repo_path = "./"  # your project itself

    files = load_codebase(repo_path)

    print(f"Loaded {len(files)} files")

    for file in files:
        if file["path"].endswith(".py"):
            chunks = chunk_python_file(file["content"])
            print(f"\nFile: {file['path']}")
            print(f"Chunks: {len(chunks)}")

            for chunk in chunks[:2]:  # preview
                print("-" * 40)
                print(chunk[:200])
