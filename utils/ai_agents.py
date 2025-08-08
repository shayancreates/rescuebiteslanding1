import streamlit as st
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import Dict, Any, List, Optional
import json
from datetime import datetime
import os
from dotenv import load_dotenv
import logging
from bson import ObjectId
from utils.config import get_secret


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


load_dotenv()

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return super().default(o)

class AIAgents:
    def __init__(self):
        try:
            # google_api_key = os.getenv("GOOGLE_API_KEY")
            google_api_key = get_secret("GOOGLE_API_KEY")
            if not google_api_key:
                raise ValueError("Google API key not found in environment variables")
            
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=google_api_key,
                temperature=0.7
            )
        except Exception as e:
            st.error(f"Failed to initialize AI Agents: {e}")
            raise
        
    def _process_llm_response(self, response):
        """Process LLM response and handle JSON parsing."""
        try:
           
            if hasattr(response, 'content'):
                content = response.content
            else:
                content = str(response)
            
            logger.debug(f"Raw LLM response: {content}")
            
           
            try:
                if content.strip().startswith('{') or content.strip().startswith('['):
                    return json.loads(content)
                
             
                if '```json' in content:
                    json_str = content.split('```json')[1].split('```')[0].strip()
                    return json.loads(json_str)
                elif '```' in content:
                    json_str = content.split('```')[1].split('```')[0].strip()
                    if json_str.startswith('{') or json_str.startswith('['):
                        return json.loads(json_str)
                
             
                return {"response": content}
                
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON response: {e}")
                return {"response": content}
                
        except Exception as e:
            logger.error(f"Error processing LLM response: {e}")
            return {
                "error": "Failed to process AI response",
                "details": str(e),
                "raw_response": content[:500] + "..." if len(content) > 500 else content
            }
    def match_surplus_food(self, food_donation: Dict[str, Any], recipients: List[Dict[str, Any]]) -> Dict[str, Any]:
        system_prompt = """You are an AI that matches surplus food donations with organizations that can use them. 
        Analyze the food donation details and match it with the most suitable recipient based on their needs, 
        capacity, and location proximity."""
        
        user_prompt = f"""
        Food Donation Details:
        - Type: {food_donation.get('type', 'N/A')}
        - Quantity: {food_donation.get('quantity', 'N/A')}
        - Expiry Date: {food_donation.get('expiry_date', 'N/A')}
        - Location: {food_donation.get('location', {}).get('address', 'N/A')}
        - Special Requirements: {food_donation.get('special_requirements', 'None')}
        
        Potential Recipients:
        {json.dumps(recipients, indent=2)}
        
        Please select the best match and provide a justification for your choice.
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        response = self.llm.invoke(messages)
        return json.loads(response.content)
    
    def create_waste_exchange(self, waste_material: Dict[str, Any], potential_users: List[Dict[str, Any]]) -> Dict[str, Any]:
        system_prompt = """You are an AI that facilitates waste exchange between businesses. Analyze the waste material 
        and match it with businesses that can repurpose it. Provide details on how the waste can be transformed 
        and used by the receiving business."""
        
        user_prompt = f"""
        Waste Material Details:
        - Type: {waste_material.get('type', 'N/A')}
        - Quantity: {waste_material.get('quantity', 'N/A')}
        - Composition: {waste_material.get('composition', 'N/A')}
        - Location: {waste_material.get('location', {}).get('address', 'N/A')}
        
        Potential Users:
        {json.dumps(potential_users, indent=2)}
        
        Please select the best match and explain how the waste can be repurposed.
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        response = self.llm.invoke(messages)
        return json.loads(response.content)

    def generate_meal_plan(self, user_profile: Dict[str, Any], local_produce: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a personalized meal plan based on user profile and local produce."""
        try:
            system_prompt = """You are a nutritionist AI that creates personalized meal plans. Generate a 7-day meal plan 
            with breakfast, lunch, and dinner options that match the user's preferences and use locally available produce.
            
            Respond in valid JSON format with this structure:
            {
              "days": {
                "Monday": {
                  "breakfast": {
                    "name": "...",
                    "description": "...",
                    "ingredients": ["...", "..."],
                    "nutrition": {
                      "calories": ...,
                      "protein": ...,
                      "carbs": ...,
                      "fat": ...
                    }
                  },
                  "lunch": {...},
                  "dinner": {...}
                },
                // ... other days
              },
              "shopping_list": ["...", "..."],
              "nutritional_summary": {
                "weekly_calories": ...,
                "weekly_protein": ...,
                // ... other metrics
              }
            }
            """
            
            user_prompt = f"""
            User Profile:
            - Age: {user_profile.get('age', 'N/A')}
            - Gender: {user_profile.get('gender', 'N/A')}
            - Dietary Preferences: {', '.join(user_profile.get('dietary_preferences', []))}
            - Allergies: {', '.join(user_profile.get('allergies', []))}
            - Health Goals: {', '.join(user_profile.get('health_goals', []))}
            - Activity Level: {user_profile.get('activity_level', 'moderate')}
            
            Available Local Produce:
            {json.dumps(local_produce, indent=2, cls=JSONEncoder) if local_produce else "None available"}
            
            Create a detailed meal plan that:
            1. Matches the user's dietary needs and goals
            2. Uses locally available ingredients when possible
            3. Provides balanced nutrition
            4. Includes a shopping list
            5. Provides nutritional information for each meal
            """
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = self.llm.invoke(messages)
            processed_response = self._process_llm_response(response)
            
            if isinstance(processed_response, dict) and "error" in processed_response:
                raise Exception(processed_response["details"])
                
            return processed_response
            
        except Exception as e:
            logger.error(f"Error generating meal plan: {str(e)}")
            return {
                "error": "Failed to generate meal plan",
                "details": str(e)
            }
    def predict_hunger_hotspots(self, historical_data: List[Dict[str, Any]], current_data: Dict[str, Any]) -> Dict[str, Any]:
        system_prompt = """You are an AI that predicts areas at risk of food insecurity. Analyze the historical data 
        and current conditions to identify potential hunger hotspots. Consider factors like food supply, demand, 
        economic conditions, and seasonal patterns."""
        
        user_prompt = f"""
        Historical Data:
        {json.dumps(historical_data, indent=2)}
        
        Current Conditions:
        {json.dumps(current_data, indent=2)}
        
        Please identify potential hunger hotspots and predict the severity of food insecurity in each area.
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        response = self.llm.invoke(messages)
        return json.loads(response.content)

@st.cache_resource
def get_ai_agents():
    return AIAgents()