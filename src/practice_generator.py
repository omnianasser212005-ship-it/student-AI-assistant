import json
import ollama


ANALYSIS_PATH = "data/analysis/exam_analysis.json"


def load_exam_analysis():

    with open(
        ANALYSIS_PATH,
        "r",
        encoding="utf-8"
    ) as f:

        data = json.load(f)

    return data["analysis"]


import ollama


def generate_practice_questions(
    exam_documents,
    num_questions=5,
    subject=None
):

    if not exam_documents:

        return (
            "No previous exams were found "
            "for the selected subject."
        )

    exam_context = "\n\n".join(
        exam_documents
    )

    prompt = f"""
You are an academic practice-question generator.

Generate exactly {num_questions} NEW practice questions.

Use ONLY the previous exam content below.

Selected subject:
{subject or "All Subjects"}

IMPORTANT RULES:

1. Generate questions based only on the provided exams.
2. Follow the style and topics of the previous exams.
3. Do not copy questions exactly.
4. Do not invent topics that do not appear in the exams.
5. Do not predict the real exam.
6. Each question should be useful for student practice.
7. Include a short model answer.
8. Number every question clearly.

Return this format:

Question 1
Type: ...
Topic: ...
Question: ...
Short model answer: ...

Question 2
Type: ...
Topic: ...
Question: ...
Short model answer: ...

PREVIOUS EXAMS:

{exam_context}
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
            "temperature": 0.3,
            "num_predict": 2000
        }
    )

    return response["message"]["content"].strip()


if __name__ == "__main__":

    print("Loading exam analysis...")

    analysis = load_exam_analysis()

    result = generate_practice_questions(
        analysis,
        num_questions=5
    )

    print("\n==============================")
    print("PRACTICE QUESTIONS")
    print("==============================")

    print(result)