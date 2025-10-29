"""
API route to get repository files directly from database
"""
from fastapi import APIRouter, HTTPException
from core.services.supabase import supabase
from typing import List, Dict, Any

router = APIRouter(prefix="/api/repos", tags=["Repository Files"])

@router.get("/{repo_id}/files/list")
async def get_repo_files_list(repo_id: str):
    """Get list of all files in a repository"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        result = supabase.table("repos").select("*").eq("id", repo_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Repository not found")
        
        repo = result.data[0]
        file_metadata = repo.get("file_metadata", [])
        
        files = []
        for file in file_metadata:
            files.append({
                "name": file.get('name', '').split('/')[-1] if file.get('name') else '',
                "path": file.get('relative_path', file.get('path', '')),
                "score": 0,
                "issues": [],
                "aiPercentage": 0,
                "quality": 0
            })
        
        return {"files": files, "count": len(files)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

