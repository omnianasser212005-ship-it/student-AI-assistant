from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
import traceback
import os
import shutil
import chromadb
import pymupdf

from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.generation import generate_answer

from src.feedback_learning import (
    add_feedback,
    learn_from_feedback
)

from src.retrieval import (
    get_file_chunks,
    get_exam_files,
    get_exam_chunks
)

from src.practice_generator import (
    load_exam_analysis,
    generate_practice_questions
)


# =========================================================
# Paths
# =========================================================

RAW_DATA_PATH = "data/raw"
VECTOR_STORE_PATH = "data/vector_store"
COLLECTION_NAME = "study_materials"

VECTOR_STORE_PATH = "data/vector_store"
COLLECTION_NAME = "study_materials"



chroma_client = chromadb.PersistentClient(
    path=VECTOR_STORE_PATH
)

embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


# =========================================================
# ChromaDB
# =========================================================






# =========================================================
# Embedding Model
# =========================================================

embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


# =========================================================
# FastAPI
# =========================================================

app = FastAPI(
    title="Student AI Assistant",
    description="AI assistant for academic study materials",
    version="1.0.0"
)







# =========================================================
# Paths
# =========================================================



# =========================================================
# Request Models
# =========================================================

class QuestionRequest(BaseModel):

    question: str

    top_k: int = 8

    subject: str | None = None

    document_type: str | None = None


class FeedbackRequest(BaseModel):

    question: str

    answer: str

    rating: int

    feedback: str

    sources: list | None = None


class FileRequest(BaseModel):

    file_name: str

    subject: str | None = None


class PracticeRequest(BaseModel):

    file_name: str

    subject: str

    number_of_questions: int = 10


# =========================================================
# Health
# =========================================================

@app.get("/health")
def health():

    return {
        "status": "ok",
        "message": "Student AI Assistant API is running."
    }
@app.get("/exam-files")
def exam_files():

    try:

        files = get_exam_files()

        return {
            "status": "success",
            "files": files
        }

    except Exception as e:

        print(
            f"Exam files error: {e}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# =========================================================
# Query
# =========================================================

@app.post("/query")
def query(request: QuestionRequest):

    if not request.question.strip():

        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )

    try:

        result = generate_answer(
            question=request.question,
            top_k=request.top_k,
            subject=request.subject,
            document_type=request.document_type
        )

        answer = result.get(
            "answer",
            ""
        )

        # The practical example is generated from
        # the same answer/context by the frontend/backend
        # response structure.
        practical_example = (
            "See the explanation above for an example "
            "based on the provided study materials."
        )

        return {
            "status": "success",
            "answer": answer,
            "practical_example": practical_example,
            "sources": result.get(
                "sources",
                []
            )
        }
    
    except Exception as e:

    

        print("\n==============================")
        print("QUERY ERROR")
        print("==============================")

        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    

 


# =========================================================
# Explain Specific File
# =========================================================

@app.post("/explain-file")
def explain_file(request: FileRequest):

    if not request.file_name.strip():

        raise HTTPException(
            status_code=400,
            detail="File name cannot be empty."
        )

    if not request.subject:

        raise HTTPException(
            status_code=400,
            detail="Subject is required."
        )

    try:

        results = get_file_chunks(
            subject=request.subject,
            file_name=request.file_name
        )

        documents = results.get(
            "documents",
            []
        )

        if not documents:
            raise HTTPException(
                status_code=404,
                detail="File was not found in the study database."
            )

        context = "\n\n".join(
            str(document)
            for document in documents
            if document
        )

        prompt = f"""
You are a university academic study assistant.

Explain the following study file clearly.

Use ONLY the provided file content.

Do not add information from general knowledge.

Organize the explanation into:

1. Main idea
2. Important concepts
3. Important definitions
4. Important examples
5. Key points to remember

Keep the terminology used in the original material.

FILE CONTENT:

{context}
"""

        import ollama

        response = ollama.chat(
            model="llama3.2",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            options={
                "temperature": 0.2,
                "num_predict": 1200
            }
        )

        explanation = response[
            "message"
        ][
            "content"
        ]

        return {
            "status": "success",
            "file_name": request.file_name,
            "subject": request.subject,
            "explanation": explanation
        }

    except HTTPException:

        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# =========================================================
# Summarize Specific File
# =========================================================

@app.post("/summarize-file")
def summarize_file(request: FileRequest):

    if not request.file_name.strip():

        raise HTTPException(
            status_code=400,
            detail="File name cannot be empty."
        )

    if not request.subject:

        raise HTTPException(
            status_code=400,
            detail="Subject is required."
        )

    try:

        results = get_file_chunks(
            subject=request.subject,
            file_name=request.file_name
        )

        documents = results.get(
            "documents",
            []
        )

        if not documents:
            raise HTTPException(
                status_code=404,
                detail="File was not found in the study database."
            )

        context = "\n\n".join(
            str(document)
            for document in documents
            if document
        )

        prompt = f"""
You are a university academic study assistant.

Summarize the following study file.

Use ONLY the provided content.

Do not add information from general knowledge.

Create a useful study summary containing:

- Main topics
- Important concepts
- Definitions
- Important points
- Important examples
- Final review points

Keep the summary concise but complete.

FILE CONTENT:

{context}
"""

        import ollama

        response = ollama.chat(
            model="llama3.2",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            options={
                "temperature": 0.2,
                "num_predict": 1000
            }
        )

        summary = response[
            "message"
        ][
            "content"
        ]

        return {
            "status": "success",
            "file_name": request.file_name,
            "subject": request.subject,
            "summary": summary
        }

    except HTTPException:

        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# =========================================================
# Previous Exams → Practice Questions
# =========================================================

@app.post("/practice-questions")
def practice_questions(request: PracticeRequest):

    if request.number_of_questions < 1:

        raise HTTPException(
            status_code=400,
            detail="Number of questions must be at least 1."
        )

    if request.number_of_questions > 30:

        raise HTTPException(
            status_code=400,
            detail="Maximum number of questions is 30."
        )

    try:

        # ==========================================
        # Get previous exam chunks from ChromaDB
        # ==========================================

        results = get_exam_chunks(
            subject=request.subject,
            file_name=request.file_name
        )

        documents = results.get(
            "documents",
            []
        )

        if not documents:

            return {
                "status": "success",
                "questions": (
                    "No previous exams were found "
                    "for the selected subject."
                )
            }

        # ChromaDB can return nested lists
        if documents and isinstance(
            documents[0],
            list
        ):
            documents = documents[0]

        # ==========================================
        # Generate questions
        # ==========================================

        result = generate_practice_questions(
            exam_documents=documents,
            num_questions=request.number_of_questions,
            subject=request.subject
        )

        return {
            "status": "success",
            "questions": result
        }

    except Exception as e:

        print(
            f"Practice questions error: {e}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# =========================================================
# Feedback
# =========================================================

@app.post("/feedback")
def submit_feedback(request: FeedbackRequest):

    if not request.feedback.strip():

        raise HTTPException(
            status_code=400,
            detail="Feedback cannot be empty."
        )

    if request.rating < 1 or request.rating > 5:

        raise HTTPException(
            status_code=400,
            detail="Rating must be between 1 and 5."
        )

    try:

        add_feedback(
            question=request.question,
            answer=request.answer,
            rating=request.rating,
            feedback=request.feedback,
            sources=request.sources
        )

        learning_result = learn_from_feedback()

        return {
            "status": "success",
            "message": "Feedback saved and learning updated.",
            "learning": learning_result
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# =========================================================
# Upload PDF
# =========================================================


@app.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    subject: str = Form(...)
):

    if not subject.strip():

        raise HTTPException(
            status_code=400,
            detail="Subject cannot be empty."
        )

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="File name is required."
        )

    if not file.filename.lower().endswith(".pdf"):

        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported."
        )

    try:

        # =================================================
        # Save PDF
        # =================================================

        subject_path = os.path.join(
            RAW_DATA_PATH,
            subject
        )

        os.makedirs(
            subject_path,
            exist_ok=True
        )

        file_path = os.path.join(
            subject_path,
            file.filename
        )

        with open(
            file_path,
            "wb"
        ) as buffer:

            shutil.copyfileobj(
                file.file,
                buffer
            )

        # =================================================
        # Extract Text
        # =================================================

        doc = pymupdf.open(
            file_path
        )

        pages = []

        full_text = ""

        for page_number, page in enumerate(
            doc,
            start=1
        ):

            page_text = page.get_text().strip()

            # OCR fallback
            if not page_text:

                try:

                    import pytesseract

                    from PIL import Image

                    pix = page.get_pixmap(
                        matrix=pymupdf.Matrix(2, 2)
                    )

                    image = Image.frombytes(
                        "RGB",
                        [pix.width, pix.height],
                        pix.samples
                    )

                    page_text = pytesseract.image_to_string(
                        image,
                        lang="eng"
                    ).strip()

                except Exception:

                    page_text = ""

            if page_text:

                pages.append(
                    (
                        page_number,
                        page_text
                    )
                )

                full_text += (
                    f"\n\n"
                    f"--- Page {page_number} ---\n"
                    f"{page_text}"
                )

        doc.close()

        if not pages:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Could not extract text from the PDF. "
                    "The PDF may be empty or unsupported."
                )
            )

        # =================================================
        # Document Classification
        # =================================================

        from src.ingestion import classify_document

        document_type = classify_document(
            full_text
        )

        print(
            f"Uploaded document type: {document_type}"
        )

        # =================================================
        # Chunking
        # =================================================

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=700,
            chunk_overlap=100
        )

        documents = []
        metadatas = []
        ids = []

        for page_number, page_text in pages:

            chunks = splitter.split_text(
                page_text
            )

            for chunk_number, chunk in enumerate(
                chunks,
                start=1
            ):

                chunk_id = (
                    f"{subject}_"
                    f"{file.filename}_"
                    f"P{page_number}_"
                    f"C{chunk_number}"
                )

                documents.append(
                    chunk
                )

                ids.append(
                    chunk_id
                )

                metadatas.append({

                    "subject": subject,

                    "file_name": file.filename,

                    "page": page_number,

                    "chunk_id": chunk_id,

                    "document_type": document_type
                })

        if not documents:

            raise HTTPException(
                status_code=400,
                detail="No usable text chunks were created."
            )


  
        # =================================================
        # Embeddings + ChromaDB
        # =================================================

        print(
            f"Generating embeddings for "
            f"{len(documents)} chunks..."
        )

        embeddings = embedding_model.encode(
            documents,
            show_progress_bar=False
        )


        # =================================================
        # Remove old version of same file
        # =================================================
        upload_collection = chroma_client.get_or_create_collection(
            name=COLLECTION_NAME
        )

        try:

            old_chunks = upload_collection.get(
                where={
                    "$and": [
                        {
                            "subject": subject
                        },
                        {
                            "file_name": file.filename
                        }
                    ]
                }
            )

            old_ids = old_chunks.get(
                "ids",
                []
            )

            if old_ids:

                upload_collection.delete(
                    ids=old_ids
                )

                print(
                    f"Removed {len(old_ids)} old chunks."
                )

        except Exception as e:

            print(
                f"Could not remove old chunks: {e}"
            )


        # =================================================
        # Store in ChromaDB
        # =================================================

        upload_collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings.tolist(),
            metadatas=metadatas
        )

        print(
            f"Added {len(documents)} chunks to ChromaDB."
        )


        

           




        # =================================================
        # Response
        # =================================================

        return {

            "status": "success",

            "message": (
                "PDF uploaded, classified, "
                "embedded and indexed successfully."
            ),

            "file": {

                "file_name": file.filename,

                "subject": subject,

                "document_type": document_type,

                "pages": len(pages),

                "chunks": len(documents)
            }
        }

    except HTTPException:

        raise

    except Exception as e:

        print(
            f"Upload error: {e}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

