import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import Optional
from .github_analyzer import analyze_repo, RateLimitExceeded, GitHubAPIError

# Load environment variables
from dotenv import load_dotenv
import os
load_dotenv(os.path.join(os.path.dirname(__file__), "../../.env"))

app = FastAPI(
    title="VibeCheck Backend",
    description="GitHub repository analysis and code quality assessment",
    version="1.0.0"
)

class AnalyzeRequest(BaseModel):
    repo_url: HttpUrl
    window_days: int = 90
    max_commits: int = 500

class RateLimitResponse(BaseModel):
    has_token: bool
    token_preview: Optional[str] = None
    message: str

@app.get("/debug/env")
async def debug_env():
    """Debug environment variables."""
    from .github_analyzer import GITHUB_APP_ID, GITHUB_APP_PRIVATE_KEY, GITHUB_APP_INSTALLATION_ID, GITHUB_TOKEN
    
    return {
        "GITHUB_APP_ID": GITHUB_APP_ID,
        "GITHUB_APP_PRIVATE_KEY": "Present" if GITHUB_APP_PRIVATE_KEY else "Missing",
        "GITHUB_APP_INSTALLATION_ID": GITHUB_APP_INSTALLATION_ID,
        "GITHUB_TOKEN": "Present" if GITHUB_TOKEN else "Missing",
        "has_app": bool(GITHUB_APP_ID and GITHUB_APP_PRIVATE_KEY and GITHUB_APP_INSTALLATION_ID),
        "has_token": bool(GITHUB_TOKEN)
    }

@app.get("/health")
async def health():
    return {"ok": True, "service": "VibeCheck Backend"}

@app.get("/api/rate-limit-status", response_model=RateLimitResponse)
async def rate_limit_status():
    """Check GitHub API rate limit status."""
    from .github_analyzer import GITHUB_APP_ID, GITHUB_APP_PRIVATE_KEY, GITHUB_APP_INSTALLATION_ID, GITHUB_TOKEN
    
    has_app = bool(GITHUB_APP_ID and GITHUB_APP_PRIVATE_KEY and GITHUB_APP_INSTALLATION_ID)
    has_token = bool(GITHUB_TOKEN)
    
    if has_app:
        auth_method = "GitHub App"
        rate_limit = "~15,000 requests/hour"
        token_preview = f"App ID: {GITHUB_APP_ID}"
    elif has_token:
        auth_method = "Personal Token"
        rate_limit = "~5,000 requests/hour"
        token_preview = f"{GITHUB_TOKEN[:4]}...{GITHUB_TOKEN[-4:]}" if len(GITHUB_TOKEN) > 10 else "***"
    else:
        auth_method = "Anonymous"
        rate_limit = "~60 requests/hour"
        token_preview = None
    
    message = f"Using {auth_method}. Rate limit: {rate_limit}"
    
    return RateLimitResponse(
        has_token=has_app or has_token,
        token_preview=token_preview,
        message=message
    )

@app.post("/api/analyze")
async def analyze(body: AnalyzeRequest):
    """Analyze a GitHub repository for code quality metrics."""
    try:
        result = await analyze_repo(
            str(body.repo_url), 
            window_days=body.window_days, 
            max_commits=body.max_commits
        )
        
        # Check if result contains an error
        if "error" in result:
            status_code = 400 if "Rate limit" in result["error"] else 500
            raise HTTPException(status_code=status_code, detail=result)
        
        return result
        
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except RateLimitExceeded as e:
        raise HTTPException(status_code=429, detail=str(e))
    except GitHubAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/")
async def root():
    return {
        "message": "VibeCheck Backend API",
        "docs": "/docs",
        "health": "/health",
        "rate_limit_status": "/api/rate-limit-status"
    }
