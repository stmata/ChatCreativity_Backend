from fastapi import APIRouter, HTTPException
from datetime import datetime
from services.analysis_service import compute_time_stats, compute_size_stats, analyze_final_idea
from services.mongodb_connection import MongoDBManager
from models.models import AnalyzePayload

router = APIRouter()
mongo_manager = MongoDBManager()
db = mongo_manager.db

@router.post("/analyze")
async def analyze_session(payload: AnalyzePayload):
    session_id = payload.session_id
    prolific_id = payload.prolific_id 

    session_doc = db["chats"].find_one({"session_id": session_id})
    if not session_doc:
        raise HTTPException(status_code=404, detail="Session not found")

    conversation_history = session_doc.get("conversation_history", [])
    final_idea = session_doc.get("final_idea", "")

    time_stats = compute_time_stats(conversation_history)
    size_stats = compute_size_stats(conversation_history)

    try:
        originality_score, matching_score, matching_analysis, assistant_influence_score = analyze_final_idea(conversation_history, final_idea)
    except ValueError:
        return False  

    analysis_result = {
        "session_id": session_id,
        "prolific_id": prolific_id,
        "final_idea": final_idea,
        "time_stats": time_stats,
        "size_stats": size_stats,
        "originality_score": originality_score,
        "matching_score": matching_score,
        "assistant_influence_score": assistant_influence_score,
        "matching_analysis": matching_analysis,
        "created_at": datetime.utcnow().isoformat(),
    }

    try:
        inserted_doc = db["analyses"].insert_one(analysis_result)
        return inserted_doc.acknowledged  
    except Exception as e:
        return False 
    
