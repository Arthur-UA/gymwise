"""
FastAPI application exposing endpoints for querying a RAG (Retrieval-Augmented Generation) pipeline.

This service initializes a RAGPipeline instance using environment variables for model configuration
and vector database access. It provides:
    - GET "/" : Returns information about the loaded LLM model and vector database.
    - POST "/ask_excercise_question" : Accepts a question with optional filters, queries the RAG pipeline,
      and returns the retrieved context along with the generated answer.

Environment variables:
    OLLAMA_MODEL   -- Name or identifier of the LLM model to use.
    PC_INDEX_NAME  -- Name of the vector database index.
    PC_NAMESPACE   -- Namespace within the vector database.

Dependencies:
    - rag_api.client.RAGPipeline : Handles the RAG execution logic.
    - FastAPI, Pydantic, Uvicorn
"""

import os
from typing import List, Dict
from pydantic import BaseModel

import uvicorn
from fastapi import FastAPI

from rag_api.client import RAGPipeline

app = FastAPI()
rag_pipe = RAGPipeline(
    llm=os.environ["OLLAMA_MODEL"],
    vector_db_index=os.environ["PC_INDEX_NAME"],
    namespace=os.environ["PC_NAMESPACE"]
)

class Query(BaseModel):
    question_text: str
    filters: Dict[str, List[str]]


@app.get("/")
async def read_root():
    model_name = os.environ["OLLAMA_MODEL"]
    return f"Model {type(rag_pipe.llm_model).__name__}:{model_name} with {type(rag_pipe.vector_db).__name__} loaded successfully!"

@app.post("/ask_excercise_question")
async def ask_excercise_question(query: Query):
    result = await rag_pipe.run_graph(query=query.question_text, filters=query.filters)
    return {
        "response": {
            "context": result["context"],
            "answer": result["answer"]
        }
    }


if __name__ == "__main__":
    uvicorn.run(app, host='0.0.0.0', port=8000)
