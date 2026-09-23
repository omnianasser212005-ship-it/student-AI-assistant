import os

import requests
from dotenv import load_dotenv


load_dotenv()


API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://127.0.0.1:8000"
)


# =========================================================
# Health Check
# =========================================================

def health_check():

    response = requests.get(
        f"{API_BASE_URL}/health",
        timeout=10
    )

    response.raise_for_status()

    return response.json()


# =========================================================
# Ask Question
# =========================================================

def ask_question(
    question,
    top_k=8,
    subject=None,
    document_type=None
):

    response = requests.post(
        f"{API_BASE_URL}/query",
        json={
            "question": question,
            "top_k": top_k,
            "subject": subject,
            "document_type": document_type
        },
        timeout=120
    )

    response.raise_for_status()

    return response.json()


# =========================================================
# Upload PDF
# =========================================================

def upload_pdf(
    file,
    subject
):

    files = {
        "file": (
            file.name,
            file.getvalue(),
            "application/pdf"
        )
    }

    data = {
        "subject": subject
    }

    response = requests.post(
        f"{API_BASE_URL}/upload",
        files=files,
        data=data,
        timeout=300
    )

    response.raise_for_status()

    return response.json()


# =========================================================
# Feedback
# =========================================================

def send_feedback(
    question,
    answer,
    rating,
    feedback,
    sources=None
):

    response = requests.post(
        f"{API_BASE_URL}/feedback",
        json={
            "question": question,
            "answer": answer,
            "rating": rating,
            "feedback": feedback,
            "sources": sources or []
        },
        timeout=120
    )

    response.raise_for_status()

    return response.json()


# =========================================================
# Explain Specific File
# =========================================================

def explain_file(
    file_name,
    subject
):

    response = requests.post(
        f"{API_BASE_URL}/explain-file",
        json={
            "file_name": file_name,
            "subject": subject
        },
        timeout=180
    )

    response.raise_for_status()

    return response.json()


def summarize_file(
    file_name,
    subject
):

    response = requests.post(
        f"{API_BASE_URL}/summarize-file",
        json={
            "file_name": file_name,
            "subject": subject
        },
        timeout=180
    )

    response.raise_for_status()

    return response.json()

# =========================================================
# Previous Exams → Practice Questions
# =========================================================

def generate_practice_questions(
    number_of_questions=5,
    subject=None,
    file_name=None
):

    response = requests.post(
        f"{API_BASE_URL}/practice-questions",
        json={
            "number_of_questions": number_of_questions,
            "subject": subject,
            "file_name": file_name
        },
        timeout=300
    )

    response.raise_for_status()

    return response.json()

def explain_file(
    file_name,
    subject
):

    response = requests.post(
        f"{API_BASE_URL}/explain-file",
        json={
            "file_name": file_name,
            "subject": subject
        },
        timeout=180
    )

    response.raise_for_status()

    return response.json()


def summarize_file(
    file_name,
    subject
):

    response = requests.post(
        f"{API_BASE_URL}/summarize-file",
        json={
            "file_name": file_name,
            "subject": subject
        },
        timeout=180
    )

    response.raise_for_status()

    return response.json()


def get_exam_files():

    response = requests.get(
        f"{API_BASE_URL}/exam-files",
        timeout=30
    )

    response.raise_for_status()

    return response.json()







