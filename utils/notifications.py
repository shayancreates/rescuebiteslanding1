from twilio.rest import Client
import streamlit as st
from typing import Dict, Any
import os
from dotenv import load_dotenv
import time
from utils.config import get_secret

load_dotenv()

class Notifications:
    def __init__(self):
        try:
            # account_sid = os.getenv("TWILIO_ACCOUNT_SID")
            # auth_token = os.getenv("TWILIO_AUTH_TOKEN")
            # whatsapp_number = os.getenv("TWILIO_WHATSAPP_NUMBER")
            account_sid = get_secret("TWILIO_ACCOUNT_SID")
            auth_token = get_secret("TWILIO_AUTH_TOKEN")
            whatsapp_number = get_secret("TWILIO_WHATSAPP_NUMBER")
            
            if not all([account_sid, auth_token, whatsapp_number]):
                raise ValueError("Missing Twilio credentials in environment variables")
            
            self.client = Client(account_sid, auth_token)
            self.whatsapp_number = whatsapp_number
            self.max_retries = 3
            self.retry_delay = 1  
        except Exception as e:
            st.error(f"Failed to initialize Twilio client: {e}")
            raise
        
    def _send_with_retry(self, to: str, message: str) -> bool:
        """Helper method to handle retries for sending messages"""
        for attempt in range(self.max_retries):
            try:
                self.client.messages.create(
                    body=message,
                    from_=f"whatsapp:{self.whatsapp_number}",
                    to=f"whatsapp:{to}"
                )
                return True
            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                st.error(f"Failed to send WhatsApp message after {self.max_retries} attempts: {e}")
                return False
    
    def send_whatsapp_message(self, to: str, message: str) -> bool:
        """Send a WhatsApp message with proper formatting"""
        try:
            
            if not to.startswith("+"):
                to = f"+{to.lstrip('0')}"
                
          
            message = message.strip()
            if len(message) > 1600:
                message = message[:1597] + "..."
                
            return self._send_with_retry(to, message)
        except Exception as e:
            st.error(f"Error preparing WhatsApp message: {e}")
            return False
    
    def notify_food_match(self, donor_phone: str, recipient_phone: str, food_details: Dict[str, Any]) -> bool:
        try:
            donor_message = f"""
             Food Match Notification 
            
            Your food donation has been matched!
            
            Item: {food_details.get('type', 'N/A')}
            Quantity: {food_details.get('quantity', 'N/A')}
            
            The recipient will contact you shortly to arrange pickup.
            Thank you for reducing food waste!
            """
            
            recipient_message = f"""
             Food Availability Notification 
            
            A food donation matching your needs is available!
            
            Item: {food_details.get('type', 'N/A')}
            Quantity: {food_details.get('quantity', 'N/A')}
            Expiry: {food_details.get('expiry_date', 'N/A')}
            Location: {food_details.get('location', {}).get('address', 'N/A')}
            
            Please contact the donor to arrange pickup.
            """
            
            donor_success = self.send_whatsapp_message(donor_phone, donor_message)
            recipient_success = self.send_whatsapp_message(recipient_phone, recipient_message)
            
            return donor_success and recipient_success
        except Exception as e:
            st.error(f"Error in food match notification: {e}")
            return False
    
    def notify_waste_exchange(self, supplier_phone: str, receiver_phone: str, waste_details: Dict[str, Any]) -> bool:
        try:
            supplier_message = f"""
             Waste Exchange Notification 
            
            Your waste material has found a new purpose!
            
            Type: {waste_details.get('type', 'N/A')}
            Quantity: {waste_details.get('quantity', 'N/A')}
            
            The receiving business will contact you shortly.
            Thank you for participating in circular economy!
            """
            
            receiver_message = f"""
             Waste Availability Notification 
            
            A waste material you can repurpose is available!
            
            Type: {waste_details.get('type', 'N/A')}
            Quantity: {waste_details.get('quantity', 'N/A')}
            Location: {waste_details.get('location', {}).get('address', 'N/A')}
            
            Please contact the supplier to arrange pickup.
            """
            
            supplier_success = self.send_whatsapp_message(supplier_phone, supplier_message)
            receiver_success = self.send_whatsapp_message(receiver_phone, receiver_message)
            
            return supplier_success and receiver_success
        except Exception as e:
            st.error(f"Error in waste exchange notification: {e}")
            return False
    
    def notify_social_impact(self, phone: str, impact_data: Dict[str, Any]) -> bool:
        try:
            message = f"""
             Social Impact Update 
            
            Your recent activities have made a difference!
            
            Meals Provided: {impact_data.get('meals_provided', 0)}
            CO2 Saved: {impact_data.get('co2_saved', 0)} kg
            Waste Reduced: {impact_data.get('waste_reduced', 0)} kg
            
            Thank you for contributing to a sustainable future!
            """
            return self.send_whatsapp_message(phone, message)
        except Exception as e:
            st.error(f"Error in social impact notification: {e}")
            return False
    
    def notify_delivery_update(self, phone: str, delivery_details: Dict[str, Any], status: str) -> bool:
        try:
            if status == "pickup_confirmed":
                message = f"""
                 Delivery Update - Pickup Confirmed
                
                Your food donation has been picked up by our delivery partner.
                
                Item: {delivery_details.get('type', 'N/A')}
                Quantity: {delivery_details.get('quantity', 'N/A')}
                
                Estimated delivery time: 30-60 minutes
                Delivery Partner Contact: {delivery_details.get('partner_phone', 'N/A')}
                
                Thank you for using our service!
                """
            elif status == "delivered":
                message = f"""
                 Delivery Update - Completed
                
                Your food donation has been {'delivered to recipient' if delivery_details.get('is_recipient') else 'received'}!
                
                Item: {delivery_details.get('type', 'N/A')}
                Quantity: {delivery_details.get('quantity', 'N/A')}
                Delivery Time: {delivery_details.get('delivery_time', 'N/A')} minutes
                
                Thank you for {'using' if delivery_details.get('is_recipient') else 'contributing to'} our service!
                """
            else:
                return False
                
            return self.send_whatsapp_message(phone, message)
        except Exception as e:
            st.error(f"Error in delivery notification: {e}")
            return False

@st.cache_resource
def get_notifications():
    return Notifications()