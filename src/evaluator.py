import ollama


def evaluate_response(
    response,
    context,
    task_type
):

    prompt = f"""
You are an academic response evaluator.

Evaluate the following AI-generated response
based ONLY on the provided study context.

TASK TYPE:
{task_type}

STUDY CONTEXT:
{context}

AI RESPONSE:
{response}

Evaluate using these criteria:

1. ACCURACY
Is the response supported by the study context?

2. RELEVANCE
Does the response directly address the task?

3. COMPLETENESS
Does the response include the important information
needed for the task?

4. CLARITY
Is the response clear and understandable?

Return:

SCORE
Give a score from 0 to 10.

STRENGTHS
List the main strengths.

WEAKNESSES
List the main weaknesses.

SUGGESTIONS
Give practical suggestions for improvement.

IMPORTANT:
Do not invent information that is not supported
by the study context.
"""

    result = ollama.chat(
        model="llama3.2",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        options={
            "temperature": 0,
            "num_predict": 500
        }
    )

    return result["message"]["content"]


if __name__ == "__main__":

    print("Evaluator module ready.")


