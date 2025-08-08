from pymongo import MongoClient
from pymongo.server_api import ServerApi
import streamlit as st
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv
from utils.config import get_secret


load_dotenv()

class Database:
    def __init__(self):
        try:
            # mongodb_uri = os.getenv("MONGODB_URI")
            # mongodb_db = os.getenv("MONGODB_DATABASE")
           
            mongodb_uri = get_secret("MONGODB_URI")
            mongodb_db = get_secret("MONGODB_DATABASE")
            
            if not mongodb_uri or not mongodb_db:
                raise ValueError("MongoDB credentials not found in environment variables")
            
            self.client = MongoClient(
                mongodb_uri,
                server_api=ServerApi('1')
            )
            self.db = self.client[mongodb_db]
            
      
            self._initialize_collections()
            
        except Exception as e:
            st.error(f"Failed to connect to MongoDB: {str(e)}")
            raise

    def _initialize_collections(self):
        """Ensure all required collections exist with indexes"""
        collections = {
            "users": [
                ("email", 1),  
                ("phone", 1)   
            ],
            
            "food_donations": [
                ("donor_id", 1),
                ("status", 1),
                ("location.address", "text")
            ],
            "food_requests": [
                ("requester_id", 1),
                ("status", 1)
            ],
            "waste_materials": [
                ("supplier_id", 1),
                ("status", 1),
                ("type", 1)
            ],
            "waste_users": [
                ("user_id", 1),
                ("waste_types", 1)
            ],
            "hunger_hotspots": [
                ("time_period", 1),
                ("severity_index", 1)
            ],
            "micro_donations": [
                ("user_id", 1),
                ("created_at", -1)
            ],
            "local_champions": [
                ("user_id", 1),
                ("status", 1)
            ],
            "social_impact": [
                ("user_id", 1),
                ("score", -1)
            ],
            "food_donations": [
                ("donor_id", 1),
                ("recipient_id", 1),
                ("delivery_partner_id", 1),
                ("status", 1),
                ("delivery_status", 1),
                ("location.address", "text")
            ],
            "delivery_logs": [
                ("delivery_id", 1),
                ("partner_id", 1),
                ("status", 1),
                ("timestamp", -1)
            ],
            "notifications": [
                ("user_id", 1),
                ("created_at", -1)
            ],
            "meal_plans": [
                ("user_id", 1),
                ("created_at", -1)
            ],
            "local_produce": [
                ("name", "text"),
                ("supplier", 1)
            ],
            "orders": [
                ("user_id", 1),
                ("created_at", -1)
            ]
        }
        
        for collection_name, indexes in collections.items():
            if collection_name not in self.db.list_collection_names():
                self.db.create_collection(collection_name)
                for index in indexes:
                    self.db[collection_name].create_index([index])

    def get_collection(self, collection_name: str):
        return self.db[collection_name]
    
    def insert_document(self, collection_name: str, document: Dict[str, Any]) -> str:
        collection = self.get_collection(collection_name)
        document['created_at'] = datetime.now()
        result = collection.insert_one(document)
        return str(result.inserted_id)
    
    def find_documents(self, collection_name: str, query: Dict[str, Any] = {}, limit: int = 100) -> List[Dict[str, Any]]:
        collection = self.get_collection(collection_name)
        return list(collection.find(query).limit(limit))
    
    def update_document(self, collection_name: str, query: Dict[str, Any], update_data: Dict[str, Any]) -> int:
        collection = self.get_collection(collection_name)
        update_data['updated_at'] = datetime.now()
        result = collection.update_many(query, {'$set': update_data})
        return result.modified_count
    
    def delete_document(self, collection_name: str, query: Dict[str, Any]) -> int:
        collection = self.get_collection(collection_name)
        result = collection.delete_many(query)
        return result.deleted_count
    
    def aggregate(self, collection_name: str, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        collection = self.get_collection(collection_name)
        return list(collection.aggregate(pipeline))
    
    def get_dataframe(self, collection_name: str, query: Dict[str, Any] = {}, limit: int = 100) -> pd.DataFrame:
        data = self.find_documents(collection_name, query, limit)
        return pd.DataFrame(data)


@st.cache_resource
def get_db():
    return Database()