# backend/app/create_collection.py
from milvus_setup import create_milvus_collection
import os

if __name__ == "__main__":
    host = os.getenv("MILVUS_HOST", "localhost")
    port = os.getenv("MILVUS_PORT", "19530")
    create_milvus_collection(host=host, port=port)
