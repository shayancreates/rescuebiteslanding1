import streamlit as st
from utils.database import get_db
from utils.ai_agents import get_ai_agents
from utils.config import get_config
from datetime import datetime
import pandas as pd
import json
from bson import ObjectId


db = get_db()
ai = get_ai_agents()
config = get_config()


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return super().default(o)


st.title("Personalized Nutrition")
st.markdown("""
### Get AI powered meal plans based on your preferences and locally available produce
""")


if 'user_id' not in st.session_state or not st.session_state.user_id:
    st.warning("Please login to access personalized nutrition features")
    st.stop()


user = db.get_collection(config.collections["users"]).find_one({"_id": st.session_state.user_id})
if not user:
    st.error("User not found")
    st.stop()


if "dietary_preferences" not in user or "health_goals" not in user:
    st.warning("Please complete your profile to get personalized recommendations")
    
    with st.form("profile_form"):
        age = st.number_input("Age", min_value=1, max_value=120, value=user.get("age", 30))
        gender = st.selectbox("Gender", ["Male", "Female", "Other", "Prefer not to say"], 
                            index=0 if "gender" not in user else ["Male", "Female", "Other", "Prefer not to say"].index(user["gender"]))
        dietary_preferences = st.multiselect("Dietary Preferences", config.dietary_preferences,
                                           default=user.get("dietary_preferences", []))
        allergies = st.text_input("Allergies (comma separated)", value=", ".join(user.get("allergies", [])))
        health_goals = st.multiselect("Health Goals", config.health_goals,
                                     default=user.get("health_goals", []))
        activity_level = st.select_slider("Activity Level", 
                                         options=["Sedentary", "Lightly Active", "Moderately Active", "Very Active", "Extremely Active"],
                                         value=user.get("activity_level", "Moderately Active"))
        
        if st.form_submit_button("Save Profile"):
            update_data = {
                "age": age,
                "gender": gender,
                "dietary_preferences": dietary_preferences,
                "allergies": [a.strip() for a in allergies.split(",") if a.strip()],
                "health_goals": health_goals,
                "activity_level": activity_level,
                "updated_at": datetime.now()
            }
            db.update_document(config.collections["users"], {"_id": st.session_state.user_id}, update_data)
            st.success("Profile updated successfully!")
            st.rerun()
    st.stop()


local_produce = db.find_documents(config.collections["local_produce"], {}, 50)


st.subheader("Your Personalized Meal Plan")
if st.button("Generate New Meal Plan"):
    with st.spinner("Creating your personalized meal plan based on local availability..."):
        user_profile = {
            "age": user.get("age", 30),
            "gender": user.get("gender", "Prefer not to say"),
            "dietary_preferences": user.get("dietary_preferences", []),
            "allergies": user.get("allergies", []),
            "health_goals": user.get("health_goals", []),
            "activity_level": user.get("activity_level", "Moderately Active")
        }
        
       
        meal_plan = ai.generate_meal_plan(user_profile, local_produce)
        
        
        if isinstance(meal_plan, dict) and "error" in meal_plan:
            st.error(f"Failed to generate meal plan: {meal_plan.get('details', 'Unknown error')}")
            st.stop()
        
    
        meal_plan_id = db.insert_document(config.collections["meal_plans"], {
            "user_id": st.session_state.user_id,
            "plan": meal_plan,
            "local_produce_used": bool(local_produce),
            "created_at": datetime.now()
        })
        
        st.session_state.current_meal_plan = meal_plan
        st.session_state.current_meal_plan_id = meal_plan_id
        st.success("Meal plan generated successfully!")


if "current_meal_plan" not in st.session_state:
    latest_plan = db.get_collection(config.collections["meal_plans"]).find_one(
        {"user_id": st.session_state.user_id},
        sort=[("created_at", -1)]
    )
    if latest_plan:
        st.session_state.current_meal_plan = latest_plan["plan"]
        st.session_state.current_meal_plan_id = latest_plan["_id"]

if "current_meal_plan" in st.session_state:
    plan = st.session_state.current_meal_plan
    
   
    if isinstance(plan, str):
        try:
            plan = json.loads(plan)
        except json.JSONDecodeError:
            st.error("Failed to parse meal plan data. Please try generating a new plan.")
            st.stop()
    
  
    if not plan or not isinstance(plan, dict):
        st.info("Your generated meal plan is currently empty or invalid. Try generating a new one.")
    else:
      
        if "days" in plan or "week" in plan:
         
            days_data = plan.get("days", plan.get("week", {}))
            
            if not days_data:
                st.info("No meal plan data available for display.")
            else:
                days = st.selectbox("Select Day", options=list(days_data.keys()))
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.subheader("Breakfast")
                    if "breakfast" in days_data[days]:
                        meal = days_data[days]["breakfast"]
                        st.markdown(f"**{meal.get('name', 'Breakfast')}**")
                        st.write(meal.get("description", "No description available"))
                        st.markdown("**Ingredients:**")
                        for ing in meal.get("ingredients", []):
                            st.write(f"- {ing}")
                    else:
                        st.info("No breakfast planned for this day")
                
                with col2:
                    st.subheader("Lunch")
                    if "lunch" in days_data[days]:
                        meal = days_data[days]["lunch"]
                        st.markdown(f"**{meal.get('name', 'Lunch')}**")
                        st.write(meal.get("description", "No description available"))
                        st.markdown("**Ingredients:**")
                        for ing in meal.get("ingredients", []):
                            st.write(f"- {ing}")
                    else:
                        st.info("No lunch planned for this day")
                
                with col3:
                    st.subheader("Dinner")
                    if "dinner" in days_data[days]:
                        meal = days_data[days]["dinner"]
                        st.markdown(f"**{meal.get('name', 'Dinner')}**")
                        st.write(meal.get("description", "No description available"))
                        st.markdown("**Ingredients:**")
                        for ing in meal.get("ingredients", []):
                            st.write(f"- {ing}")
                    else:
                        st.info("No dinner planned for this day")
                
               
                if "nutritional_info" in days_data[days]:
                    st.subheader("Nutritional Information")
                    st.json(days_data[days]["nutritional_info"])
                elif "nutrition" in days_data[days].get("breakfast", {}):
                    st.subheader("Nutritional Information")
                    st.json({
                        "breakfast": days_data[days]["breakfast"].get("nutrition", {}),
                        "lunch": days_data[days].get("lunch", {}).get("nutrition", {}),
                        "dinner": days_data[days].get("dinner", {}).get("nutrition", {})
                    })
        
        
        if local_produce and ("shopping_list" in plan or any("ingredients" in day for day in plan.get("days", {}).values())):
            st.subheader("Source Ingredients Locally")
            local_options = []
            

            if "shopping_list" in plan:
                for item in plan["shopping_list"]:
                    for produce in local_produce:
                        if item.lower() in produce.get("name", "").lower():
                            local_options.append({
                                "ingredient": item,
                                "produce": produce["name"],
                                "supplier": produce["supplier"],
                                "price": produce.get("price", "N/A"),
                                "location": produce.get("location", {}).get("address", "N/A")
                            })
            else:
                for day in plan.get("days", {}).values():
                    for meal in ["breakfast", "lunch", "dinner"]:
                        if meal in day:
                            for ing in day[meal].get("ingredients", []):
                                for produce in local_produce:
                                    if ing.lower() in produce.get("name", "").lower():
                                        local_options.append({
                                            "ingredient": ing,
                                            "produce": produce["name"],
                                            "supplier": produce["supplier"],
                                            "price": produce.get("price", "N/A"),
                                            "location": produce.get("location", {}).get("address", "N/A")
                                        })
            
            if local_options:
                df = pd.DataFrame(local_options)
                st.dataframe(df)
                
                if st.button("Order Selected Ingredients"):
                    order_id = db.insert_document(config.collections["orders"], {
                        "user_id": st.session_state.user_id,
                        "items": local_options,
                        "status": "pending",
                        "created_at": datetime.now()
                    })
                    st.success("Order placed successfully! You'll receive a confirmation shortly.")
            else:
                st.info("No local sourcing options found for this meal plan")