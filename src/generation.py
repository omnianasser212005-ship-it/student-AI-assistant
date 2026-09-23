import ollama

from src.retrieval import search

from src.feedback_learning import (
    get_learning_context,
    add_feedback,
    learn_from_feedback
)


def build_context(results):

    documents = results.get(
        "documents",
        [[]]
    )[0]

    metadatas = results.get(
        "metadatas",
        [[]]
    )[0]

    context_parts = []

    for document, metadata in zip(
        documents,
        metadatas
    ):

        if metadata is None:
            continue

        context_parts.append(
            f"""
SOURCE
File: {metadata.get("file_name", "Unknown")}
Subject: {metadata.get("subject", "Unknown")}
Page: {metadata.get("page", "Unknown")}

CONTENT:
{document}
"""
        )

    return "\n\n".join(context_parts)


def generate_answer(
    question,
    top_k=8,
    subject=None,
    document_type=None
):

    # =========================
    # Retrieve relevant chunks
    # =========================

    results = search(
        query=question,
        top_k=top_k,
        subject=subject,
        document_type=document_type
    )

    # =========================
    # Build context
    # =========================

    context = build_context(results)

    if not context:

        return {
            "answer": (
                "I could not find enough information "
                "in the provided study materials."
            ),
            "context": "",
            "sources": []
        }

    # =========================
    # Get learned rules
    # =========================

    learning_context = get_learning_context()

    # =========================
    # Build Prompt
    # =========================

    prompt = f"""
You are an AI academic study assistant.

Your job is to answer the student's question
using the provided study materials.

IMPORTANT RULES:

1. Use the study context as the primary source.

2. Do not invent information that is not supported
   by the provided study context.

3. Do not use your general knowledge to fill
   missing information.

4. If the study context does not contain enough
   information, clearly say:

"The provided study materials do not contain
enough information to answer this question."

5. Explain the answer clearly and simply.

6. Give ONE practical example only if the example
   is supported by the study materials.

7. At the end, list the source file and page.

8. Follow the learned response preferences below
   when they do not conflict with the study context.

========================
LEARNED FROM USER FEEDBACK
========================

{learning_context}

========================
STUDY CONTEXT
========================

{context}

========================
STUDENT QUESTION
========================

{question}

========================
ANSWER
========================
"""

    # =========================
    # Generate Answer
    # =========================

    print("\nGenerating answer...")

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
            "num_predict": 800
        }
    )

    answer = response["message"]["content"]

    # =========================
    # Sources
    # =========================

    sources = []

    metadatas = results.get(
        "metadatas",
        [[]]
    )[0]

    for metadata in metadatas:

        if metadata is None:
            continue

        source = {
            "file_name": metadata.get(
                "file_name",
                "Unknown"
            ),
            "subject": metadata.get(
                "subject",
                "Unknown"
            ),
            "page": metadata.get(
                "page",
                "Unknown"
            )
        }

        if source not in sources:
            sources.append(source)

    return {
        "answer": answer,
        "context": context,
        "sources": sources
    }


# =========================
# User Feedback
# =========================

def collect_user_feedback(
    question,
    answer,
    sources
):

    print("\n==============================")
    print("USER EVALUATION")
    print("==============================")

    while True:

        try:

            rating = int(
                input(
                    "Rate this answer from 1 to 5: "
                )
            )

            if 1 <= rating <= 5:
                break

            print("Please enter a number from 1 to 5.")

        except ValueError:

            print(
                "Please enter a valid number."
            )

    feedback = input(
        "What should be improved? "
    ).strip()

    add_feedback(
        question=question,
        answer=answer,
        rating=rating,
        feedback=feedback,
        sources=sources
    )

    print("\nFeedback saved.")

    # Learn immediately from the new feedback
    learn_from_feedback()

    print("Learning updated.")


# =========================
# Test
# =========================

if __name__ == "__main__":

    print("==============================")
    print("STUDENT AI ASSISTANT")
    print("==============================")

    question = input(
        "\nEnter your question: "
    )

    result = generate_answer(
        question=question,
        top_k=8
    )

    print("\n==============================")
    print("ANSWER")
    print("==============================")

    print(
        result["answer"]
    )

    print("\n==============================")
    print("SOURCES")
    print("==============================")

    for source in result["sources"]:

        print(
            f"- {source['file_name']} "
            f"(Page {source['page']})"
        )

    # =========================
    # Ask user for evaluation
    # =========================

    collect_user_feedback(
        question=question,
        answer=result["answer"],
        sources=result["sources"]
    )

