import os
import math
import asyncio
import statistics
import time
import jwt
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass

import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# GitHub App configuration
GITHUB_APP_ID = os.getenv("GITHUB_APP_ID")
GITHUB_APP_PRIVATE_KEY = os.getenv("GITHUB_APP_PRIVATE_KEY")
GITHUB_APP_INSTALLATION_ID = os.getenv("GITHUB_APP_INSTALLATION_ID")

# Fallback to personal token
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

def get_auth_headers() -> Dict[str, str]:
    """Get authentication headers for GitHub API."""
    if GITHUB_APP_ID and GITHUB_APP_PRIVATE_KEY and GITHUB_APP_INSTALLATION_ID:
        # Use GitHub App
        token = generate_installation_token()
        return {"Authorization": f"Bearer {token}"}
    elif GITHUB_TOKEN:
        # Use personal token
        return {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    else:
        # No authentication
        return {}

def generate_installation_token() -> str:
    """Generate installation access token for GitHub App."""
    if not all([GITHUB_APP_ID, GITHUB_APP_PRIVATE_KEY, GITHUB_APP_INSTALLATION_ID]):
        raise ValueError("GitHub App credentials not configured")
    
    # Create JWT token
    now = int(time.time())
    payload = {
        "iat": now - 60,  # Issued at (1 minute ago)
        "exp": now + 600,  # Expires in 10 minutes
        "iss": GITHUB_APP_ID  # Issuer (App ID)
    }
    
    # Generate JWT
    jwt_token = jwt.encode(payload, GITHUB_APP_PRIVATE_KEY, algorithm="RS256")
    
    # Exchange JWT for installation token
    url = f"https://api.github.com/app/installations/{GITHUB_APP_INSTALLATION_ID}/access_tokens"
    headers = {"Authorization": f"Bearer {jwt_token}", "Accept": "application/vnd.github.v3+json"}
    
    response = httpx.post(url, headers=headers)
    response.raise_for_status()
    
    return response.json()["token"]

@dataclass
class RateLimitInfo:
    remaining: int
    reset_time: int
    limit: int

class GitHubAPIError(Exception):
    pass

class RateLimitExceeded(GitHubAPIError):
    pass


def parse_repo(url: str) -> Tuple[str, str]:
    url = url.rstrip("/")
    parts = url.split("/")
    if len(parts) < 5 or parts[2] != "github.com":
        raise ValueError("Invalid GitHub repo URL. Expected https://github.com/{owner}/{repo}")
    owner = parts[3]
    repo = parts[4].removesuffix(".git")
    return owner, repo


def parse_rate_limit_headers(response: httpx.Response) -> RateLimitInfo:
    """Parse GitHub rate limit headers from response."""
    remaining = int(response.headers.get("X-RateLimit-Remaining", "0"))
    reset_time = int(response.headers.get("X-RateLimit-Reset", "0"))
    limit = int(response.headers.get("X-RateLimit-Limit", "60"))
    return RateLimitInfo(remaining=remaining, reset_time=reset_time, limit=limit)


async def make_github_request(client: httpx.AsyncClient, url: str, params: Optional[Dict] = None) -> httpx.Response:
    """Make a GitHub API request with rate limit handling."""
    try:
        headers = get_auth_headers()
        response = await client.get(url, params=params, headers=headers)
        
        # Check rate limits
        rate_info = parse_rate_limit_headers(response)
        
        if response.status_code == 403 and "rate limit" in response.text.lower():
            raise RateLimitExceeded(f"Rate limit exceeded. Reset at {rate_info.reset_time}")
        
        if response.status_code == 404:
            raise GitHubAPIError(f"Repository not found: {url}")
        
        response.raise_for_status()
        return response
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 403:
            raise RateLimitExceeded("Rate limit exceeded")
        raise GitHubAPIError(f"HTTP error: {e.response.status_code}")


async def get_repo_languages(client: httpx.AsyncClient, owner: str, repo: str) -> Dict[str, int]:
    """Get repository languages."""
    url = f"https://api.github.com/repos/{owner}/{repo}/languages"
    response = await make_github_request(client, url)
    return response.json()


async def get_commits(client: httpx.AsyncClient, owner: str, repo: str, since: str, max_commits: int) -> List[Dict[str, Any]]:
    """Get repository commits with pagination."""
    commits = []
    page = 1
    per_page = min(100, max_commits)  # GitHub max is 100 per page
    
    while len(commits) < max_commits:
        url = f"https://api.github.com/repos/{owner}/{repo}/commits"
        params = {
            "since": since,
            "per_page": per_page,
            "page": page
        }
        
        response = await make_github_request(client, url, params)
        batch = response.json()
        
        if not batch:  # No more commits
            break
            
        commits.extend(batch)
        
        if len(batch) < per_page:  # Last page
            break
            
        page += 1
        
        # Small delay to be respectful
        await asyncio.sleep(0.1)
    
    return commits[:max_commits]


async def get_commit_details(client: httpx.AsyncClient, owner: str, repo: str, commits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Get detailed commit information with concurrency control."""
    semaphore = asyncio.Semaphore(5)  # Limit concurrent requests
    
    async def fetch_commit(commit: Dict[str, Any]) -> Dict[str, Any]:
        async with semaphore:
            sha = commit["sha"]
            url = f"https://api.github.com/repos/{owner}/{repo}/commits/{sha}"
            response = await make_github_request(client, url)
            return response.json()
    
    # Process commits in batches to avoid overwhelming the API
    details = []
    batch_size = 10
    
    for i in range(0, len(commits), batch_size):
        batch = commits[i:i + batch_size]
        batch_details = await asyncio.gather(*[fetch_commit(c) for c in batch])
        details.extend(batch_details)
        
        # Small delay between batches
        if i + batch_size < len(commits):
            await asyncio.sleep(0.5)
    
    return details


def gini(values: List[float]) -> float:
    arr = sorted([v for v in values if v > 0])
    n = len(arr)
    if n == 0:
        return 0.0
    s = sum(arr)
    if s == 0:
        return 0.0
    cum = 0.0
    weighted = 0.0
    for v in arr:
        cum += v
        weighted += cum
    return (n + 1 - 2 * (weighted / s)) / n


def top_dir(path: str) -> str:
    i = path.find("/")
    return "(root)" if i == -1 else path[:i]


def compartmentalization(files: List[Dict[str, Any]]) -> float:
    # files: [{filename, additions, deletions}]
    if not files or len(files) == 1:
        return 1.0
    by_dir: Dict[str, int] = {}
    for f in files:
        w = (int(f.get("additions", 0)) + int(f.get("deletions", 0))) or 1
        d = top_dir(f["filename"]) if isinstance(f.get("filename"), str) else "(root)"
        by_dir[d] = by_dir.get(d, 0) + w
    vals = list(by_dir.values())
    total = sum(vals) or 1
    probs = [v / total for v in vals]
    if len(probs) <= 1:
        return 1.0
    H = -sum(p * math.log(p) for p in probs if p > 0)
    return 1 - (H / math.log(len(probs)))


async def analyze_repo(repo_url: str, window_days: int = 90, max_commits: int = 500) -> Dict[str, Any]:
    """Analyze a GitHub repository using REST API with proper error handling."""
    owner, repo = parse_repo(repo_url)
    since = (datetime.utcnow() - timedelta(days=window_days)).isoformat() + "Z"

    timeout = httpx.Timeout(30.0)
    limits = httpx.Limits(max_keepalive_connections=10, max_connections=20)

    try:
        async with httpx.AsyncClient(timeout=timeout, limits=limits) as client:
            # Get languages
            languages = await get_repo_languages(client, owner, repo)
            
            # Get commits
            commits = await get_commits(client, owner, repo, since, max_commits)
            
            if not commits:
                return {
                    "repo": f"{owner}/{repo}",
                    "error": "No commits found in the specified time window",
                    "languages": languages,
                    "team": {"contributions": [], "giniContribution": 0.0, "topContributorsShare": 0.0, "perAuthorLanguage": []},
                    "commits": {"count": 0, "medianCompartmentalization": 1.0, "meanCompartmentalization": 1.0}
                }
            
            # Get commit details
            details = await get_commit_details(client, owner, repo, commits)
            
    except RateLimitExceeded as e:
        return {
            "repo": f"{owner}/{repo}",
            "error": f"Rate limit exceeded: {str(e)}",
            "suggestion": "Add GITHUB_TOKEN to .env file or reduce max_commits/window_days"
        }
    except GitHubAPIError as e:
        return {
            "repo": f"{owner}/{repo}",
            "error": f"GitHub API error: {str(e)}"
        }
    except Exception as e:
        return {
            "repo": f"{owner}/{repo}",
            "error": f"Unexpected error: {str(e)}"
        }

    # Process the data
    author_net: Dict[str, int] = {}
    ci_values: List[float] = []
    ext_map: Dict[str, str] = {
        "js": "JavaScript", "jsx": "JavaScript", "ts": "TypeScript", "tsx": "TypeScript",
        "py": "Python", "go": "Go", "rb": "Ruby", "java": "Java", "cs": "C#", "php": "PHP",
        "rs": "Rust", "kt": "Kotlin", "swift": "Swift", "cpp": "C++", "c": "C",
        "m": "Objective-C", "mm": "Objective-C++", "scala": "Scala", "dart": "Dart",
    }
    per_author_lang: Dict[str, Dict[str, int]] = {}

    for d in details:
        commit_obj = d.get("commit") or {}
        author_login = (d.get("author") or {}).get("login")
        author = author_login or (commit_obj.get("author") or {}).get("email") or "unknown"

        stats = d.get("stats") or {}
        adds = int(stats.get("additions", 0))
        dels = int(stats.get("deletions", 0))
        author_net[author] = author_net.get(author, 0) + (adds - dels)

        files = d.get("files") or []
        if files:
            ci_values.append(compartmentalization(files))
        lang_bucket = per_author_lang.get(author, {})
        for f in files:
            filename = f.get("filename", "")
            ext = filename.split(".")[-1].lower() if "." in filename else ""
            lang = ext_map.get(ext, "Other")
            weight = (int(f.get("additions", 0)) + int(f.get("deletions", 0))) or 1
            lang_bucket[lang] = lang_bucket.get(lang, 0) + weight
        per_author_lang[author] = lang_bucket

    totals = [max(0, v) for v in author_net.values()]
    top3_share = (sum(sorted(totals, reverse=True)[:3]) / (sum(totals) or 1)) if totals else 0.0
    median_ci = statistics.median(ci_values) if ci_values else 1.0
    mean_ci = (sum(ci_values) / len(ci_values)) if ci_values else 1.0

    return {
        "repo": f"{owner}/{repo}",
        "limits": {"since": since, "max_commits": max_commits, "truncated": len(commits) >= max_commits},
        "languages": languages,
        "team": {
            "giniContribution": gini(totals),
            "topContributorsShare": top3_share,
            "contributions": [{"author": k, "netLines": v} for k, v in author_net.items()],
            "perAuthorLanguage": [{"author": a, "languages": l} for a, l in per_author_lang.items()],
        },
        "commits": {
            "count": len(details),
            "medianCompartmentalization": median_ci,
            "meanCompartmentalization": mean_ci,
        },
    }
