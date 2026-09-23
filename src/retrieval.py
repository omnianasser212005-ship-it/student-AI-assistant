import chromadb
from sentence_transformers import SentenceTransformer


VECTOR_STORE_PATH = "data/vector_store"
COLLECTION_NAME = "study_materials"


model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


client = chromadb.PersistentClient(
    path=VECTOR_STORE_PATH
)


collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"}
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


def get_file_chunks(
    subject,
    file_name
):

    results = collection.get(
        where={
            "$and": [
                {
                    "subject": subject
                },
                {
                    "file_name": file_name
                }
            ]
        },
        include=[
            "documents",
            "metadatas"
        ]
    )

    return results


def get_exam_files():

    results = collection.get(
        where={
            "document_type": "exam"
        },
        include=[
            "metadatas"
        ]
    )

    metadatas = results.get(
        "metadatas",
        []
    )

    exam_files = []

    for metadata in metadatas:

        if not metadata:
            continue

        item = {
            "subject": metadata.get(
                "subject",
                "Unknown"
            ),
            "file_name": metadata.get(
                "file_name",
                "Unknown"
            )
        }

        if item not in exam_files:

            exam_files.append(item)

    return sorted(
        exam_files,
        key=lambda x: (
            x["subject"],
            x["file_name"]
        )
    )
def get_exam_chunks(
    subject,
    file_name
):

    results = collection.get(
        where={
            "$and": [
                {
                    "subject": subject
                },
                {
                    "file_name": file_name
                },
                {
                    "document_type": "exam"
                }
            ]
        },
        include=[
            "documents",
            "metadatas"
        ]
    )

    return results