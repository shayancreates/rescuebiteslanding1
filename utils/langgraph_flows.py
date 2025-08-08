from langgraph.graph import StateGraph
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from typing import Dict, Any, List
import json
from utils.ai_agents import get_ai_agents
import streamlit as st

ai = get_ai_agents()

class LangGraphFlows:
    def __init__(self):
        self.workflows = {
            "meal_planning": self._create_meal_planning_workflow(),
            "food_redistribution": self._create_food_redistribution_workflow(),
            "waste_exchange": self._create_waste_exchange_workflow(),
            "impact_calculation": self._create_impact_calculation_workflow()
        }
    
    def _create_meal_planning_workflow(self):
        workflow = StateGraph(dict)  
        
   
        def get_user_profile(state: Dict[str, Any]) -> Dict[str, Any]:
            return {"user_profile": state["user_profile"]}
        
        def get_local_produce(state: Dict[str, Any]) -> Dict[str, Any]:
            return {"local_produce": state["local_produce"]}
        
        def generate_meal_plan(state: Dict[str, Any]) -> Dict[str, Any]:
            user_profile = state["user_profile"]
            local_produce = state["local_produce"]
            meal_plan = ai.generate_meal_plan(user_profile, local_produce)
            return {"meal_plan": meal_plan}
        
        def format_output(state: Dict[str, Any]) -> Dict[str, Any]:
            return {"output": state["meal_plan"]}
        
        
        workflow.add_node("get_user_profile", get_user_profile)
        workflow.add_node("get_local_produce", get_local_produce)
        workflow.add_node("generate_meal_plan", generate_meal_plan)
        workflow.add_node("format_output", format_output)
        
       
        workflow.add_edge("get_user_profile", "generate_meal_plan")
        workflow.add_edge("get_local_produce", "generate_meal_plan")
        workflow.add_edge("generate_meal_plan", "format_output")
        
      
        workflow.set_entry_point("get_user_profile")
        workflow.set_finish_point("format_output")
        
        return workflow.compile()
    
    def _create_food_redistribution_workflow(self):
        workflow = StateGraph(dict)  
        
        def analyze_donation(state: Dict[str, Any]) -> Dict[str, Any]:
            return {"donation": state["donation"]}
        
        def get_recipients(state: Dict[str, Any]) -> Dict[str, Any]:
            return {"recipients": state["recipients"]}
        
        def match_donation(state: Dict[str, Any]) -> Dict[str, Any]:
            donation = state["donation"]
            recipients = state["recipients"]
            match = ai.match_surplus_food(donation, recipients)
            return {"match": match}
        
        def notify_parties(state: Dict[str, Any]) -> Dict[str, Any]:
            return {"notification_sent": True}
        
        workflow.add_node("analyze_donation", analyze_donation)
        workflow.add_node("get_recipients", get_recipients)
        workflow.add_node("match_donation", match_donation)
        workflow.add_node("notify_parties", notify_parties)
        
        workflow.add_edge("analyze_donation", "match_donation")
        workflow.add_edge("get_recipients", "match_donation")
        workflow.add_edge("match_donation", "notify_parties")
        
        workflow.set_entry_point("analyze_donation")
        workflow.set_finish_point("notify_parties")
        
        return workflow.compile()
    
    def _create_waste_exchange_workflow(self):
        workflow = StateGraph(dict)  
        
        def analyze_waste(state: Dict[str, Any]) -> Dict[str, Any]:
            return {"waste": state["waste"]}
        
        def get_potential_users(state: Dict[str, Any]) -> Dict[str, Any]:
            return {"potential_users": state["potential_users"]}
        
        def match_waste(state: Dict[str, Any]) -> Dict[str, Any]:
            waste = state["waste"]
            users = state["potential_users"]
            match = ai.create_waste_exchange(waste, users)
            return {"match": match}
        
        def notify_parties(state: Dict[str, Any]) -> Dict[str, Any]:
            return {"notification_sent": True}
        
        workflow.add_node("analyze_waste", analyze_waste)
        workflow.add_node("get_potential_users", get_potential_users)
        workflow.add_node("match_waste", match_waste)
        workflow.add_node("notify_parties", notify_parties)
        
        workflow.add_edge("analyze_waste", "match_waste")
        workflow.add_edge("get_potential_users", "match_waste")
        workflow.add_edge("match_waste", "notify_parties")
        
        workflow.set_entry_point("analyze_waste")
        workflow.set_finish_point("notify_parties")
        
        return workflow.compile()
    
    def _create_impact_calculation_workflow(self):
        workflow = StateGraph(dict)  
        
        def get_food_items(state: Dict[str, Any]) -> Dict[str, Any]:
            return {"food_items": state["food_items"]}
        
        def calculate_nutrition(state: Dict[str, Any]) -> Dict[str, Any]:
            food_items = state["food_items"]
            nutrition = ai.calculate_nutritional_impact(food_items)
            return {"nutrition": nutrition}
        
        def calculate_environmental(state: Dict[str, Any]) -> Dict[str, Any]:
            food_items = state["food_items"]

            co2_saved = len(food_items) * 0.5  # 0.5kg CO2 per item saved
            waste_reduced = len(food_items) * 0.3  # 0.3kg waste reduced per item
            return {"co2_saved": co2_saved, "waste_reduced": waste_reduced}
        
        def combine_results(state: Dict[str, Any]) -> Dict[str, Any]:
            return {
                "nutritional_impact": state["nutrition"],
                "environmental_impact": {
                    "co2_saved": state["co2_saved"],
                    "waste_reduced": state["waste_reduced"]
                }
            }
        
        workflow.add_node("get_food_items", get_food_items)
        workflow.add_node("calculate_nutrition", calculate_nutrition)
        workflow.add_node("calculate_environmental", calculate_environmental)
        workflow.add_node("combine_results", combine_results)
        
        workflow.add_edge("get_food_items", "calculate_nutrition")
        workflow.add_edge("get_food_items", "calculate_environmental")
        workflow.add_edge("calculate_nutrition", "combine_results")
        workflow.add_edge("calculate_environmental", "combine_results")
        
        workflow.set_entry_point("get_food_items")
        workflow.set_finish_point("combine_results")
        
        return workflow.compile()
    
    def run_workflow(self, workflow_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        if workflow_name not in self.workflows:
            raise ValueError(f"Unknown workflow: {workflow_name}")
        
        workflow = self.workflows[workflow_name]
        return workflow.invoke(input_data)

@st.cache_resource
def get_langgraph_flows():
    return LangGraphFlows()