import ollama

from retrieval import get_file_chunks


MODEL_NAME = "llama3.2"


def summarize_file(subject, file_name):

    # =========================
    # Get all chunks of the file
    # =========================

    results = get_file_chunks(
        subject,
        file_name
    )

    documents = results["documents"]
    metadatas = results["metadatas"]

    if not documents:

        return "The requested file was not found."


    # =========================
    # Sort chunks by page
    # =========================

    chunks = []

    for document, metadata in zip(
        documents,
        metadatas
    ):

        page = metadata.get(
            "page",
            0
        )

        chunks.append(
            (page, document)
        )


    chunks.sort(
        key=lambda x: x[0]
    )


    # =========================
    # Build file content
    # =========================

    file_content = ""

    for page, document in chunks:

        file_content += (
            f"\n\n--- Page {page} ---\n"
        )

        file_content += document


    # =========================
    # Summarization Prompt
    # =========================

    prompt = f"""
You are an AI academic study assistant.

Summarize the following study file.

IMPORTANT RULES:

1. Use ONLY the provided file content.
2. Do not add information that is not present
   in the file.
3. Keep the important definitions, concepts,
   characteristics, and relationships.
4. Organize the summary using clear headings
   and bullet points.
5. Keep the terminology used in the original
   study material.
6. Make the summary useful for exam revision.
7. Do not unnecessarily repeat information.
8. If an important concept appears on a specific
   page, mention its page number.

At the end, provide:

- Key Points
- Important Terms
- Exam Revision Notes

========================
FILE
========================

Subject:
{subject}

File:
{file_name}

========================
FILE CONTENT
========================

{file_content}

========================
SUMMARY
========================
"""


    # =========================
    # Call Ollama
    # =========================

    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )


    return response["message"]["content"]


# =========================
# Test
# =========================

if __name__ == "__main__":

    subject = input(
        "Enter subject: "
    )

    file_name = input(
        "Enter file name: "
    )

    summary = summarize_file(
        subject,
        file_name
    )

    print("\n")
    print("=" * 60)
    print("FILE SUMMARY")
    print("=" * 60)

    print(summary)