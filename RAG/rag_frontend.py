import streamlit as st 
import rag_backend as rag_back

st.set_page_config(page_title="Read Paper with RAG")

new_title = '<p style="font-family:sans-serif; color:Green; font-size: 42px;">Read Paper For Me</p>'
st.markdown(new_title, unsafe_allow_html=True)

if 'vector_index' not in st.session_state: 
    with st.spinner("📀 Waiting please I am reading the paper!"): 
        st.session_state.vector_index = rag_back.hr_index()

input_text = st.text_area("Input text", label_visibility="collapsed") 
go_button = st.button("Answer Me", type="primary") ### Button Name

if go_button: 
    
    with st.spinner("📢一生懸命回答中"): 
        response_content = rag_back.hr_rag_response(index=st.session_state.vector_index, question=input_text) ### replace with RAG Function from backend file
        st.write(response_content) 