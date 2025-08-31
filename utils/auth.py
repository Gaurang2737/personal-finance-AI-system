import streamlit as st
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=['bcrypt'],deprecated='auto')

def hash_password_auth(password: str)-> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hash_password: str)-> bool:
    return pwd_context.verify(plain_password,hash_password)