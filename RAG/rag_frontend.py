import streamlit as st
import rag_backend as rag_back

st.set_page_config(page_title="Read Paper with RAG")

new_title = '<p style="font-family:sans-serif; color:Green; font-size: 42px;">Read Paper For Me</p>'
st.markdown(new_title, unsafe_allow_html=True)

# New text box for PDF URL input
pdf_url = st.text_input("Enter PDF URL", value="", key="pdf_url")

# New button to handle PDF URL submission
load_pdf_button = st.button("Load PDF")

input_text = st.text_area("Input Questions", label_visibility="visible", key="input_text")


# Create columns for buttons
col1, col2 = st.columns([2, 1])  # Adjust the ratio as needed

with col1:
    # Original button for question answering
    go_button = st.button("Answer Me", type="primary")

with col2:
    # New button to clear the session
    clear_session_button = st.button("Clear Session", type="secondary")

# Error message container
error_message = st.empty()


# Handle the clear session button
if clear_session_button:
    try:
        st.session_state.clear()
        rag_back.clear_pdf_data()  # Clear backend data
        st.success("Session cleared successfully!")
    except Exception as e:
        error_message.error(f"An error occurred while clearing the session: {str(e)}")


if load_pdf_button:
    if not pdf_url.strip():
        error_message.error("Please enter a valid PDF URL.")
    elif 'vector_index' in st.session_state:
        error_message.error("A document is already loaded. Please start a new session to load a different document.")
    else:
        try:
            with st.spinner("Loading PDF and Reading..."):
                st.session_state.vector_index = rag_back.load_pdf_and_create_index(pdf_url)
                st.success("PDF loaded successfully!")
                error_message.empty()  # Clear any previous error messages
        except Exception as e:
            error_message.error(f"An error occurred while loading the PDF: {str(e)}")


if go_button:
    if 'vector_index' not in st.session_state:
        error_message.error("Please load a PDF document before asking questions.")
    else:
        with st.spinner("📢一生懸命回答中"):
            try:
                response_content = rag_back.get_rag_response(index=st.session_state.vector_index, question=input_text)
                st.write(response_content)
            except Exception as e:
                error_message.error(f"An error occurred while generating the response: {str(e)}")
