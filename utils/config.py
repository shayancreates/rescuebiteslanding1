import streamlit as st
import os

class Config:
    def __init__(self):
        self.collections = {
            "users": "users",
            "suppliers": "suppliers",
            "recipients": "recipients",
            "food_requests": "food_requests",
            "food_donations": "food_donations",
            "waste_materials": "waste_materials",
            "waste_users": "waste_users",
            "meal_plans": "meal_plans",
            "local_produce": "local_produce",
            "nutritional_impact": "nutritional_impact",
            "social_impact": "social_impact",
            "hunger_hotspots": "hunger_hotspots",
            "micro_donations": "micro_donations",
            "local_champions": "local_champions",
            "delivery_partners": "delivery_partners",
            "delivery_logs": "delivery_logs"
        }
        self.roles = [
            "donor",
            "recipient",
            "delivery_partner",
            "admin"
        ]
        
       
        self.delivery_statuses = [
            "requested",
            "pickup_confirmed",
            "in_transit",
            "delivered",
            "cancelled"
        ]
        self.food_types = [
            "Fruits", "Vegetables", "Grains", "Dairy", "Meat", 
            "Poultry", "Fish", "Baked Goods", "Prepared Meals", "Other"
        ]
        
        self.waste_types = [
            "Vegetable Scraps", "Fruit Pulp", "Coffee Grounds", 
            "Eggshells", "Bread Crusts", "Other Organic", "Other"
        ]
        
        self.dietary_preferences = [
               "Vegetarian",
            "Vegan",
            "Pescatarian",
            "Gluten-Free",
            "Dairy-Free",
            "Nut-Free",
            "Keto",
            "Paleo",
            "Low-Carb",
            "Low-Fat",
            "Halal",
            "Kosher",
            "Other"
        ]
        
        self.health_goals = [
             "Weight Loss",
            "Weight Gain",
            "Muscle Building",
            "Diabetes Management",
            "Heart Health",
            "General Wellness",
            "Improved Digestion",
            "Better Sleep",
            "Increased Energy",
            "Stress Reduction"
        ]

def get_secret(key):
    try:
        return st.secrets[key]  # Works in Streamlit context
    except:
        return os.getenv(key)
@st.cache_resource
def get_config():
    return Config()