from services.mongodb_connection import MongoDBManager
from openai import AzureOpenAI
import os
from dotenv import load_dotenv
from typing import List, Optional, Dict, Any
from utils import cache_config
from utils.prompt_config import get_keyword_extraction_prompt
from models.models import ConfigModel

load_dotenv()

db_manager = MongoDBManager()

chat_collection = db_manager.get_collection("chats")
analysis_collection = db_manager.get_collection("analyses")
config_collection = db_manager.get_collection("config")

try:
    client = AzureOpenAI(
    api_key=os.getenv("API_KEY"),
    api_version=os.getenv("OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("API_BASE")
)
except Exception as e:
    raise RuntimeError(f"Erreur lors de l'initialisation du client Azure OpenAI : {e}")

def get_statistics():
    total_users = chat_collection.count_documents({})
    total_completed_sessions = chat_collection.count_documents({"final_idea": {"$exists": True}})
    total_abandoned_sessions = total_users - total_completed_sessions
    reengagement_pipeline = [
        {"$match": {"time_stats.user_returned_after_30mins": True}}, 
        {"$group": {"_id": None, "num_reengagements": {"$sum": 1}}}  
    ]
    reengagement_result = list(analysis_collection.aggregate(reengagement_pipeline))
    num_reengagements = reengagement_result[0].get("num_reengagements", 0) if reengagement_result else 0
    session_duration_pipeline = [
        {"$match": {"time_stats.total_duration_minutes": {"$exists": True}}},
        {"$group": {"_id": None, "avg_session_duration": {"$avg": "$time_stats.total_duration_minutes"}}}
    ]
    session_duration_result = list(analysis_collection.aggregate(session_duration_pipeline))
    avg_session_duration = round(session_duration_result[0].get("avg_session_duration", 0.00), 2) if session_duration_result else 0.00

    return {
        "total_users": total_users,
        "total_completed_sessions": total_completed_sessions,
        "total_abandoned_sessions": total_abandoned_sessions,
        "num_reengagements": num_reengagements,  
        "avg_session_duration": avg_session_duration  
    }

def extract_keywords(texts):
    """
    Uses GPT-4o-mini to extract the most relevant themes and their frequencies as a Python dictionary.
    """

    prompt = get_keyword_extraction_prompt(texts)

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert in semantic keyword extraction and frequency analysis."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )

        raw_response = response.choices[0].message.content

        cleaned_response = raw_response.strip().replace("```python", "").replace("```", "").strip()

        theme_frequencies = eval(cleaned_response) if cleaned_response.startswith("{") and cleaned_response.endswith("}") else {}

        return [{"_id": theme, "count": round(freq, 2)} for theme, freq in theme_frequencies.items()]

    except Exception as e:
        return []

def get_diagram_data():

    score_pipeline = [
        {
            "$group": {
                "_id": None,
                "avg_ai_score": {"$avg": "$assistant_influence_score"},
                "avg_originality": {"$avg": "$originality_score"},
                "avg_matching_score": {"$avg": "$matching_score"}
            }
        }
    ]
    score_result = list(analysis_collection.aggregate(score_pipeline))
    avg_ai_score = round(score_result[0]["avg_ai_score"], 2) if score_result else 0.00
    avg_originality = round(score_result[0]["avg_originality"], 2) if score_result else 0.00
    avg_matching_score = round(score_result[0]["avg_matching_score"], 2) if score_result else 0.00 

    size_pipeline = [
        {
            "$group": {
                "_id": None,
                "avg_user_msg_size": {"$avg": "$size_stats.avg_user_size"},
                "avg_ai_msg_size": {"$avg": "$size_stats.avg_ai_size"}
            }
        }
    ]
    size_result = list(analysis_collection.aggregate(size_pipeline))
    avg_user_msg_size = round(size_result[0]["avg_user_msg_size"], 2) if size_result else 0.00
    avg_ai_msg_size = round(size_result[0]["avg_ai_msg_size"], 2) if size_result else 0.00

    heatmap_pipeline = [
        {
            "$project": {
                "originality_bucket": {
                    "$switch": {
                        "branches": [
                            {"case": {"$lt": ["$originality_score", 25]}, "then": "0-25"},
                            {"case": {"$lt": ["$originality_score", 50]}, "then": "25-50"},
                            {"case": {"$lt": ["$originality_score", 75]}, "then": "50-75"},
                            {"case": {"$lte": ["$originality_score", 100]}, "then": "75-100"}
                        ],
                        "default": "Unknown"
                    }
                },
                "total_messages": "$time_stats.total_messages"
            }
        },
        {
            "$group": {
                "_id": "$originality_bucket",
                "avg_messages": {"$avg": "$total_messages"} 
            }
        },
        {
            "$sort": {"_id": 1}
        }
    ]
    heatmap_result = list(analysis_collection.aggregate(heatmap_pipeline))

    final_ideas = list(analysis_collection.find({"final_idea": {"$exists": True, "$ne": None}}, {"final_idea": 1}))

    all_texts = [doc["final_idea"] for doc in final_ideas]

    theme_result = extract_keywords(all_texts)
    return {
        "avg_ai_score": avg_ai_score,
        "avg_matching":avg_matching_score,
        "avg_originality": avg_originality,
        "avg_user_msg_size": avg_user_msg_size,
        "avg_ai_msg_size": avg_ai_msg_size,
        "heatmap_data": heatmap_result,
        "theme_distribution": theme_result
    }

def get_analysis_data(start_date=None, end_date=None):
    """
    Retrieve analysis data from MongoDB, with optional filtering by date.
    """
    query = {}
    if start_date and end_date:
        query["created_at"] = {"$gte": start_date, "$lte": end_date}

    analysis_data = list(analysis_collection.find(query, {
        "_id": 0,
        "session_id": 1, 
        "prolific_id":1,
        "time_stats.total_messages": 1, 
        "time_stats.total_duration_minutes": 1,
        "created_at": 1, 
        "time_stats.user_returned_after_30mins": 1,        
        "time_stats.avg_ai_latency_seconds": 1,
        "originality_score": 1, 
        "matching_score": 1, 
        "assistant_influence_score":1, 
        "matching_analysis": 1
    }))

    return analysis_data

def delete_analysis_entry(session_id):
    """
    Delete an analysis entry based on session_id from both 'analyses' and 'chats' collections.
    """
    analysis_result = analysis_collection.delete_one({"session_id": session_id})
    chat_result = chat_collection.delete_one({"session_id": session_id})
    deleted = analysis_result.deleted_count > 0 or chat_result.deleted_count > 0
    return {"deleted": deleted}

async def fetch_all_users():
    """
    Récupère toutes les sessions complètes de analysis_collection et les sessions incomplètes de chat_collection.
    """
    analysis_data = list(analysis_collection.find({}, {
        "_id": 0,
        "session_id": 1,
        "prolific_id":1,
        "final_idea": 1,
        "time_stats.total_messages": 1,
        "time_stats.total_duration_minutes": 1,
        "created_at": 1,
        "time_stats.user_returned_after_30mins": 1,
        "originality_score": 1,
        "matching_score": 1,
        "matching_analysis": 1
    }))
    chat_sessions = list(chat_collection.find({"final_idea": {"$exists": False}}, {"_id": 0, "session_id": 1,"conversation_history": 1,        "prolific_id":1,
}))
    all_sessions = analysis_data + chat_sessions  
    return all_sessions

async def fetch_users_by_session_id(session_id: str):
    """
    Recherche une session par son ID :
    1. Vérifie d'abord dans `analysis_collection`.
    2. Si elle existe, retourne les détails de `analysis_collection` + les données de `chat_collection` si présentes.
    3. Si non trouvée, vérifie seulement dans `chat_collection`.
    4. Si aucune donnée trouvée, retourne None.
    """
    analysis_data = analysis_collection.find_one(
        {"session_id": session_id},
        {"_id": 0}  
    )
    if analysis_data:
        chat_data = chat_collection.find_one(
            {"session_id": session_id},
            {"_id": 0} 
        )
        if chat_data:
            analysis_data["chat_session"] = chat_data
        return analysis_data
    chat_data = chat_collection.find_one(
        {"session_id": session_id},
        {"_id": 0} 
    )
    return chat_data if chat_data else None

async def get_config():
    """
    Fetch the configuration from the database.
    If no configuration exists, return None.
    """
    if config_collection is None:
        raise ValueError("Database collection is not initialized")
    config = config_collection.find_one({}, {"_id": 0})  
    return config if config else None

async def update_config(config_data: ConfigModel):
    """
    Update or insert a new configuration in the database.
    """
    if config_collection is None:
        raise ValueError("Database collection is not initialized")
    existing_config = await get_config() 
    if existing_config:
        config_collection.update_one({}, {"$set": config_data.dict()})
    else:
        config_collection.insert_one(config_data.dict())
    fresh = await get_config()
    cache_config.config_cache = fresh
    return fresh

async def get_chats(ids: List[str]) -> List[dict]:
    chats = []
    for session_id in ids:
        chat_data = chat_collection.find_one(
            {"session_id": session_id},
            {"_id": 0}  
        )
        if chat_data is not None:
            chats.append(chat_data)
    return chats

async def get_analysis(ids: List[str], file_format: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Récupère les documents dans la collection 'analyses' correspondant aux IDs fournis.
    La variable file_format peut servir à adapter le format de retour.
    """
    analyses = []
    for session_id in ids:
        analysis_data = analysis_collection.find_one(
            {"session_id": session_id},
            {"_id": 0}  
        )
        if analysis_data is not None:
            analyses.append(analysis_data)
    return analyses

async def get_all(ids: List[str], file_format: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
    """Combine les données des collections 'chats' et 'analyses'."""
    chats = await get_chats(ids)
    analyses = await get_analysis(ids, file_format)
    return {"chats": chats, "analyses": analyses}