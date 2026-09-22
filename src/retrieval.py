import chromadb
from sentence_transformers import SentenceTransformer


VECTOR_STORE_PATH = "data/vector_store"
COLLECTION_NAME = "study_materials"


# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")


# Connect to ChromaDB
client = chromadb.PersistentClient(
    path=VECTOR_STORE_PATH
)

collection = client.get_collection(
    name=COLLECTION_NAME
)


def search(
    query,
    top_k=5,
    subject=None,
    document_type=None
):

    query_embedding = model.encode(
        [query]
    ).tolist()

    filters = []

    if subject:
        filters.append({
            "subject": subject
        })

    if document_type:
        filters.append({
            "document_type": document_type
        })

    where_filter = None

    if len(filters) == 1:

        where_filter = filters[0]

    elif len(filters) > 1:

        where_filter = {
            "$and": filters
        }

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k,
        where=where_filter
    )

    return results
def get_file_chunks(subject, file_name):

    results = collection.get(
        where={
            "$and": [
                {"subject": subject},
                {"file_name": file_name}
            ]
        },
        include=[
            "documents",
            "metadatas"
        ]
    )

    return results