"""
MongoDB database connector for exercise data.
"""
from pymongo import MongoClient
from typing import Optional, Dict, Any
import os


class ExerciseDatabase:
    """Handles connection and queries to MongoDB exercise database."""
    
    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize database connection.
        
        Args:
            connection_string: MongoDB connection string. If None, uses local MongoDB.
        """
        # Use local MongoDB by default
        if connection_string is None:
            connection_string = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
        
        self.connection_string = connection_string
        self.client = MongoClient(self.connection_string)
        self.db = self.client.get_database("sweatsync")
        self.exercises_collection = self.db.get_collection("exercises")
    
    def search_exercise(
        self, 
        target_muscle: Optional[str] = None, 
        category: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Search for an exercise by target muscle and/or category.
        
        Args:
            target_muscle: Target muscle group (e.g., "chest", "back", "legs")
            category: Exercise category (e.g., "strength", "cardio", "flexibility")
        
        Returns:
            Dictionary containing exercise_id and name, or None if not found
        """
        query = {}
        
        if target_muscle:
            query["target_muscle"] = {"$regex": target_muscle, "$options": "i"}
        
        if category:
            query["category"] = {"$regex": category, "$options": "i"}
        
        # Find one matching exercise
        result = self.exercises_collection.find_one(query)
        
        if result:
            return {
                "exercise_id": str(result["_id"]),
                "name": result.get("name", "Unknown Exercise")
            }
        return None
    
    def close(self):
        """Close database connection."""
        if self.client:
            self.client.close()
