from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List
from core.analyzers.github_analyzer import (
    analyze_and_store_repo, 
    analyze_repo,
    RateLimitExceeded, 
    GitHubAPIError,
    DatabaseError,
    StorageError
)
from models.schema import (
    AnalyzeRequest,
    AnalyzeWithStorageRequest,
    UserRequest,
    AnalysisResponse,
    PaginatedResponse
)
from core.services.chatgpt import analyze_code_quality_with_chatgpt

router = APIRouter(prefix="/api/repos", tags=["Repository Analysis"])

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_repository(body: AnalyzeRequest):
    """Analyze a GitHub repository for code quality metrics (without storage)."""
    try:
        result = await analyze_repo(
            str(body.repo_url), 
            window_days=body.window_days, 
            max_commits=body.max_commits
        )
        
        if "error" in result:
            # Only treat as error if it's not a "no commits" case
            if "No commits found in the specified time window" not in result["error"]:
                status_code = 400 if "Rate limit" in result["error"] else 500
                raise HTTPException(status_code=status_code, detail=result)
        
        return AnalysisResponse(**result)
        
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except RateLimitExceeded as e:
        raise HTTPException(status_code=429, detail=str(e))
    except GitHubAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/analyze-and-store", response_model=AnalysisResponse)
async def analyze_and_store_repository(body: AnalyzeWithStorageRequest):
    """Analyze a GitHub repository and store results in database with file extraction for vector embedding."""
    print(f"DEBUG: API route - received request: {body}")
    try:
        result = await analyze_and_store_repo(
            str(body.repo_url),
            user_id=body.user_id,
            window_days=body.window_days,
            max_commits=body.max_commits,
            download_zipball=body.download_zipball
        )
        
        if "error" in result:
            # Only treat as error if it's not a "no commits" case
            if "No commits found in the specified time window" not in result["error"]:
                status_code = 400 if "Rate limit" in result["error"] else 500
                raise HTTPException(status_code=status_code, detail=result)
        
        return AnalysisResponse(**result)
        
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except RateLimitExceeded as e:
        raise HTTPException(status_code=429, detail=str(e))
    except GitHubAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except StorageError as e:
        raise HTTPException(status_code=500, detail=f"Storage error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/users")
async def create_user(body: UserRequest):
    """Create or update a user in the database."""
    from core.services.supabase import supabase
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        # Upsert user
        user_data = {
            "email": body.email,
            "name": body.name,
            "github_username": body.github_username
        }
        
        result = supabase.table("users").upsert(
            user_data,
            on_conflict="email"
        ).execute()
        
        if result.data:
            return {"user": result.data[0], "message": "User created/updated successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to create user")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")

@router.get("/users/{user_id}")
async def get_user(user_id: str):
    """Get user information by ID."""
    from core.services.supabase import supabase
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        result = supabase.table("users").select("*").eq("id", user_id).execute()
        
        if result.data:
            return {"user": result.data[0]}
        else:
            raise HTTPException(status_code=404, detail="User not found")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user: {str(e)}")

@router.get("/users/{user_id}/analyses")
async def get_user_analyses(user_id: str, limit: int = 50, offset: int = 0):
    """Get all repository analyses for a user."""
    from core.services.supabase import supabase
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        result = supabase.table("repos").select("*").eq("user_id", user_id).order(
            "analysis_date", desc=True
        ).range(offset, offset + limit - 1).execute()
        
        return PaginatedResponse(
            analyses=result.data,
            count=len(result.data),
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analyses: {str(e)}")

@router.get("/repos")
async def get_repositories(limit: int = 50, offset: int = 0):
    """Get all repositories in the database."""
    from core.services.supabase import supabase
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        result = supabase.table("repos").select("*").order(
            "created_at", desc=True
        ).range(offset, offset + limit - 1).execute()
        
        return PaginatedResponse(
            repositories=result.data,
            count=len(result.data),
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get repositories: {str(e)}")

@router.get("/repos/{repo_id}")
async def get_repo(repo_id: str):
    """Get a specific repository by ID."""
    from core.services.supabase import supabase
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        result = supabase.table("repos").select("*").eq("id", repo_id).execute()
        
        if result.data:
            return {"repo": result.data[0]}
        else:
            raise HTTPException(status_code=404, detail="Repository not found")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get repository: {str(e)}")

@router.get("/repos/{repo_id}/files")
async def get_repo_files(repo_id: str, limit: int = 100, offset: int = 0):
    """Get all files for a specific repository."""
    from core.services.supabase import supabase
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        # Get the repository to access file metadata
        repo_result = supabase.table("repos").select("file_metadata").eq("id", repo_id).execute()
        
        if not repo_result.data:
            raise HTTPException(status_code=404, detail="Repository not found")
        
        file_metadata = repo_result.data[0].get("file_metadata", [])
        
        # Apply pagination to the file metadata
        paginated_files = file_metadata[offset:offset + limit]
        
        return PaginatedResponse(
            files=paginated_files,
            count=len(paginated_files),
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get files: {str(e)}")

@router.get("/{repo_id}/scoring")
async def get_repo_scoring(repo_id: str):
    """Get ChatGPT-powered scoring for a repository."""
    from core.services.supabase import supabase
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        # Get the repository data
        repo_result = supabase.table("repos").select("*").eq("id", repo_id).execute()
        
        if not repo_result.data:
            raise HTTPException(status_code=404, detail="Repository not found")
        
        repo_data = repo_result.data[0]
        
        # Extract analysis data
        raw_analysis = repo_data.get("raw_analysis", {})
        file_metadata = repo_data.get("file_metadata", [])
        
        if not raw_analysis:
            raise HTTPException(status_code=400, detail="No analysis data available for this repository")
        
        # Get ChatGPT scoring
        scoring_result = analyze_code_quality_with_chatgpt(raw_analysis, file_metadata)
        
        return scoring_result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get scoring: {str(e)}")
