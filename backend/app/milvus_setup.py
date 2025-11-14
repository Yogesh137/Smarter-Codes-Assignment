# backend/app/milvus_setup.py
from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection
import os

def create_milvus_collection(host="localhost", port="19530", collection_name="html_chunks"):
    """
    Creates Milvus collection:
    fields: id (auto), url (VARCHAR), chunk (VARCHAR), embedding (FLOAT_VECTOR dim=384)
    """
    connections.connect(alias="default", host=host, port=port)

    if Collection.exists(collection_name):
        print(f"Collection '{collection_name}' already exists.")
        return Collection(collection_name)

    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="url", dtype=DataType.VARCHAR, max_length=2048),
        FieldSchema(name="chunk", dtype=DataType.VARCHAR, max_length=8192),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=384),
    ]

    schema = CollectionSchema(fields=fields, description="HTML chunks with embeddings")
    collection = Collection(name=collection_name, schema=schema)
    print(f"Created collection '{collection_name}'")

    index_params = {
        "index_type": "HNSW",
        "metric_type": "COSINE",
        "params": {"M": 8, "efConstruction": 64}
    }
    collection.create_index(field_name="embedding", index_params=index_params)
    collection.load()
    print("Index created and collection loaded.")
    return collection

if __name__ == "__main__":
    host = os.getenv("MILVUS_HOST", "localhost")
    port = os.getenv("MILVUS_PORT", "19530")
    create_milvus_collection(host=host, port=port)
