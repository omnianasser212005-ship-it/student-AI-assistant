import os
import json
import ollama


FEEDBACK_DIR = "data/feedback"
FEEDBACK_PATH = os.path.join(
    FEEDBACK_DIR,
    "user_feedback.json"
)

LEARNED_RULES_PATH = os.path.join(
    FEEDBACK_DIR,
    "learned_rules.json"
)


def ensure_feedback_dir():

    os.makedirs(
        FEEDBACK_DIR,
        exist_ok=True
    )


def load_feedback():

    ensure_feedback_dir()

    if not os.path.exists(FEEDBACK_PATH):
        return []

    with open(
        FEEDBACK_PATH,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


def save_feedback(feedback):

    ensure_feedback_dir()

    with open(
        FEEDBACK_PATH,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            feedback,
            f,
            ensure_ascii=False,
            indent=4
        )


def load_learned_rules():

    ensure_feedback_dir()

    if not os.path.exists(LEARNED_RULES_PATH):
        return []

    with open(
        LEARNED_RULES_PATH,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


def save_learned_rules(rules):

    ensure_feedback_dir()

    with open(
        LEARNED_RULES_PATH,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            rules,
            f,
            ensure_ascii=False,
            indent=4
        )


def add_feedback(
    question,
    answer,
    rating,
    feedback,
    sources=None
):

    data = load_feedback()

    new_feedback = {
        "question": question,
        "answer": answer,
        "rating": rating,
        "feedback": feedback,
        "sources": sources or []
    }

    data.append(new_feedback)

    save_feedback(data)

    print("User feedback saved.")


def learn_from_feedback():

    feedback_data = load_feedback()

    if not feedback_data:
        print("No feedback available.")
        return []

    # Only use meaningful negative/low ratings
    useful_feedback = [
        item
        for item in feedback_data
        if item.get("rating", 5) <= 3
        and item.get("feedback")
    ]

    if not useful_feedback:
        print("No negative feedback to learn from.")
        return load_learned_rules()

    feedback_text = ""

    for item in useful_feedback:

        feedback_text += f"""
QUESTION:
{item["question"]}

RATING:
{item["rating"]}/5

USER FEEDBACK:
{item["feedback"]}

------------------------
"""

    prompt = f"""
You are a feedback-learning component
for an academic study assistant.

Analyze the user feedback below.

Your task is to identify GENERAL response
improvement rules that can help the assistant
answer future students better.

Do NOT extract academic facts from the feedback.

Do NOT invent facts.

Focus ONLY on response behavior, such as:

- clarity
- conciseness
- explanation depth
- organization
- use of examples
- difficulty level
- source usage
- avoiding unsupported information

Return ONLY a JSON array.

Example:

[
    "Use simpler explanations when possible.",
    "Keep answers concise unless the student asks for detail.",
    "Use examples from the provided study material when available."
]

USER FEEDBACK:

{feedback_text}
"""

    print("Learning from user feedback...")

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

    content = response["message"]["content"].strip()

    try:

        # Remove markdown code fences if Llama adds them
        content = content.replace(
            "```json",
            ""
        ).replace(
            "```",
            ""
        ).strip()

        new_rules = json.loads(content)

        if not isinstance(new_rules, list):
            return load_learned_rules()

    except Exception:

        print(
            "Could not parse learned rules."
        )

        return load_learned_rules()

    old_rules = load_learned_rules()

    combined_rules = old_rules + new_rules

    # Remove duplicates
    combined_rules = list(
        dict.fromkeys(combined_rules)
    )

    save_learned_rules(
        combined_rules
    )

    print(
        f"Learned rules: {len(combined_rules)}"
    )

    return combined_rules


def get_learning_context():

    rules = load_learned_rules()

    if not rules:
        return ""

    context = """
USER FEEDBACK LEARNING RULES:

The following rules were learned from
previous student feedback.

Follow them when generating future answers:

"""

    for rule in rules:
        context += f"- {rule}\n"

    return context

