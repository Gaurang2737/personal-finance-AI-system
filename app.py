import streamlit as st
from utils.database import SessionLocal, User, create_database_and_table
from utils.auth import verify_password, hash_password_auth

create_database_and_table()

st.set_page_config(
    page_title="Personal Finance AI",
    page_icon="🤖💰",
    layout="centered"
)

def show_login_page():
    st.title("Personal Finance AI System")
    st.write("Welcome back! Please Log in or sign up to Continue")
    login_tab, sign_up_tab = st.tabs(['Login','Sign Up'])
    with login_tab:
        with st.form('login form'):
            username= st.text_input("Username")
            password = st.text_input("Password",type='password')
            submitted = st.form_submit_button('Login')

            if submitted:
                db = SessionLocal()
                user = db.query(User).filter_by(username=username).first()
                db.close()

                if user and verify_password(password,user.hashed_password):
                    st.session_state["user_id"] = user.id
                    st.session_state["username"] = user.username
                    st.success('Logged in Successfully!!')
                    st.rerun()
                else:
                    st.error('Incorrect Username or password')

    with sign_up_tab:
        with st.form('Sign up'):
            new_username_text = st.text_input("Choose a Username")
            new_password_text = st.text_input('Choose a password')
            submitted = st.form_submit_button('Sign up')
            if submitted:
                db = SessionLocal()
                existing_user = db.query(User).filter_by(username=new_username_text).first()
                if existing_user:
                    st.error("Username already exists. Please choose another one")
                else:
                    hash_pass = hash_password_auth(new_password_text)
                    new_user = User(username= new_username_text,hashed_password= hash_pass )
                    db.add(new_user)
                    db.commit()
                    st.success("Account created successfully! Please go to the Login tab to log in.")
                db.close()

def show_main_page():
    st.sidebar.title(f"Welcome, {st.session_state['username']}!")
    st.sidebar.markdown("----")

    st.header("Welcome to your Personal Finance AI System")
    st.write("Navigate to the different sections using the sidebar on the left.")
    st.info("You can now upload new statements from the 'Upload Statement' page.")

    if st.sidebar.button('Logout'):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

if "user_id" in st.session_state:
    show_main_page()
else:
    show_login_page()