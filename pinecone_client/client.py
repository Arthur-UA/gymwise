import os
import json
import logging
from itertools import batched
from pathlib import Path
from typing import List, Dict, Optional

from dotenv import load_dotenv
from pinecone import Pinecone

load_dotenv(override=True)

class VectorDBClient:
    """Initializes the Pinecone vector DB, supports vector loading with additional metadata"""

    def __init__(self, index_name: str, namespace: str):
        self.db = Pinecone(api_key=os.environ['PINECONE_KEY'])
        self.index_name = index_name
        self.namespace = namespace

        if not self.db.has_index(index_name):
            self.db.create_index_for_model(
                name=index_name,
                cloud="aws",
                region="us-east-1",
                embed={
                    "model": "llama-text-embed-v2",
                    "field_map": {"text": "chunk_text"}
                }
            )
        self.index_host = self.db.describe_index(self.index_name)['host']
        self.index = self.db.Index(host=self.index_host)
        self.aindex: Optional[object] = None
    
    def upload_vectors(self, text_metadata_batched: List[List[Dict[str, str]]]) -> None:
        """Uploads vectors to a Pinecone DB
        
        Args:
            namespace (str): Specific namespace,
            text_metadata_batched (List[List[Dict[str, str]]]): Metadata to be loaded
        """
        try:
            for batch in text_metadata_batched:
                self.index.upsert_records(
                    self.namespace, batch
                )
        except Exception as _e:
            logging.error(f'An error occured during uploading:\n{_e}')
    
    async def query_dense_index(self, query: str, filters: Dict[str, List[str]]):
        """Makes a similarity search through the excersices in Pinecone DB
        Args:
            query (str): Question from a user,
            filters (Dict[str, List[str]]): Equipment and muscle group filtering
        """
        if not self.aindex:
            self.aindex = self.db.IndexAsyncio(host=self.index_host)
        
        # Build filter object conditionally
        pinecone_filter = {}
        if filters:
            if filters.get("equipment"):
                pinecone_filter["equipment"] = {"$in": filters["equipment"]}
            if filters.get("muscleGroup"):
                pinecone_filter["muscleGroup"] = {"$in": filters["muscleGroup"]}

        return await self.aindex.search_records(
            namespace=self.namespace,
            query={
                "inputs": {"text": query}, 
                "top_k": 4,
                # Only include the filter if we actually have any constrainSearchRecordsResponse
                **({"filter": pinecone_filter} if pinecone_filter else {})
            },
            fields=["equipment", "muscleGroup", "chunk_text", "imageUrl"]
        )

    @staticmethod
    def _load_text_metadata(filepath: str) -> List[List[Dict[str, str]]]:
        """Loads the scraper metadata in a convinient way for a Pinecone DB
        
        Args:
            filepath (str): Path to a scraper output
        
        Returns:
            List[List[Dict[str, str]]]: A list of batches (96 each) of excercise metadata
        """

        excercise_metadata_path = Path(os.path.dirname(__file__)) / '..' / filepath

        with open(excercise_metadata_path, 'r') as file:
            excercise_metadata = [
                {
                    "_id": 'exs_' + str(i),
                    "chunk_text": f"Here's the guide how to do {excercise['exerciseName']} to hit your {excercise['muscleGroup']}\n" + excercise["description"],
                    **{k: v for k, v in excercise.items() if k != "description" and not k.startswith("#")}
                }
                for i, excercise in enumerate(json.load(file))
            ]

        return list(batched(excercise_metadata, 96))


if __name__ == '__main__':
    vector_db = VectorDBClient('gym-excercises')
    vector_db.upload_vectors(
        text_metadata_batched=vector_db._load_text_metadata('scraper_client/scraper_output.json')
    )
