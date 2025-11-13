from fastapi import APIRouter, Header, Depends, HTTPException, Query
from services.chat_handler import process_chat_stream
from services.getConversation_service import get_conversation
from services.saveConversation_service import update_final_idea 
from models.models import ChatRequest, FinalIdeaRequest

router = APIRouter()

async def get_session_id(x_session_id: str = Header(...)):
    return x_session_id

@router.post("/chat_stream")
async def chat_stream_endpoint(request: ChatRequest, session_id: str = Depends(get_session_id)):
    conversation_history = []  
    return await process_chat_stream(request.message, session_id, conversation_history)

@router.get("/conversation")
async def conversation_endpoint(session_id: str):
    conversation, nbreMessage, sexe = await get_conversation(session_id)
    return {"conversation_history": conversation,
        "message_value": nbreMessage,         "sexe": sexe
}

@router.post("/add-finalIdea")
async def add_final_idea_endpoint(final_idea: FinalIdeaRequest, session_id: str = Query(...)):
    """
    Endpoint qui enregistre l'idée finale associée à une session.
    Le session_id est transmis en query string.
    """
    result, url = await update_final_idea(session_id, final_idea.idea, final_idea.prolific_id)
    if result.modified_count == 0 and result.upserted_id is None:
        raise HTTPException(status_code=400, detail="Erreur lors de l'ajout de l'idée finale")
    return url
