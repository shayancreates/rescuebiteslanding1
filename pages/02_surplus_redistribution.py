import streamlit as st
from utils.database import get_db
from utils.ai_agents import get_ai_agents
from utils.notifications import get_notifications
from utils.config import get_config
from utils.langgraph_flows import get_langgraph_flows
from utils.deliverypartner import get_delivery_partner
from datetime import datetime
import pandas as pd
import json


db = get_db()
ai = get_ai_agents()
notify = get_notifications()
config = get_config()
flows = get_langgraph_flows()
delivery = get_delivery_partner()

st.title("Surplus Food Redistribution")
st.markdown("""
### Connect food donors with organizations that can use their surplus
""")


if 'user_id' not in st.session_state or not st.session_state.user_id:
    st.warning("Please login to access surplus redistribution features")
    st.stop()

user = db.get_collection(config.collections["users"]).find_one({"_id": st.session_state.user_id})
if not user:
    st.error("User not found")
    st.stop()


if user["role"] == "donor":
    st.subheader("Donate Surplus Food")
    
    with st.form("donation_form"):
        food_type = st.selectbox("Food Type", options=config.food_types)
        quantity = st.text_input("Quantity (e.g., 5 kg, 10 boxes)")
        expiry_date = st.date_input("Expiry Date", min_value=datetime.today())
        location = st.text_input("Pickup Location")
        special_requirements = st.text_area("Special Requirements (storage, handling, etc.)")
        donor_phone = st.text_input("Your Phone Number for Coordination", value=user.get("phone", ""))
        
        if st.form_submit_button("Submit Donation"):
            donation_data = {
                "donor_id": st.session_state.user_id,
                "type": food_type,
                "quantity": quantity,
                "expiry_date": expiry_date.strftime("%Y-%m-%d"),
                "location": {"address": location},
                "special_requirements": special_requirements,
                "donor_phone": donor_phone,
                "status": "available",
                "created_at": datetime.now()
            }
            
            donation_id = db.insert_document(config.collections["food_donations"], donation_data)
            
            
            recipients = db.find_documents(config.collections["recipients"], {}, 50)
            
            if recipients:
               
                result = flows.run_workflow("food_redistribution", {
                    "donation": donation_data,
                    "recipients": recipients
                })
                
                if "match" in result:
                    best_match = result["match"]
                    db.update_document(config.collections["food_donations"], 
                                     {"_id": donation_id},
                                     {"recipient_id": best_match["recipient_id"],
                                      "status": "matched"})
                    
                    recipient = db.get_collection(config.collections["recipients"]).find_one(
                        {"_id": best_match["recipient_id"]})
                    
                    if recipient:
                        
                        notify.notify_food_match(
                            donor_phone=donor_phone,
                            recipient_phone=recipient.get("phone", ""),
                            food_details=donation_data
                        )
                        
                       
                        db.get_collection(config.collections["social_impact"]).update_one(
                            {"user_id": st.session_state.user_id},
                            {"$inc": {
                                "meals_provided": 10,  
                                "co2_saved": 5,  
                                "waste_reduced": 3,  
                                "score": 15
                            }}
                        )
                        
                        st.success(f"Donation matched with {recipient.get('name', 'recipient')}! Both parties have been notified via WhatsApp.")
                    else:
                        st.error("Matched recipient not found")
                else:
                    st.success("Donation submitted! We'll notify you when we find a match.")
            else:
                st.warning("No recipients currently available. Your donation has been recorded and we'll notify you when a match is found.")

elif user["role"] == "recipient":
    st.subheader("Available Food Donations")
    
    donations = db.find_documents(config.collections["food_donations"], 
                                {"status": "available"}, 50)
    
    if donations:
        for donation in donations:
            with st.expander(f"{donation['type']} - {donation['quantity']}"):
                st.write(f"**Expiry:** {donation['expiry_date']}")
                st.write(f"**Location:** {donation['location']['address']}")
                st.write(f"**Special Requirements:** {donation.get('special_requirements', 'None')}")
                
                if st.button("Request This Donation", key=f"request_{donation['_id']}"):
                    db.update_document(config.collections["food_donations"],
                                     {"_id": donation["_id"]},
                                     {"recipient_id": st.session_state.user_id,
                                      "status": "matched"})
                    
                    
                    notify.send_whatsapp_message(
                        to=donation["donor_phone"],
                        message=f"""
                         Food Request Notification 
                        
                        Your donation has been requested!
                        
                        Item: {donation['type']}
                        Quantity: {donation['quantity']}
                        
                        The recipient will contact you shortly to arrange pickup.
                        """
                    )
                    
                    st.success("Request sent! The donor has been notified and will contact you to arrange pickup.")
    else:
        st.info("No available donations at this time. Please check back later.")

elif user["role"] == "delivery_partner":
    st.subheader("Delivery Partner Dashboard")
    
    tab1, tab2 = st.tabs(["Available Deliveries", "My Deliveries"])
    
    with tab1:
        st.markdown("### Available Pickups")
        available_deliveries = delivery.get_available_deliveries()
        
        if available_deliveries:
            for delivery_item in available_deliveries:
                with st.expander(f"{delivery_item['type']} - {delivery_item['quantity']}"):
                    st.write(f"**From:** {delivery_item['location']['address']}")
                    
                    donor = db.get_collection(config.collections["users"]).find_one(
                        {"_id": delivery_item["donor_id"]})
                    st.write(f"**Donor:** {donor.get('name', 'N/A')}")
                    st.write(f"**Donor Phone:** {donor.get('phone', 'N/A')}")
                    
                    recipient = db.get_collection(config.collections["users"]).find_one(
                        {"_id": delivery_item["recipient_id"]})
                    st.write(f"**Recipient:** {recipient.get('name', 'N/A')}")
                    st.write(f"**Recipient Address:** {recipient.get('address', 'N/A')}")
                    st.write(f"**Recipient Phone:** {recipient.get('phone', 'N/A')}")
                    
                    if st.button("Confirm Pickup", key=f"pickup_{delivery_item['_id']}"):
                        if delivery.confirm_pickup(delivery_item["_id"], st.session_state.user_id):
                            st.success("Pickup confirmed! Recipient has been notified.")
                            st.rerun()
                        else:
                            st.error("Failed to confirm pickup")
        else:
            st.info("No available deliveries at this time")
    
    with tab2:
        st.markdown("### My Active Deliveries")
        my_deliveries = delivery.get_my_deliveries(st.session_state.user_id)
        
        if my_deliveries:
            for delivery_item in my_deliveries:
                with st.expander(f"{delivery_item['type']} - {delivery_item['quantity']}"):
                    status = delivery_item.get("delivery_status", "pending")
                    st.write(f"**Status:** {status.capitalize()}")
                    
                    if "pickup_time" in delivery_item:
                        st.write(f"**Pickup Time:** {delivery_item['pickup_time'].strftime('%Y-%m-%d %H:%M')}")
                    
                    if status == "pickup_confirmed":
                       
                        time_elapsed = (datetime.now() - delivery_item["delivery_start_time"]).total_seconds() / 60
                        st.write(f"**Time in Transit:** {int(time_elapsed)} minutes")
                        
                        if st.button("Mark as Delivered", key=f"deliver_{delivery_item['_id']}"):
                            if delivery.confirm_delivery(delivery_item["_id"]):
                                st.success("Delivery confirmed! Both parties have been notified.")
                                st.rerun()
                            else:
                                st.error("Failed to confirm delivery")
        else:
            st.info("You don't have any active deliveries")


st.subheader("Your Activity")
if user["role"] == "donor":
    user_donations = db.find_documents(config.collections["food_donations"],
                                     {"donor_id": st.session_state.user_id}, 10)
    if user_donations:
        st.dataframe(pd.DataFrame(user_donations)[["type", "quantity", "status", "created_at"]])
    else:
        st.info("You haven't made any donations yet.")
elif user["role"] == "recipient":
    user_requests = db.find_documents(config.collections["food_donations"],
                                    {"recipient_id": st.session_state.user_id}, 10)
    if user_requests:
        st.dataframe(pd.DataFrame(user_requests)[["type", "quantity", "status", "created_at"]])
    else:
        st.info("You haven't requested any donations yet.")
elif user["role"] == "delivery_partner":
    delivery_logs = db.find_documents(
        config.collections["delivery_logs"],
        {"partner_id": st.session_state.user_id},
        10
    )
    
    if delivery_logs:
       
        for log in delivery_logs:
            log["_id"] = str(log["_id"])
            log["delivery_id"] = str(log["delivery_id"])
        
        st.dataframe(pd.DataFrame(delivery_logs)[["delivery_id", "status", "timestamp"]])
    else:
        st.info("You haven't completed any deliveries yet")


if user["role"] == "delivery_partner":
    st.subheader("Delivery Performance")
    
    # Get all completed deliveries
    completed_deliveries = db.find_documents(
        config.collections["delivery_logs"],
        {"partner_id": st.session_state.user_id, "status": "delivered"},
        100
    )
    
    if completed_deliveries:
     
        delivery_data = []
        for delivery_log in completed_deliveries:
            delivery = db.get_collection(config.collections["food_donations"]).find_one(
                {"_id": delivery_log["delivery_id"]})
            if delivery and "delivery_duration_minutes" in delivery:
                delivery_data.append({
                    "date": delivery_log["timestamp"].strftime("%Y-%m-%d"),
                    "duration": delivery["delivery_duration_minutes"],
                    "type": delivery["type"],
                    "quantity": delivery["quantity"]
                })
        
        if delivery_data:
            df = pd.DataFrame(delivery_data)
            
         
            avg_time = df["duration"].mean()
            st.metric("Average Delivery Time", f"{avg_time:.1f} minutes")
            
            
            st.line_chart(df.set_index("date")["duration"])
    else:
        st.info("No delivery performance data available yet")