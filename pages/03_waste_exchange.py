import streamlit as st
from utils.database import get_db
from utils.ai_agents import get_ai_agents
from utils.notifications import get_notifications
from utils.config import get_config
from utils.langgraph_flows import get_langgraph_flows
from datetime import datetime
import pandas as pd

def display_waste_exchange():
    db = get_db()
    ai = get_ai_agents()
    notify = get_notifications()
    config = get_config()
    flows = get_langgraph_flows()

    st.title("Business to Business Waste Exchange")
    st.markdown("""
    ### Transform waste into resources that others can use
    """)

    if 'user_id' not in st.session_state or not st.session_state.user_id:
        st.warning("Please login to access waste exchange features")
        return

    user = db.get_collection(config.collections["users"]).find_one({"_id": st.session_state.user_id})
    if not user:
        st.error("User not found")
        return


    tab1, tab2 = st.tabs(["Offer Waste", "Find Waste"])

    with tab1:
        st.subheader("Offer Your Waste Materials")
        
        with st.form("waste_form"):
            waste_type = st.selectbox("Waste Type", options=config.waste_types)
            quantity = st.text_input("Quantity (e.g., 20 kg, 5 bags)")
            composition = st.text_area("Composition Details")
            location = st.text_input("Pickup Location")
            contact_phone = st.text_input("Your Phone Number", value=user.get("phone", ""))
            
            if st.form_submit_button("Submit Waste Offer"):
                waste_data = {
                    "supplier_id": st.session_state.user_id,
                    "type": waste_type,
                    "quantity": quantity,
                    "composition": composition,
                    "location": {"address": location},
                    "contact_phone": contact_phone,
                    "status": "available",
                    "created_at": datetime.now()
                }
                
                try:
                    waste_id = db.insert_document(config.collections["waste_materials"], waste_data)
                    
                  
                    waste_users = db.find_documents(config.collections["waste_users"], {}, 50)
                    
                    if waste_users:
                       #langgraph workflow used to match waste
                        result = flows.run_workflow("waste_exchange", {
                            "waste": waste_data,
                            "potential_users": waste_users
                        })
                        
                        if result and "match" in result:
                            best_match = result["match"]
                            db.update_document(config.collections["waste_materials"],
                                             {"_id": waste_id},
                                             {"receiver_id": best_match["user_id"],
                                              "status": "matched"})
                            
                            receiver = db.get_collection(config.collections["users"]).find_one(
                                {"_id": best_match["user_id"]})
                            
                            if receiver:
                               
                                notify_success = notify.notify_waste_exchange(
                                    supplier_phone=contact_phone,
                                    receiver_phone=receiver.get("phone", ""),
                                    waste_details=waste_data
                                )
                                
                                if notify_success:
                              
                                    db.get_collection(config.collections["social_impact"]).update_one(
                                        {"user_id": st.session_state.user_id},
                                        {"$inc": {
                                            "waste_reduced": float(quantity.split()[0]) if quantity.split()[0].isdigit() else 1,
                                            "co2_saved": 2,  # Estimate
                                            "score": 10
                                        }}
                                    )
                                    
                                    st.success(f"Waste matched with {receiver.get('name', 'business')}! Both parties have been notified via WhatsApp.")
                                else:
                                    st.warning("Waste matched but notifications failed to send")
                            else:
                                st.error("Matched receiver not found")
                        else:
                            st.success("Waste offer submitted! We'll notify you when we find a match.")
                    else:
                        st.warning("No potential users currently available. Your waste offer has been recorded.")
                except Exception as e:
                    st.error(f"Error processing waste offer: {str(e)}")

    with tab2:
        st.subheader("Find Waste You Can Use")
        
        wastes = db.find_documents(config.collections["waste_materials"],
                                 {"status": "available"}, 50)
        
        if wastes:
            for waste in wastes:
                with st.expander(f"{waste['type']} - {waste['quantity']}"):
                    st.write(f"**Composition:** {waste['composition']}")
                    st.write(f"**Location:** {waste['location']['address']}")
                    
                    if st.button("Request This Waste", key=f"request_{waste['_id']}"):
                        try:
                            db.update_document(config.collections["waste_materials"],
                                             {"_id": waste["_id"]},
                                             {"receiver_id": st.session_state.user_id,
                                              "status": "matched"})
                            
                          
                            notify_success = notify.send_whatsapp_message(
                                to=waste["contact_phone"],
                                message=f"""
                                 Waste Request Notification 
                                
                                Your waste material has been requested!
                                
                                Type: {waste['type']}
                                Quantity: {waste['quantity']}
                                
                                The requester will contact you shortly to arrange pickup.
                                """
                            )
                            
                            if notify_success:
                                st.success("Request sent! The supplier has been notified and will contact you.")
                            else:
                                st.warning("Request processed but notification failed to send")
                        except Exception as e:
                            st.error(f"Error processing request: {str(e)}")
        else:
            st.info("No available waste materials at this time. Please check back later.")

   
    st.subheader("Your Waste Exchange Activity")
    user_wastes = db.find_documents(config.collections["waste_materials"],
                                  {"$or": [
                                      {"supplier_id": st.session_state.user_id},
                                      {"receiver_id": st.session_state.user_id}
                                  ]}, 10)

    if user_wastes:
        st.dataframe(pd.DataFrame(user_wastes)[["type", "quantity", "status", "created_at"]])
    else:
        st.info("You haven't participated in any waste exchanges yet.")

if __name__ == "__main__":
    display_waste_exchange()