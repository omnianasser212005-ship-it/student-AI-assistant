import os
import pymupdf
import chromadb
import ollama

from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
import pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


RAW_DATA_PATH = "data/raw"
VECTOR_STORE_PATH = "data/vector_store"
COLLECTION_NAME = "study_materials"


# =========================
# Embedding Model
# =========================

print("Loading embedding model...")

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

print("Embedding model loaded.")


# =========================
# ChromaDB
# =========================

client = chromadb.PersistentClient(
    path=VECTOR_STORE_PATH
)

try:
    client.delete_collection(
        name=COLLECTION_NAME
    )

    print("Old collection deleted.")

except Exception:
    pass


collection = client.get_or_create_collection(
    name=COLLECTION_NAME
)


# =========================
# Chunking
# =========================

splitter = RecursiveCharacterTextSplitter(
    chunk_size=700,
    chunk_overlap=100
)


# =========================
# Storage
# =========================

all_documents = []
all_metadatas = []
all_ids = []


# =========================
# Document Classifier
# =========================
def ocr_page(page):

    pix = page.get_pixmap(
        matrix=pymupdf.Matrix(2, 2)
    )

    image = Image.frombytes(
        "RGB",
        [pix.width, pix.height],
        pix.samples
    )

    text = pytesseract.image_to_string(
        image,
        lang="eng"
    )

    return text.strip()



def classify_document(text):

    text_upper = text.upper()

    # =========================
    # Strong EXAM indicators
    # =========================

    exam_indicators = [
        "PROBLEM 1",
        "PROBLEM 2",
        "QUESTION 1",
        "QUESTION 2",
        "EXAM",
        "MIDTERM",
        "FINAL EXAM",
        "QUIZ",
        "POINTS)",
        "POINT)",
        "?)",
        "TRUE / FALSE",
        "TRUE OR FALSE",
        "MULTIPLE CHOICE",
        "CHOOSE THE CORRECT",
        "SELECT THE CORRECT",
        "ANSWER:",
        "THE FINAL ANSWER",
        "MARKS)",
        "MARK)"
    ]

    indicator_count = sum(
        1
        for indicator in exam_indicators
        if indicator in text_upper
    )


    # =========================
    # Strong exam decision
    # =========================

    strong_exam_patterns = [
        "PROBLEM 1",
        "PROBLEM 2",
        "QUESTION 1",
        "QUESTION 2",
        "Q1.",
        "Q2.",
        "FINAL EXAM",
        "MIDTERM EXAM",
        "EXAM PAPER",
        "EXAMINATION",
    ]

    strong_count = sum(
        1
        for pattern in strong_exam_patterns
        if pattern in text_upper
    )

    if strong_count >= 2:
        return "exam"


    # =========================
    # LLM classification
    # =========================

    sample = text[:12000]

    prompt = f"""
You are classifying a university academic document.

Choose exactly ONE category:

EXAM
LECTURE

EXAM:
The document is primarily an exam, quiz, midterm, final,
question paper, or an exam answer/solution document.

Examples:
- Problem 1, Problem 2, Problem 3
- Question 1, Question 2, Question 3
- Multiple choice questions
- True/False questions
- Questions with points or marks
- Questions followed by answers or solutions
- Exam answer keys or worked solutions

LECTURE:
The document is primarily teaching/course material.

Examples:
- Definitions
- Concepts
- Theories
- Explanations
- Course notes
- Examples
- Algorithms
- Educational material

IMPORTANT:

A lecture may contain words such as:
"question", "answer", "problem", "example",
"true/false", or "exercise".

These words alone are NOT enough to classify the document as EXAM.

Do NOT classify a document as EXAM just because it discusses
questions or gives examples of questions.

Classify as EXAM only when the document is primarily:
1. A collection of questions intended for students to answer, OR
2. An exam/quiz/midterm/final answer key or solution document.

Classify as LECTURE when the document mainly explains
academic concepts, even if it contains examples or questions.

Do NOT use:
- file name
- folder name
- subject name

Use ONLY the actual document content.

Return EXACTLY one word:

EXAM

or

LECTURE


DOCUMENT CONTENT:

{sample}
"""

    response = ollama.chat(
        model="llama3.2",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        options={
            "temperature": 0
        }
    )

    result = (
        response["message"]["content"]
        .strip()
        .upper()
    )

    print(
        f"    Classifier response: {result}"
    )

    if result == "EXAM":
        return "exam"

    return "lecture"


# =========================
# Read Subjects
# =========================

for subject in os.listdir(
    RAW_DATA_PATH
):

    subject_path = os.path.join(
        RAW_DATA_PATH,
        subject
    )

    if not os.path.isdir(
        subject_path
    ):
        continue

    print(
        f"\nSubject: {subject}"
    )


    # =========================
    # Read PDFs
    # =========================

    for file_name in os.listdir(
        subject_path
    ):

        if not file_name.lower().endswith(
            ".pdf"
        ):
            continue


        pdf_path = os.path.join(
            subject_path,
            file_name
        )

        print(
            f"  File: {file_name}"
        )


        # =========================
        # Open PDF
        # =========================

        doc = pymupdf.open(
            pdf_path
        )


        # =========================
        # Extract ALL file text
        # =========================

        full_file_text = ""

        pages_text = []


        for page_number, page in enumerate(
            doc,
            start=1
        ):

            page_text = (
                page.get_text()
                .strip()
            )

            # OCR fallback for scanned/image pages
            if not page_text:

                print(
                    f"    Page {page_number}: "
                    f"No text found, running OCR..."
                )

                page_text = ocr_page(page)

            pages_text.append(
                (
                    page_number,
                    page_text
                )
            )

            if page_text:

                full_file_text += (
                    f"\n\n"
                    f"--- Page {page_number} ---\n"
                    f"{page_text}"
                )


        # =========================
        # Classify WHOLE PDF
        # =========================

        print(
            "    Classifying document..."
        )

        document_type = classify_document(
            full_file_text
        )

        print(
            f"    Document type: {document_type}"
        )


        # =========================
        # Chunk Pages
        # =========================

        for page_number, page_text in pages_text:

            if not page_text:
                continue


            chunks = splitter.split_text(
                page_text
            )


            for chunk_number, chunk in enumerate(
                chunks,
                start=1
            ):

                chunk_id = (
                    f"{subject}_"
                    f"{file_name}_"
                    f"P{page_number}_"
                    f"C{chunk_number}"
                )


                all_ids.append(
                    chunk_id
                )

                all_documents.append(
                    chunk
                )


                all_metadatas.append({

                    "subject": subject,

                    "file_name": file_name,

                    "page": page_number,

                    "chunk_id": chunk_id,

                    "document_type": document_type
                })


        doc.close()


# =========================
# Check data
# =========================

if not all_documents:

    print(
        "No documents were found."
    )

    exit()


# =========================
# Embeddings
# =========================

print(
    "\nGenerating embeddings..."
)

embeddings = model.encode(
    all_documents,
    show_progress_bar=True
)

print(
    "Embeddings generated."
)


# =========================
# Store in ChromaDB
# =========================

print(
    "\nStoring data in ChromaDB..."
)

collection.add(

    ids=all_ids,

    documents=all_documents,

    embeddings=embeddings.tolist(),

    metadatas=all_metadatas
)


# =========================
# Verify
# =========================

print(
    "\n=============================="
)

print(
    "INGESTION COMPLETED"
)

print(
    "=============================="
)

print(
    f"Total chunks: "
    f"{len(all_documents)}"
)

print(
    f"Embedding dimension: "
    f"{len(embeddings[0])}"
)

print(
    f"Database count: "
    f"{collection.count()}"
)


# =========================
# Document Types
# =========================

print(
    "\nDocument types found:"
)

types = set(
    metadata["document_type"]
    for metadata in all_metadatas
)

for document_type in sorted(types):

    count = sum(
        1
        for metadata in all_metadatas
        if metadata["document_type"]
        == document_type
    )

    print(
        f"- {document_type}: "
        f"{count} chunks"
    )