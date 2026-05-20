import streamlit as st
from database.mongodb import get_or_create_user

def login():
    if st.session_state.get("user_id") is not None:
        return True
    st.title("🏋️ AI  Ral-time GYM Trainer")
    st.markdown("### welcome! Please enter a username to start.")

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input(
            "Enter username", placeholder="unique name e.g. harsha"
        )
        submit_btn = st.form_submit_button("start session", width="stretch")

    if submit_btn:
        if not username:
            st.error("Name cannot be empty")
            return False
        user = get_or_create_user(username)

        st.session_state.username = user["username"]
        st.session_state.user_id =user["_id"]
        st.rerun()

    return False
