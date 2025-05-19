# auth.py - Функции аутентификации и авторизации

import streamlit as st
from config import ROLES, PASSWORD, MAX_LOGIN_ATTEMPTS

# Безопасный перезапуск Streamlit
try:
    from streamlit import experimental_rerun
except ImportError:
    def experimental_rerun():
        st.stop()

def show_login() -> None:
    """
    Отображает страницу входа и обрабатывает аутентификацию пользователя.
    """
    st.title("🔒 Industry Dashboard Login")
    remaining = MAX_LOGIN_ATTEMPTS - st.session_state.login_attempts
    
    if remaining <= 0:
        st.error("Too many failed attempts. Access locked. Please restart the app.")
        return
        
    st.warning(f"You have {remaining} login attempt{'s' if remaining>1 else ''} remaining.")
    
    role = st.selectbox("Select Role", ROLES)
    pwd = st.text_input("Enter password:", type="password")
    
    if st.button("Login"):
        if st.session_state.login_attempts >= MAX_LOGIN_ATTEMPTS:
            st.error("Access locked. Too many attempts.")
        elif pwd == PASSWORD:
            st.session_state.logged_in = True
            st.session_state.login_error = False
            st.session_state.role = role
            st.session_state.login_attempts = 0
            experimental_rerun()
        else:
            st.session_state.login_error = True
            st.session_state.login_attempts += 1
            
        if st.session_state.login_error:
            st.error("Invalid password.")