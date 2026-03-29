# DevSearch-AI

Local-first internal company knowledge assistant with:
- authenticated local users
- role-based document access
- audit logging
- admin document upload and tagging
- grounded retrieval over internal documents

## Local Development

Backend:

```bash
cd /Users/nishthapandey/DevSearch-AI
source venv/bin/activate
uvicorn app:app --reload
```

Frontend:

```bash
cd /Users/nishthapandey/DevSearch-AI/devsearch-ui
npm run dev
```

Demo users:
- `alice / employee123`
- `maya / manager123`
- `harper / hr123`
- `frank / finance123`
- `lara / legal123`
- `admin / admin123`

## Docker Compose

Build and run:

```bash
cd /Users/nishthapandey/DevSearch-AI
cp .env.example .env
docker compose up --build
```

Open the UI at `http://localhost:8080`.

Optional Ollama container:

```bash
docker compose --profile llm up --build
```

The stack persists:
- vector data in a Docker volume
- audit logs in a Docker volume
- uploaded admin documents in a Docker volume

Note:
- the Docker backend uses the lightweight local hashing embedder by default for faster builds
- local Python development can still use `sentence-transformers` when installed and cached
