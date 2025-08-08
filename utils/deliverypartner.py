# utils/deliverypartner.py
from datetime import datetime
import streamlit as st
from utils.database import get_db
from utils.notifications import get_notifications
from utils.config import get_config
import time

class DeliveryPartner:
    def __init__(self):
        self.db = get_db()
        self.notify = get_notifications()
        self.config = get_config()
        
    def get_available_deliveries(self):
        """Get all deliveries that need pickup"""
        return self.db.find_documents(
            self.config.collections["food_donations"],
            {"status": "matched", "delivery_status": {"$exists": False}},
            100
        )
    
    def get_my_deliveries(self, partner_id):
        """Get deliveries assigned to this partner"""
        return self.db.find_documents(
            self.config.collections["food_donations"],
            {"delivery_partner_id": partner_id},
            100
        )
    
    def confirm_pickup(self, delivery_id, partner_id):
        """Mark a delivery as picked up and notify recipient"""
        delivery = self.db.get_collection(
            self.config.collections["food_donations"]
        ).find_one({"_id": delivery_id})
        
        if not delivery:
            st.error("Delivery not found")
            return False
            
        
        update_result = self.db.update_document(
            self.config.collections["food_donations"],
            {"_id": delivery_id},
            {
                "delivery_partner_id": partner_id,
                "pickup_time": datetime.now(),
                "delivery_status": "pickup_confirmed",
                "delivery_start_time": datetime.now()
            }
        )
        
        if update_result > 0:
           
            self.db.insert_document(
                self.config.collections["delivery_logs"],
                {
                    "delivery_id": delivery_id,
                    "partner_id": partner_id,
                    "status": "pickup_confirmed",
                    "timestamp": datetime.now()
                }
            )
            
         
            recipient = self.db.get_collection(
                self.config.collections["users"]
            ).find_one({"_id": delivery["recipient_id"]})
            
            if recipient and "phone" in recipient:
                message = f"""
                Delivery Update - Pickup Confirmed
                
                Your food donation has been picked up by our delivery partner.
                
                Item: {delivery.get('type', 'N/A')}
                Quantity: {delivery.get('quantity', 'N/A')}
                
                Estimated delivery time: 30-60 minutes
                Delivery Partner Contact: {st.session_state.user_phone}
                
                Thank you for using our service!
                """
                return self.notify.send_whatsapp_message(
                    recipient["phone"],
                    message
                )
            return True
        return False
    
    def confirm_delivery(self, delivery_id):
        """Mark a delivery as completed and notify both parties"""
        delivery = self.db.get_collection(
            self.config.collections["food_donations"]
        ).find_one({"_id": delivery_id})
        
        if not delivery:
            st.error("Delivery not found")
            return False
            
       
        delivery_time = (datetime.now() - delivery["delivery_start_time"]).total_seconds() / 60
        
        
        update_result = self.db.update_document(
            self.config.collections["food_donations"],
            {"_id": delivery_id},
            {
                "delivery_status": "delivered",
                "delivery_end_time": datetime.now(),
                "delivery_duration_minutes": delivery_time
            }
        )
        
        if update_result > 0:
       
            self.db.insert_document(
                self.config.collections["delivery_logs"],
                {
                    "delivery_id": delivery_id,
                    "partner_id": st.session_state.user_id,
                    "status": "delivered",
                    "timestamp": datetime.now()
                }
            )
            
            
            donor = self.db.get_collection(
                self.config.collections["users"]
            ).find_one({"_id": delivery["donor_id"]})
            
            recipient = self.db.get_collection(
                self.config.collections["users"]
            ).find_one({"_id": delivery["recipient_id"]})
            
          
            success = True
            
            if recipient and "phone" in recipient:
                message = f"""
                Delivery Update - Completed
                
                Your food donation has been delivered!
                
                Item: {delivery.get('type', 'N/A')}
                Quantity: {delivery.get('quantity', 'N/A')}
                Delivery Time: {int(delivery_time)} minutes
                
                Thank you for using our service!
                """
                success &= self.notify.send_whatsapp_message(
                    recipient["phone"],
                    message
                )
                
            if donor and "phone" in donor:
                message = f"""
                Delivery Update - Completed
                
                Your food donation has been successfully delivered to the recipient!
                
                Item: {delivery.get('type', 'N/A')}
                Quantity: {delivery.get('quantity', 'N/A')}
                
                Thank you for your contribution!
                """
                success &= self.notify.send_whatsapp_message(
                    donor["phone"],
                    message
                )
                
            return success
        return False

@st.cache_resource
def get_delivery_partner():
    return DeliveryPartner()