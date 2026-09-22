import chromadb
import json
import os

VECTOR_STORE_PATH = "data/vector_store"
COLLECTION_NAME = "study_materials"


# =========================
# ChromaDB
# =========================

client = chromadb.PersistentClient(
    path=VECTOR_STORE_PATH
)

collection = client.get_collection(
    name=COLLECTION_NAME
)


# =========================
# Get Exam Documents
# =========================

def get_exam_documents(subject=None):

    if subject:

        results = collection.get(
            where={
                "$and": [
                    {
                        "document_type": "exam"
                    },
                    {
                        "subject": subject
                    }
                ]
            },
            include=[
                "documents",
                "metadatas"
            ]
        )

    else:

        results = collection.get(
            where={
                "document_type": "exam"
            },
            include=[
                "documents",
                "metadatas"
            ]
        )

    return results


# =========================
# Test
# =========================
import ollama

def analyze_exams(documents, metadatas):

    from collections import Counter, defaultdict
    import re

    # ==========================================
    # Group by exam
    # ==========================================

    exams = defaultdict(list)

    for document, metadata in zip(documents, metadatas):
        exams[metadata["file_name"]].append(document)

    # ==========================================
    # Counters
    # ==========================================

    topic_counter = Counter()

    format_counter = Counter()

    wording_counter = Counter()

    exam_stats = {}

    # ==========================================
    # Analyze each exam
    # ==========================================

    for file_name, chunks in exams.items():

        text = "\n".join(chunks)
        text_upper = text.upper()

        # -------------------------
        # Question formats
        # -------------------------

        formats = {
            "True / False": len(
                re.findall(
                    r"\bTRUE\b|\bFALSE\b|\bT/F\b",
                    text_upper
                )
            ),

            "Problem": len(
                re.findall(
                    r"\bPROBLEM\s+\d+",
                    text_upper
                )
            ),

            "Question": len(
                re.findall(
                    r"\bQUESTION\s+\d+",
                    text_upper
                )
            ),

            "Part": len(
                re.findall(
                    r"\bPART\s+[A-Z]",
                    text_upper
                )
            ),

            "Points / Marks": len(
                re.findall(
                    r"\b\d+\s*POINTS?\b|\b\d+\s*MARKS?\b",
                    text_upper
                )
            )
        }

        # -------------------------
        # Wording patterns
        # -------------------------

        wording = {
            "Explain": len(
                re.findall(
                    r"\bEXPLAIN\b",
                    text_upper
                )
            ),

            "Calculate": len(
                re.findall(
                    r"\bCALCULATE\b",
                    text_upper
                )
            ),

            "Justify": len(
                re.findall(
                    r"\bJUSTIFY\b",
                    text_upper
                )
            ),

            "Derive": len(
                re.findall(
                    r"\bDERIVE\b",
                    text_upper
                )
            ),

            "Compare": len(
                re.findall(
                    r"\bCOMPARE\b",
                    text_upper
                )
            ),

            "Briefly": len(
                re.findall(
                    r"\bBRIEFLY\b",
                    text_upper
                )
            )
        }

        # Add to global counters

        for key, value in formats.items():
            format_counter[key] += value

        for key, value in wording.items():
            wording_counter[key] += value

        # -------------------------
        # Topic keywords
        # -------------------------

        topics = [
            "SVM",
            "SUPPORT VECTOR",
            "NEURAL NETWORK",
            "BACKPROPAGATION",
            "LOGISTIC REGRESSION",
            "DECISION TREE",
            "PRUNING",
            "CROSS VALIDATION",
            "OVERFITTING",
            "NEAREST NEIGHBOR",
            "K-NN",
            "ADABOOST",
            "MUTUAL INFORMATION",
            "FEATURE SELECTION",
            "KERNEL",
            "RADIAL BASIS",
            "POLYNOMIAL",
            "SIGMOID"
        ]

        for topic in topics:

            count = text_upper.count(topic)

            if count > 0:
                topic_counter[topic] += count

        exam_stats[file_name] = {
            "chunks": len(chunks),
            "formats": formats,
            "wording": wording
        }

    # ==========================================
    # Print Analysis
    # ==========================================

    print("\n")
    print("=" * 50)
    print("PREVIOUS EXAMS ANALYSIS")
    print("=" * 50)

    print("\n1. RECURRING TOPICS")

    for topic, count in topic_counter.most_common():
        print(f"- {topic}: {count}")

    print("\n2. QUESTION FORMATS")

    for fmt, count in format_counter.most_common():
        print(f"- {fmt}: {count}")

    print("\n3. QUESTION WORDING PATTERNS")

    for word, count in wording_counter.most_common():
        print(f"- {word}: {count}")

    print("\n4. EXAMS ANALYZED")

    for file_name, stats in exam_stats.items():

        print(
            f"- {file_name}: "
            f"{stats['chunks']} chunks"
        )

    print("\n5. PRACTICE DIRECTIONS")

    print(
        "- Practice problem-solving questions."
    )

    print(
        "- Practice True/False questions."
    )

    print(
        "- Practice explaining concepts briefly."
    )

    print(
        "- Practice calculation and derivation questions."
    )

    print(
        "- Practice questions involving the recurring topics above."
    )

    print("=" * 50)

    return {
        "topics": topic_counter,
        "formats": format_counter,
        "wording": wording_counter,
        "exam_stats": exam_stats
    }
def generate_practice_questions(analysis, num_questions=10):

    prompt = f"""
You are an academic exam question generator.

Your task is to generate NEW practice questions
based ONLY on the observed patterns in previous exams.

IMPORTANT:
- Do NOT copy questions from previous exams.
- Do NOT reproduce exact questions.
- Do NOT invent topics that are not present in the analysis.
- Follow the observed question formats and wording style.
- The questions should resemble the instructor's style,
  but they must be new questions.
- Include answers/model answers.
- Include the question type.
- Include the expected difficulty.

========================
EXAM STYLE ANALYSIS
========================

Recurring topics:

{dict(analysis["topics"])}

Question formats:

{dict(analysis["formats"])}

Question wording patterns:

{dict(analysis["wording"])}

========================
TASK
========================

Generate {num_questions} new practice questions.

Try to reproduce the observed distribution of:

- Problem solving
- True / False
- Explain
- Calculate
- Justify
- Derive
- Short answer

when supported by the analysis.

For every question use this structure:

QUESTION 1
Type:
Topic:
Difficulty:

Question:
...

MODEL ANSWER:

...

========================
PRACTICE QUESTIONS
========================
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
            "temperature": 0.2,
            "num_predict": 1200
        }
    )

    return response["message"]["content"]
if __name__ == "__main__":

    results = get_exam_documents()

    documents = results["documents"]
    metadatas = results["metadatas"]
    from collections import defaultdict
    exams = defaultdict(list)

for document, metadata in zip(documents, metadatas):
    file_name = metadata["file_name"]

    exams[file_name].append(document)
    print("\n==============================")
    print("EXAMS FOUND")
    print("==============================")

    for file_name, chunks in exams.items():

        print(
            f"{file_name}: {len(chunks)} chunks"
        )

    print("\n==============================")
    print("PREVIOUS EXAMS")
    print("==============================")

    print(
        f"Exam chunks found: {len(documents)}"
    )
    print("\nAnalyzing previous exams...")

    analysis = analyze_exams(
    documents,
    metadatas
)
    os.makedirs("data/analysis", exist_ok=True)

    with open(
        "data/analysis/exam_analysis.json",
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            {
                "analysis": analysis
            },
            f,
            ensure_ascii=False,
            indent=4
        )

    print("\nExam analysis saved successfully.")
    print(
        "File: data/analysis/exam_analysis.json"
    )
    print("\n")
    print("=" * 50)
    print("GENERATING PRACTICE QUESTIONS")
    print("=" * 50)

    # practice_questions = generate_practice_questions(
    #     analysis,
    #     num_questions=5
    # )

    # print(practice_questions)

    print("\n==============================")
    print("EXAM ANALYSIS")
    print("==============================")

    print(analysis)

    for i, (document, metadata) in enumerate(
        zip(documents, metadatas)
    ):

        print(
            f"\n--- Exam Chunk {i + 1} ---"
        )

        print(
            f"File: {metadata['file_name']}"
        )

        print(
            f"Page: {metadata['page']}"
        )

        print(
            document[:500]
        )