from fastapi import FastAPI
from src.retrieval.search import search
from src.llm.llm import generate_answer
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "🚀 DevSearch AI is running"}


@app.get("/ask")
def ask(query: str, role: str = "employee"):
    try:
        results = search(query, user_role=role)
        answer = generate_answer(query, results)

        return {
            "query": query,
            "role": role,
            "answer": answer
        }

    except Exception as e:
        return {"error": str(e)}