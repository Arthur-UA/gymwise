import os
from typing import List, Optional, Dict
from typing_extensions import TypedDict

from dotenv import load_dotenv
from langchain import hub
from langgraph.graph import START, StateGraph
from langchain_ollama.llms import OllamaLLM
from langchain_core.documents import Document

from pinecone_client.client import VectorDBClient

load_dotenv(override=True)

PROMPT = hub.pull("rlm/rag-prompt")

class State(TypedDict):
    question: str
    context: List[Document]
    answer: str
    filters: Optional[Dict[str, List[str]]]

class RAGPipeline:
    """Initializes the RAG pipeline, supports running the full pipeline with retrieval and LLM call"""

    def __init__(self, llm: str, vector_db_index: str, namespace: str):
        self.llm_model = OllamaLLM(model=llm)
        self.vector_db = VectorDBClient(index_name=vector_db_index, namespace=namespace)

        graph_builder = StateGraph(State).add_sequence([self._retrieve, self._generate])
        graph_builder.add_edge(START, "_retrieve")

        self.graph = graph_builder.compile()

    async def _retrieve(self, state: State):
        raw = await self.vector_db.query_dense_index(
            query=state["question"],
            filters=state.get("filters")
        )

        hits = raw.get("result", {}).get("hits", [])

        docs = [
            Document(
                id=rec.get("_id"),
                page_content=rec.get("fields", {}).get("chunk_text", ""),
                metadata={
                    "equipment": rec.get("fields", {}).get("equipment"),
                    "muscleGroup": rec.get("fields", {}).get("muscleGroup"),
                    "imageUrl": rec.get("fields", {}).get("imageUrl")
                }
            )
            for rec in hits
        ]
        return {"context": docs}

    async def _generate(self, state: State):
        docs_content = "\n\n".join(d.page_content for d in state["context"])
        messages = await PROMPT.ainvoke({"question": state["question"], "context": docs_content})

        answer = await self.llm_model.ainvoke(messages)
        return {"answer": answer}
    
    async def run_graph(self, query: str, filters: Optional[Dict[str, List[str]]]):
        """Runs the full LangChain Graph which triggers retrieval, and LLM answer generation

        Args:
            query (str): A question from a user,
            filters (Optional[Dict[str, List[str]]]): Equipment and muscle group filtering
        """

        return await self.graph.ainvoke({
            "question": query,
            "filters": filters if filters else {}
        })



if __name__ == "__main__":
    model = OllamaLLM(model=os.environ["OLLAMA_MODEL"])
    print(model.invoke("Hello, tell me something cool)"))
