import streamlit as st
from utils.database import get_db
from utils.notifications import get_notifications
from utils.config import get_config
import datetime

def display_local_champion():
    db = get_db()
    notify = get_notifications()
    config = get_config()

    st.title(" Local Champion Program")
    st.markdown("""
    ### Become a leader in your community's food sustainability efforts
    """)

    if 'user_id' not in st.session_state or not st.session_state.user_id:
        st.warning("Please login to access local champion features")
        return

    user = db.get_collection(config.collections["users"]).find_one({"_id": st.session_state.user_id})
    if not user:
        st.error("User not found")
        return

 
    is_champion = db.get_collection(config.collections["local_champions"]).find_one(
        {"user_id": st.session_state.user_id})

    if is_champion:
        st.success("You are already a Local Champion!")
        
    
        st.subheader("Champion Dashboard")
        
   
        champion_data = db.aggregate(config.collections["food_donations"], [
            {"$match": {"champion_id": st.session_state.user_id}},
            {"$group": {
                "_id": None,
                "total_donations": {"$sum": 1},
                "total_meals": {"$sum": {"$toInt": {"$arrayElemAt": [{"$split": ["$quantity", " "]}, 0]}}}
            }}
        ])
        
        if champion_data and len(champion_data) > 0:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Donations Facilitated", champion_data[0].get("total_donations", 0))
            with col2:
                st.metric("Estimated Meals Provided", champion_data[0].get("total_meals", 0))
        else:
            st.info("No champion activity yet")
        
      
        st.subheader("Champion Tools")
        
    
        pending_donations = db.find_documents(config.collections["food_donations"],
                                            {"status": "available",
                                             "location.address": {"$regex": user.get("location", "")}}, 10)
        
        if pending_donations:
            st.write("**Pending Donations in Your Area:**")
            for donation in pending_donations:
                st.write(f"- {donation['type']} ({donation['quantity']}) at {donation['location']['address']}")
        else:
            st.info("No pending donations in your area")
        

        with st.form("champion_action"):
            action = st.selectbox("What would you like to do?",
                                ["Organize pickup", "Coordinate distribution", "Recruit volunteers"])
            details = st.text_area("Details")
            
            if st.form_submit_button("Submit Action"):
                try:
                   
                    st.success(f"Action submitted: {action}. We'll notify relevant parties.")
                except Exception as e:
                    st.error(f"Error submitting action: {str(e)}")
        
   
        if st.button("Leave Champion Program"):
            try:
                db.delete_document(config.collections["local_champions"],
                                 {"user_id": st.session_state.user_id})
                st.success("You've left the Champion program. Thank you for your service!")
                st.rerun()
            except Exception as e:
                st.error(f"Error leaving program: {str(e)}")
    else:
        
        st.subheader("Become a Local Champion")
        st.write("""
        As a Local Champion, you'll help coordinate food redistribution efforts in your community.
        Responsibilities may include:
        - Connecting donors with recipients
        - Organizing pickup and delivery
        - Promoting the platform locally
        - Reporting on local needs
        """)
        
        with st.form("champion_application"):
            location = st.text_input("Your Neighborhood/City", value=user.get("location", ""))
            experience = st.text_area("Relevant Experience")
            availability = st.selectbox("Weekly Availability",
                                      ["1-5 hours", "5-10 hours", "10+ hours"])
            motivation = st.text_area("Why do you want to be a Local Champion?")
            
            if st.form_submit_button("Apply to Become Champion"):
                try:
                    application_data = {
                        "user_id": st.session_state.user_id,
                        "location": location,
                        "experience": experience,
                        "availability": availability,
                        "motivation": motivation,
                        "status": "pending",
                        "applied_at": datetime.datetime.now()
                    }
                    
                    db.insert_document(config.collections["local_champions"], application_data)
                    
                   
                    st.success("Application submitted! We'll review your application and get back to you soon.")
                    
                   
                    notify_success = notify.send_whatsapp_message(
                        to=user.get("phone", ""),
                        message=f"""
                        Local Champion Application Received 
                        
                        Thank you for applying to be a Local Champion!
                        
                        We'll review your application and get back to you soon.
                        
                        In the meantime, keep contributing to the platform to strengthen your application.
                        """
                    )
                    
                    if not notify_success:
                        st.warning("Application submitted but notification failed to send")
                except Exception as e:
                    st.error(f"Error submitting application: {str(e)}")

if __name__ == "__main__":
    display_local_champion()