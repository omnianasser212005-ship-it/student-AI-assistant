import streamlit as st
import os


from api_client import (
    health_check,
    ask_question,
    send_feedback,
    upload_pdf,
    explain_file,
    summarize_file,
    generate_practice_questions,
    get_exam_files
)


# =========================================================
# Page Configuration
# =========================================================

st.set_page_config(
    page_title="Student AI Assistant",
  
    layout="wide"
)


# =========================================================
# Header
# =========================================================

st.title(" Student AI Assistant")

st.caption(
    "Your AI assistant for university study materials."
)


# =========================================================
# Backend Status
# =========================================================

try:

    health_check()

    st.success("🟢 Backend is online")

except Exception:

    st.error(
        "🔴 Backend is not available. "
        "Start the FastAPI server first."
    )

    st.stop()


# =========================================================
# Sidebar
# =========================================================

with st.sidebar:

    st.header("Study Materials")

    st.write(
        "Upload your lecture notes or previous exams."
    )

    uploaded_file = st.file_uploader(
        "Upload PDF",
        type=["pdf"],
        key="sidebar_pdf_uploader"
    )

    subject = st.text_input(
        "Subject",
        placeholder="Example: Software Engineering",
        key="sidebar_subject"
    )

    if st.button(
        "Upload PDF",
        use_container_width=True,
        key="sidebar_upload_button"
    ):

        if uploaded_file is None:

            st.warning(
                "Please select a PDF."
            )

        elif not subject.strip():

            st.warning(
                "Please enter the subject."
            )

        else:

            with st.spinner(
                "Processing PDF..."
            ):

                try:

                    result = upload_pdf(
                        file=uploaded_file,
                        subject=subject
                    )

                    file_info = result.get(
                        "file",
                        {}
                    )

                    st.success(
                        "PDF uploaded successfully!"
                    )

                    st.info(
                        f"""
 **File:** {file_info.get(
    "file_name",
    uploaded_file.name
)}

 **Subject:** {file_info.get(
    "subject",
    subject
)}

 **Chunks:** {file_info.get(
    "chunks",
    "Unknown"
)}

 **Type:** {file_info.get(
    "document_type",
    "Unknown"
)}
"""
                    )

                except Exception as e:

                    st.error(
                        f"Upload error: {e}"
                    )
        try:

            exam_result = get_exam_files()

            exam_files = exam_result.get(
                "files",
                []
            )

        except Exception:

            exam_files = []
try:
    exam_result = get_exam_files()

    exam_files = exam_result.get(
        "files",
        []
    )

except Exception as e:

    exam_files = []

    st.warning(
        f"Could not load previous exams: {e}"
    )

# =========================================================
# Tabs
# =========================================================

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "Ask & Example",
        "Explain File",
        "Summarize File",
        "Practice Questions"
    ]
)


# =========================================================
# TAB 1
# Answer + Human Practical Example
# =========================================================

with tab1:

    st.header(
        "Ask a Question"
    )

    st.write(
        "Ask a question about your uploaded study materials."
    )

    question = st.text_area(
        "Your Question",
        placeholder=(
            "Example: What is software architecture?"
        ),
        height=120,
        key="main_question"
    )

    col1, col2 = st.columns(
        [3, 1]
    )

    with col1:

        subject_filter = st.text_input(
            "Optional Subject Filter",
            placeholder="Example: Software Engineering",
            key="question_subject"
        )

    with col2:

        top_k = st.number_input(
            "Sources",
            min_value=1,
            max_value=20,
            value=8,
            key="question_top_k"
        )

    if st.button(
        "Ask Question",
        type="primary",
        use_container_width=True,
        key="main_ask_button"
    ):

        if not question.strip():

            st.warning(
                "Please enter a question."
            )

        else:

            with st.spinner(
                "Searching your study materials..."
            ):

                try:

                    result = ask_question(
                        question=question,
                        top_k=top_k,
                        subject=(
                            subject_filter.strip()
                            if subject_filter.strip()
                            else None
                        )
                    )

                    st.session_state[
                        "last_question"
                    ] = question

                    st.session_state[
                        "last_answer"
                    ] = result.get(
                        "answer",
                        ""
                    )

                    st.session_state[
                        "last_sources"
                    ] = result.get(
                        "sources",
                        []
                    )

                    st.session_state[
                        "practical_example"
                    ] = result.get(
                        "practical_example",
                        ""
                    )

                except Exception as e:

                    st.error(
                        f"Error: {e}"
                    )


    if "last_answer" in st.session_state:

        st.divider()

        st.subheader(
            "Answer"
        )

        st.write(
            st.session_state[
                "last_answer"
            ]
        )


        practical_example = st.session_state.get(
            "practical_example",
            ""
        )

        if practical_example:

            st.subheader(
                "Human Practical Example"
            )

            st.info(
                practical_example
            )


        st.subheader(
            "Sources"
        )

        sources = st.session_state.get(
            "last_sources",
            []
        )

        if sources:

            for source in sources:

                st.info(
                    f"{source.get('file_name', 'Unknown')} "
                    f"— Page {source.get('page', 'Unknown')}"
                )

        else:

            st.write(
                "No sources available."
            )


        # =================================================
        # Feedback
        # =================================================

        st.divider()

        st.subheader(
            "Improve the Assistant"
        )

        rating = st.slider(
            "Rate this answer",
            1,
            5,
            3,
            key="answer_rating"
        )

        feedback = st.text_area(
            "What should be improved?",
            placeholder=(
                "Example: Make the explanation shorter "
                "and use a simple example."
            ),
            key="answer_feedback"
        )

        if st.button(
            "Send Feedback",
            use_container_width=True,
            key="send_answer_feedback"
        ):

            if not feedback.strip():

                st.warning(
                    "Please enter your feedback."
                )

            else:

                try:

                    result = send_feedback(
                        question=st.session_state[
                            "last_question"
                        ],
                        answer=st.session_state[
                            "last_answer"
                        ],
                        rating=rating,
                        feedback=feedback,
                        sources=sources
                    )

                    st.success(
                        result.get(
                            "message",
                            "Feedback saved successfully."
                        )
                    )

                except Exception as e:

                    st.error(
                        f"Feedback error: {e}"
                    )



# =========================================================
# Available Study Files
# =========================================================

RAW_DATA_PATH = "data/raw"


def get_available_study_files():

    files = []

    if not os.path.exists(RAW_DATA_PATH):
        return files

    for subject_name in os.listdir(RAW_DATA_PATH):

        subject_path = os.path.join(
            RAW_DATA_PATH,
            subject_name
        )

        if not os.path.isdir(subject_path):
            continue

        for file_name in os.listdir(subject_path):

            if file_name.lower().endswith(".pdf"):

                files.append({
                    "subject": subject_name,
                    "file_name": file_name
                })

    return files


available_files = get_available_study_files()


# =========================================================
# TAB 2
# Explain Specific File
# =========================================================

with tab2:

    st.header(
        "Explain a Specific File"
    )

    st.write(
        "Choose a file from your uploaded study materials."
    )

    if not available_files:

        st.warning(
            "No PDF study materials were found."
        )

    else:

        explain_options = [
            f"{item['subject']} — {item['file_name']}"
            for item in available_files
        ]

        selected_explain = st.selectbox(
            "Select File",
            explain_options,
            key="explain_file_select"
        )

        selected_index = explain_options.index(
            selected_explain
        )

        selected_explain_file = available_files[
            selected_index
        ]

        explain_subject = selected_explain_file[
            "subject"
        ]

        explain_file_name = selected_explain_file[
            "file_name"
        ]

        st.info(
            f"Subject: {explain_subject}\n\n"
            f"File: {explain_file_name}"
        )

        if st.button(
            "Explain File",
            type="primary",
            use_container_width=True,
            key="explain_file_button"
        ):

            with st.spinner(
                "Reading and explaining the file..."
            ):

                try:

                    result = explain_file(
                        file_name=explain_file_name,
                        subject=explain_subject
                    )

                    st.session_state[
                        "file_explanation"
                    ] = result.get(
                        "explanation",
                        ""
                    )

                    st.session_state[
                        "explained_file_name"
                    ] = explain_file_name

                except Exception as e:

                    st.error(
                        f"Error: {e}"
                    )

        if "file_explanation" in st.session_state:

            st.divider()

            st.subheader(
                f"Explanation: "
                f"{st.session_state.get('explained_file_name', '')}"
            )

            st.write(
                st.session_state[
                    "file_explanation"
                ]
            )


# =========================================================
# TAB 3
# Summarize Specific File
# =========================================================

with tab3:

    st.header(
        "Summarize a Specific File"
    )

    st.write(
        "Generate a concise study summary from one file."
    )

    if not available_files:

        st.warning(
            "No PDF study materials were found."
        )

    else:

        summary_options = [
            f"{item['subject']} — {item['file_name']}"
            for item in available_files
        ]

        selected_summary = st.selectbox(
            "Select File",
            summary_options,
            key="summary_file_select"
        )

        selected_index = summary_options.index(
            selected_summary
        )

        selected_summary_file = available_files[
            selected_index
        ]

        summary_subject = selected_summary_file[
            "subject"
        ]

        summary_file_name = selected_summary_file[
            "file_name"
        ]

        st.info(
            f"Subject: {summary_subject}\n\n"
            f"File: {summary_file_name}"
        )

        if st.button(
            "Summarize File",
            type="primary",
            use_container_width=True,
            key="summary_file_button"
        ):

            with st.spinner(
                "Creating study summary..."
            ):

                try:

                    result = summarize_file(
                        file_name=summary_file_name,
                        subject=summary_subject
                    )

                    st.session_state[
                        "file_summary"
                    ] = result.get(
                        "summary",
                        ""
                    )

                    st.session_state[
                        "summarized_file_name"
                    ] = summary_file_name

                except Exception as e:

                    st.error(
                        f"Error: {e}"
                    )

        if "file_summary" in st.session_state:

            st.divider()

            st.subheader(
                f"Study Summary: "
            )
            st.write(
                st.session_state[
                    "file_summary"
                ]
            )
                




# =========================================================
# TAB 4
# Previous Exams → Practice Questions
# =========================================================


# =========================================================
# TAB 4
# Previous Exams → Practice Questions
# =========================================================

with tab4:

    st.header(
        "Previous Exams → Practice Questions"
    )

    st.write(
        "Generate new practice questions "
        "based on previous exams."
    )

    # =====================================================
    # No exams
    # =====================================================

    if not exam_files:

        st.warning(
            "No previous exams were found in the study database."
        )

    else:

        # =================================================
        # Subjects from EXAMS only
        # =================================================

        exam_subjects = sorted(
            list(
                set(
                    item["subject"]
                    for item in exam_files
                )
            )
        )

        practice_subject = st.selectbox(
            "Subject",
            exam_subjects,
            key="practice_subject"
        )

        # =================================================
        # Exams for selected subject
        # =================================================

        subject_exams = [
            item
            for item in exam_files
            if item["subject"] == practice_subject
        ]

        exam_options = [
            item["file_name"]
            for item in subject_exams
        ]

        selected_exam = st.selectbox(
            "Select Previous Exam",
            exam_options,
            key="practice_exam_file"
        )

        # =================================================
        # Number of questions
        # =================================================

        number_of_questions = st.slider(
            "Number of Questions",
            min_value=1,
            max_value=30,
            value=5,
            key="practice_number"
        )

        st.info(
            f"Subject: {practice_subject}\n\n"
            f"Previous Exam: {selected_exam}"
        )

        # =================================================
        # Generate
        # =================================================

        if st.button(
            "Generate Practice Questions",
            type="primary",
            use_container_width=True,
            key="practice_button"
        ):

            with st.spinner(
                "Generating practice questions..."
            ):

                try:

                    result = generate_practice_questions(
                        number_of_questions=number_of_questions,
                        subject=practice_subject,
                        file_name=selected_exam
                    )

                    st.session_state[
                        "practice_questions"
                    ] = result.get(
                        "questions",
                        ""
                    )

                except Exception as e:

                    st.error(
                        f"Error: {e}"
                    )

        # =================================================
        # Display
        # =================================================

        if "practice_questions" in st.session_state:

            st.divider()

            st.subheader(
                "Practice Questions"
            )

            st.write(
                st.session_state[
                    "practice_questions"
                ]
            )


            


    

