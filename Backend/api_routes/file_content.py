"""
File content API for serving file contents to frontend.
Since files are in Supabase, we need to download them on-demand.
"""

from fastapi import APIRouter, HTTPException
from core.services.supabase import supabase
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/files", tags=["File Content"])

@router.get("/repos/{repo_id}/file/{file_path:path}")
async def get_file_content(repo_id: str, file_path: str):
    """
    Get the content of a specific file from repository storage.
    
    Args:
        repo_id: Repository ID
        file_path: Relative path to the file
        
    Returns:
        File content as text
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        # Get repository to find base path
        repo_result = supabase.table("repos").select("file_storage_base_path, file_metadata").eq("id", repo_id).execute()
        
        if not repo_result.data:
            raise HTTPException(status_code=404, detail="Repository not found")
        
        repo_data = repo_result.data[0]
        base_path = repo_data.get("file_storage_base_path")
        file_metadata = repo_data.get("file_metadata", [])
        
        if not base_path:
            raise HTTPException(status_code=404, detail="No file storage path found")
        
        # Find the file in metadata
        file_info = None
        logger.info(f"=== File Download Request ===")
        logger.info(f"Requested file_path: '{file_path}'")
        logger.info(f"Total files in metadata: {len(file_metadata)}")
        logger.info(f"First 10 available files:")
        for i, file in enumerate(file_metadata[:10]):
            rel = file.get('relative_path', 'N/A')
            pth = file.get('path', 'N/A')
            name = file.get('name', 'N/A')
            logger.info(f"  [{i+1}] relative_path='{rel}' path='{pth}' name='{name}'")
        
        # Try multiple matching strategies
        for file in file_metadata:
            relative_path = file.get('relative_path', '')
            path = file.get('path', '')
            name = file.get('name', '')
            
            # Normalize paths for comparison (remove leading slashes, normalize separators)
            def normalize_path(p):
                if not p: return ''
                return p.strip('/').replace('\\', '/')
            
            norm_relative = normalize_path(relative_path)
            norm_path = normalize_path(path)
            norm_file_path = normalize_path(file_path)
            
            # Strategy 1: Exact match (normalized)
            if norm_relative == norm_file_path or norm_path == norm_file_path:
                file_info = file
                logger.info(f"✓ Found by exact match: {relative_path}")
                break
            
            # Strategy 2: Path ends with relative_path
            if norm_relative and (norm_file_path.endswith(norm_relative) or norm_relative in norm_file_path):
                file_info = file
                logger.info(f"✓ Found by suffix match: {relative_path}")
                break
            
            # Strategy 3: Filename matches (check last part of path)
            if name:
                norm_name = normalize_path(name)
                file_basename = norm_file_path.split('/')[-1] if '/' in norm_file_path else norm_file_path
                if norm_name == file_basename or file_basename in norm_name:
                    file_info = file
                    logger.info(f"✓ Found by filename match: {name}")
                    break
            
            # Strategy 4: Case-insensitive matching
            if relative_path.lower() == file_path.lower() or path.lower() == file_path.lower():
                file_info = file
                logger.info(f"✓ Found by case-insensitive match: {relative_path}")
                break
        
        if not file_info:
            # Log ALL available files for debugging
            all_paths = []
            for f in file_metadata:
                all_paths.append({
                    'relative_path': f.get('relative_path'),
                    'path': f.get('path'),
                    'name': f.get('name')
                })
            logger.error(f"✗ File NOT FOUND: '{file_path}'")
            logger.error(f"All {len(file_metadata)} available files:")
            for i, paths in enumerate(all_paths):
                logger.error(f"  [{i+1}] {paths}")
            raise HTTPException(status_code=404, detail=f"File not found in repository: {file_path}")
        
        storage_path = file_info.get('storage_path')
        if not storage_path:
            # If storage_path not found, construct it from base_path and relative_path
            relative_path = file_info.get('relative_path') or file_info.get('path')
            storage_path = f"{base_path}/{relative_path}" if relative_path else None
            
        if not storage_path:
            raise HTTPException(status_code=404, detail="File storage path not found")
        
        logger.info(f"Downloading file from storage path: {storage_path}")
        
        # Download file from Supabase storage
        file_data = supabase.storage.from_("repo-files").download(storage_path)
        
        if not file_data:
            raise HTTPException(status_code=404, detail="Could not download file from storage")
        
        # Decode content
        try:
            content = file_data.decode('utf-8')
        except UnicodeDecodeError:
            raise HTTPException(status_code=415, detail="File is binary or not readable")
        
        return {
            "path": file_path,
            "content": content,
            "file_info": file_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting file content: {str(e)}", exc_info=True)
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to get file content: {str(e)}")

@router.get("/repos/{repo_id}/files")
async def list_files(repo_id: str):
    """
    List all files in a repository with their issues.
    
    Returns:
        List of files with metadata and issue counts
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        repo_result = supabase.table("repos").select("file_metadata").eq("id", repo_id).execute()
        
        if not repo_result.data:
            raise HTTPException(status_code=404, detail="Repository not found")
        
        file_metadata = repo_result.data[0].get("file_metadata", [])
        
        files = []
        for file_info in file_metadata:
            files.append({
                "path": file_info.get('relative_path', file_info.get('path', '')),
                "name": file_info.get('name', ''),
                "size": file_info.get('size_bytes', 0),
                "extension": file_info.get('file_extension', ''),
                "storage_path": file_info.get('storage_path', '')
            })
        
        return {"files": files, "count": len(files)}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")
