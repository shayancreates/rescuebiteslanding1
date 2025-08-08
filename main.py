import streamlit as st
from utils.database import get_db
from utils.ai_agents import get_ai_agents
from utils.notifications import get_notifications
from utils.config import get_config
from datetime import datetime
import pandas as pd
import plotly.express as px

db = get_db()
ai = get_ai_agents()
notify = get_notifications()
config = get_config()

if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'user_phone' not in st.session_state:
    st.session_state.user_phone = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = None
if 'user_role' not in st.session_state:
    st.session_state.user_role = None


st.markdown("""
    <style>
    .main {
        background-color: #f5f5f5;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        border: none;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    </style>
    """, unsafe_allow_html=True)


with st.sidebar:
    st.title("")
    st.markdown("""
    ### Sustainable Food Sharing
    """)
    
    if st.session_state.user_id:
        user = db.get_collection(config.collections["users"]).find_one({"_id": st.session_state.user_id})
        if user:
            st.markdown(f"Welcome, {user.get('name', 'User')}!")
            st.markdown(f"**Role:** {user.get('role', 'User').title()}")
            
            st.session_state.user_phone = user.get('phone', '')
            st.session_state.user_name = user.get('name', 'User')
            st.session_state.user_role = user.get('role', 'user')
            
            if st.button("Logout"):
                st.session_state.user_id = None
                st.session_state.user_phone = None
                st.session_state.user_name = None
                st.session_state.user_role = None
                st.rerun()
        else:
            st.session_state.user_id = None
            st.rerun()
    else:
        login_tab, register_tab = st.tabs(["Login", "Register"])
        
        with login_tab:
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            if st.button("Login"):
                user = db.get_collection(config.collections["users"]).find_one({
                    "email": email,
                    "password": password  
                })
                if user:
                    st.session_state.user_id = user["_id"]
                    st.session_state.user_phone = user.get('phone', '')
                    st.session_state.user_name = user.get('name', 'User')
                    st.session_state.user_role = user.get('role', 'user')
                    st.rerun()
                else:
                    st.error("Invalid credentials")
        
        with register_tab:
            name = st.text_input("Full Name", key="reg_name")
            email = st.text_input("Email", key="reg_email")
            phone = st.text_input("Phone Number", key="reg_phone")
            password = st.text_input("Password", type="password", key="reg_password")
            role = st.selectbox("Role", ["donor", "recipient", "delivery_partner", "supplier", "consumer"], key="reg_role")
            
            if st.button("Register"):
                existing_user = db.get_collection(config.collections["users"]).find_one({"email": email})
                if existing_user:
                    st.error("Email already registered")
                else:
                    user_data = {
                        "name": name,
                        "email": email,
                        "phone": phone,
                        "password": password,
                        "role": role,
                        "created_at": datetime.now()
                    }
                    user_id = db.insert_document(config.collections["users"], user_data)
                    st.session_state.user_id = user_id
                    st.session_state.user_phone = phone
                    st.session_state.user_name = name
                    st.session_state.user_role = role
                    st.rerun()


if st.session_state.user_id:
    user = db.get_collection(config.collections["users"]).find_one({"_id": st.session_state.user_id})
    if not user:
        st.session_state.user_id = None
        st.rerun()
    
    st.title("RescueBites")
    st.markdown("""
    Join our platform to connect surplus food with those who need it, while reducing environmental impact and building sustainable food systems. 
    Together, we can make a difference one meal at a time.
    """)
    


    
    if user["role"] == "donor":
        donations = db.find_documents(config.collections["food_donations"], {"donor_id": st.session_state.user_id})
        st.subheader("Your Recent Donations")
        if donations:
            df = pd.DataFrame(donations)
            st.dataframe(df[["type", "quantity", "status", "created_at"]])
    
    elif user["role"] == "recipient":
        received = db.find_documents(config.collections["food_donations"], {"recipient_id": st.session_state.user_id})
        st.subheader("Your Recent Receipts")
        if received:
            df = pd.DataFrame(received)
            st.dataframe(df[["type", "quantity", "donor_id", "created_at"]])
    
    impact = db.get_collection(config.collections["social_impact"]).find_one({"user_id": st.session_state.user_id})
    if impact:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Meals Provided", impact["meals_provided"])
        with col2:
            st.metric("CO₂ Saved (kg)", impact["co2_saved"])
        with col3:
            st.metric("Waste Reduced (kg)", impact["waste_reduced"])
else:
    st.title("RescueBites")
    st.markdown("""
    Join our platform to connect surplus food with those who need it, while reducing environmental impact and building sustainable food systems. 
    Together, we can make a difference one meal at a time.
    """)
    
 
    st.markdown("""
    ### How It Works:
    - **Donate surplus food** from businesses and individuals
    - **Receive nutritious meals** if you're in need
    - **Track your impact** on the environment and community
    - **Build sustainable** food systems together
    """)