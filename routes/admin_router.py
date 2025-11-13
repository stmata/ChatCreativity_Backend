from fastapi import APIRouter, HTTPException
from services.admin_services import get_config, get_chats, get_analysis, get_all, update_config, fetch_users_by_session_id, fetch_all_users, get_statistics, delete_analysis_entry, get_analysis_data, get_diagram_data
from datetime import datetime
from typing import List, Dict, Optional, Any
from models.models import ConfigModel, DownloadRequest

router = APIRouter()

@router.get("/stats")
def fetch_stats():
    return get_statistics()

@router.get("/diagrams")
def fetch_diagram_data():
    return get_diagram_data()

@router.get("/analysis")
async def fetch_analysis(start_date: str = None, end_date: str = None):
    """
    Fetch analysis data with optional date filtering.
    """
    start_dt = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
    end_dt = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None
    return get_analysis_data(start_dt, end_dt)

@router.delete("/analysis/{session_id}")
async def remove_analysis(session_id: str):
    """
    Delete a specific analysis entry.
    """
    return delete_analysis_entry(session_id)

@router.get("/datas", response_model=List[Dict])
async def get_users():
    """
    Récupère toutes les données depuis MongoDB sans filtrage.
    """
    return await fetch_all_users()

@router.get("/user", response_model=List[Dict[str, Any]])
async def get_users(id_session: Optional[str] = None):
    """
    Récupère toutes les données depuis MongoDB.
    - Si `id_session` est fourni, retourne les données filtrées par session_id.
    - Sinon, retourne toutes les sessions.
    """
    if id_session:
        result = await fetch_users_by_session_id(id_session)
        return [result] if result else [] 
    return await fetch_all_users()

@router.get("/config", response_model=ConfigModel)
async def get_configuration():
    """
    Retrieve the configuration from the database.
    """
    config = await get_config()
    if not config:
        raise HTTPException(status_code=404, detail="No configuration found in the database")
    return config

@router.put("/config", response_model=ConfigModel)
async def update_configuration(config_data: ConfigModel):
    """
    Update the configuration in the database.
    """
    updated_config = await update_config(config_data)
    if not updated_config:
        raise HTTPException(status_code=400, detail="Failed to update configuration")
    return updated_config

@router.post("/download/chats", response_model=List[dict])
async def download_chats(request: DownloadRequest):
    chats = await get_chats(request.ids)
    if not chats:
        raise HTTPException(status_code=400, detail="No chats found for given IDs")
    return chats

@router.post("/download/analysis", response_model=List[dict])
async def download_analysis(request: DownloadRequest):
    analyses = await get_analysis(request.ids, request.format)
    if not analyses:
        raise HTTPException(status_code=400, detail="No analyses found for given IDs")
    return analyses

@router.post("/download/all", response_model=dict)
async def download_all(request: DownloadRequest):
    data = await get_all(request.ids, request.format)
    if not data["chats"] and not data["analyses"]:
        raise HTTPException(status_code=400, detail="No data found for given IDs")
    return data

