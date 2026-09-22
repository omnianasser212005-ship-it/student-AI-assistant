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


def generate_practice_questions(
    analysis,
    num_questions=5
):

    all_questions = []

    for i in range(1, num_questions + 1):

        print(f"\nGenerating question {i}/{num_questions}...")

        prompt = f"""
You are an academic practice-question generator.

Generate EXACTLY ONE NEW practice question.

Use ONLY the exam analysis below.

The question must follow the observed style
of the previous exams.

Return ONLY this format:

QUESTION
Type: ...
Topic: ...
Question: ...
Short model answer: ...

IMPORTANT:
- Generate ONE question only.
- Do not generate a second question.
- Do not copy an existing exam question.
- Do not predict the real exam.
- Keep the answer short.

EXAM ANALYSIS:

{analysis}
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
                "num_predict": 300
            }
        )

        question = response["message"]["content"].strip()

        all_questions.append(
            f"Question {i}\n{question}"
        )

        print(f"Question {i} completed.")

    return "\n\n==============================\n\n".join(
        all_questions
    )


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