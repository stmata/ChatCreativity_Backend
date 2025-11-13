import asyncio
from services.mongodb_connection import MongoDBManager

mongo_manager = MongoDBManager()
collection = mongo_manager.get_collection('chats')
config_collection = mongo_manager.get_collection("config")


async def load_conversation(session_id: str) -> list:
    """
    Charge l'historique de conversation pour une session donnée.
    Renvoie une liste de messages (chaque message étant un dict avec 'role' et 'content').
    """
    def sync_find():
        doc = collection.find_one({"session_id": session_id})
        if doc and "conversation_history" in doc:
            return doc["conversation_history"]
        return []
    conversation = await asyncio.to_thread(sync_find)
    return conversation

async def update_final_idea(session_id: str, idea: str, prolific_id: str):
    """
    Met à jour ou crée un document pour la session donnée en y ajoutant l'idée finale.
    """
    def sync_update():
        return collection.update_one(
            {"session_id": session_id},
            {"$set": {"final_idea": idea, "prolific_id": prolific_id
        }},
            upsert=True
        )
    result = await asyncio.to_thread(sync_update)
    def sync_get_url():
        config_doc = config_collection.find_one({}, {"_id": 0, "linkValue": 1})
        return config_doc.get("linkValue") if config_doc else None
    
    url = await asyncio.to_thread(sync_get_url)
    return result, url

async def save_conversation(session_id: str, conversation_history: list):
    """
    Ajoute les nouveaux messages sans dupliquer ceux déjà présents dans la base.
    """
    def sync_save():
        doc = collection.find_one({"session_id": session_id})
        existing_history = doc.get("conversation_history", []) if doc else []

        existing_set = {f"{m['role']}|{m['content']}|{m['timestamp']}" for m in existing_history}
        new_filtered = [
            m for m in conversation_history
            if f"{m['role']}|{m['content']}|{m['timestamp']}" not in existing_set
        ]

        combined_history = existing_history + new_filtered

        return collection.update_one(
            {"session_id": session_id},
            {"$set": {"conversation_history": combined_history}},
            upsert=True
        )

    result = await asyncio.to_thread(sync_save)
    return result


