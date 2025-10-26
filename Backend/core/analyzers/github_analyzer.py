import os
import math
import asyncio
import statistics
import time
import jwt
import zipfile
import tempfile
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

# Import shared Supabase client
from core.services.supabase import supabase

def get_auth_headers() -> Dict[str, str]:
    """Get authentication headers for GitHub API."""
    print(f"DEBUG: get_auth_headers - GITHUB_APP_ID: {bool(GITHUB_APP_ID)}, GITHUB_APP_PRIVATE_KEY: {bool(GITHUB_APP_PRIVATE_KEY)}, GITHUB_APP_INSTALLATION_ID: {bool(GITHUB_APP_INSTALLATION_ID)}")
    print(f"DEBUG: get_auth_headers - GITHUB_TOKEN: {bool(GITHUB_TOKEN)}")
    
    if GITHUB_APP_ID and GITHUB_APP_PRIVATE_KEY and GITHUB_APP_INSTALLATION_ID:
        # Use GitHub App
        print("DEBUG: Using GitHub App authentication")
        token = generate_installation_token()
        return {"Authorization": f"Bearer {token}"}
    elif GITHUB_TOKEN:
        # Use personal token
        print("DEBUG: Using personal token authentication")
        return {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    else:
        # No authentication
        print("DEBUG: No authentication available")
        return {}

def generate_installation_token() -> str:
    """Generate installation access token for GitHub App."""
    if not all([GITHUB_APP_ID, GITHUB_APP_PRIVATE_KEY, GITHUB_APP_INSTALLATION_ID]):
        raise ValueError("GitHub App credentials not configured")
    
    # Ensure private key is properly formatted with newlines
    private_key = GITHUB_APP_PRIVATE_KEY.replace('\\n', '\n')
    
    # Create JWT token
    now = int(time.time())
    payload = {
        "iat": now - 60,  # Issued at (1 minute ago)
        "exp": now + 600,  # Expires in 10 minutes
        "iss": GITHUB_APP_ID  # Issuer (App ID)
    }
    
    # Generate JWT
    jwt_token = jwt.encode(payload, private_key, algorithm="RS256")
    
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

class DatabaseError(Exception):
    pass

class StorageError(Exception):
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


async def make_github_request(client: httpx.AsyncClient, url: str, params: Optional[Dict] = None, max_retries: int = 3) -> httpx.Response:
    """Make a GitHub API request with rate limit handling and retry logic."""
    for attempt in range(max_retries):
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
            
        except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.WriteTimeout, httpx.PoolTimeout) as e:
            if attempt < max_retries - 1:
                print(f"DEBUG: Request timeout (attempt {attempt + 1}/{max_retries}), retrying in 2 seconds...")
                await asyncio.sleep(2)
                continue
            else:
                raise GitHubAPIError(f"Request timeout after {max_retries} attempts: {str(e)}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                raise RateLimitExceeded("Rate limit exceeded")
            raise GitHubAPIError(f"HTTP error: {e.response.status_code}")
        except Exception as e:
            if "handshake operation timed out" in str(e) and attempt < max_retries - 1:
                print(f"DEBUG: SSL handshake timeout (attempt {attempt + 1}/{max_retries}), retrying in 3 seconds...")
                await asyncio.sleep(3)
                continue
            else:
                raise GitHubAPIError(f"Request failed: {str(e)}")
    
    raise GitHubAPIError("Max retries exceeded")


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
    semaphore = asyncio.Semaphore(3)  # Limit concurrent requests
    
    async def fetch_commit(commit: Dict[str, Any]) -> Dict[str, Any]:
        async with semaphore:
            sha = commit["sha"]
            url = f"https://api.github.com/repos/{owner}/{repo}/commits/{sha}"
            response = await make_github_request(client, url)
            # Small delay to be gentle on GitHub API
            await asyncio.sleep(0.1)
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


# COMMENTED OUT: Old zipball approach - replaced with Contents API for better file size handling
# async def download_repo_zipball(client: httpx.AsyncClient, owner: str, repo: str, ref: str = "main") -> bytes:
#     """Download repository as zipball from GitHub."""
#     url = f"https://api.github.com/repos/{owner}/{repo}/zipball/{ref}"
#     headers = get_auth_headers()
#     
#     try:
#         response = await client.get(url, headers=headers, follow_redirects=True)
#         response.raise_for_status()
#         return response.content
#     except httpx.HTTPStatusError as e:
#         if e.response.status_code == 404:
#             raise GitHubAPIError(f"Repository or branch not found: {owner}/{repo}#{ref}")
#         raise GitHubAPIError(f"Failed to download zipball: {e.response.status_code}")


async def get_repo_contents_recursive(client: httpx.AsyncClient, owner: str, repo: str, ref: str = "main", path: str = "") -> List[Dict[str, Any]]:
    """Recursively get all repository contents using GitHub Contents API."""
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}" if path else f"https://api.github.com/repos/{owner}/{repo}/contents"
    headers = get_auth_headers()
    headers["Accept"] = "application/vnd.github+json"
    
    try:
        response = await make_github_request(client, url, {"ref": ref})
        contents = response.json()
        
        files = []
        
        # Handle single file response
        if isinstance(contents, dict):
            if contents.get("type") == "file":
                files.append(contents)
            elif contents.get("type") == "dir":
                # This shouldn't happen with the API, but handle it
                subfiles = await get_repo_contents_recursive(client, owner, repo, ref, contents["path"])
                files.extend(subfiles)
        # Handle directory response (array of items)
        elif isinstance(contents, list):
            for item in contents:
                if item.get("type") == "file":
                    files.append(item)
                elif item.get("type") == "dir":
                    # Recursively get subdirectory contents
                    subfiles = await get_repo_contents_recursive(client, owner, repo, ref, item["path"])
                    files.extend(subfiles)
        
        return files
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise GitHubAPIError(f"Repository, branch, or path not found: {owner}/{repo}#{ref}/{path}")
        raise GitHubAPIError(f"Failed to get contents: {e.response.status_code}")


async def download_file_content(client: httpx.AsyncClient, file_info: Dict[str, Any]) -> bytes:
    """Download file content using GitHub Contents API with proper size handling."""
    url = file_info["download_url"]
    headers = get_auth_headers()
    
    try:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        return response.content
    except httpx.HTTPStatusError as e:
        raise GitHubAPIError(f"Failed to download file {file_info['path']}: {e.response.status_code}")


# COMMENTED OUT: Old zipball extraction approach - replaced with Contents API
# async def extract_and_store_files(zipball_data: bytes, repo_id: str, user_id: str, ref: str = "main") -> Dict[str, Any]:
#     """Extract zipball and store individual files for vector embedding preparation."""
#     if not supabase:
#         raise StorageError("Supabase client not initialized")
#     
#     if not zipball_data:
#         raise StorageError("Zipball data is empty or None")
#     
#     print(f"DEBUG: extract_and_store_files - repo_id: {repo_id}, user_id: {user_id}, ref: {ref}")
#     print(f"DEBUG: zipball_data size: {len(zipball_data) if zipball_data else 'None'}")
#     
#     # Create timestamp for this extraction
#     timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
#     base_path = f"repos/{user_id}/{repo_id}/{ref}_{timestamp}"
#     
#     stored_files = []
#     file_metadata = []
#     skipped_files = []
#     
#     try:
#         # Extract zipball to temporary directory
#         with tempfile.TemporaryDirectory() as temp_dir:
#             zip_path = os.path.join(temp_dir, f"{repo_id}_{ref}.zip")
#             
#             # Write zipball data to temporary file
#             with open(zip_path, 'wb') as f:
#                 f.write(zipball_data)
#             
#             # Extract zipball
#             with zipfile.ZipFile(zip_path, 'r') as zip_ref:
#                 zip_ref.extractall(temp_dir)
#             
#             # Find the extracted directory (GitHub zipballs have a top-level directory)
#             extracted_dirs = [d for d in os.listdir(temp_dir) if os.path.isdir(os.path.join(temp_dir, d)) and d != f"{repo_id}_{ref}.zip"]
#             if not extracted_dirs:
#                 raise StorageError("No extracted directory found in zipball")
#             
#             extracted_dir = os.path.join(temp_dir, extracted_dirs[0])
#             
#             # Walk through extracted files and upload them
#             for root, dirs, files in os.walk(extracted_dir):
#                 for file in files:
#                     file_path = os.path.join(root, file)
#                     relative_path = os.path.relpath(file_path, extracted_dir)
#                     
#                     print(f"DEBUG: Processing file: {file_path}, relative_path: {relative_path}")
#                     
#                     # Skip if relative_path is None or empty
#                     if not relative_path:
#                         print(f"DEBUG: Skipping file with empty relative_path: {file_path}")
#                         skipped_files.append({"path": relative_path, "reason": "empty_path"})
#                         continue
#                     
#                     # Skip certain files/directories
#                     if should_skip_file(relative_path):
#                         print(f"DEBUG: Skipping file based on pattern: {relative_path}")
#                         skipped_files.append({"path": relative_path, "reason": "pattern_match"})
#                         continue
#                     
#                     # Check file size first (Supabase has a 50MB limit)
#                     file_size = os.path.getsize(file_path)
#                     max_size = 50 * 1024 * 1024  # 50MB
#                     
#                     if file_size > max_size:
#                         print(f"DEBUG: Skipping file due to size: {relative_path} ({file_size} bytes)")
#                         skipped_files.append({"path": relative_path, "reason": "file_too_large", "size_bytes": file_size})
#                         continue
#                     
#                     # Read file content
#                     try:
#                         with open(file_path, 'rb') as f:
#                             file_content = f.read()
#                     except (UnicodeDecodeError, PermissionError) as e:
#                         # Skip binary files or files we can't read
#                         print(f"DEBUG: Skipping file due to read error: {relative_path} - {str(e)}")
#                         skipped_files.append({"path": relative_path, "reason": "read_error", "error": str(e)})
#                         continue
#                     
#                     # Determine file type and content type
#                     file_ext = os.path.splitext(file)[1].lower()
#                     content_type = get_content_type(file_ext)
#                     
#                     # Create storage path
#                     storage_path = f"{base_path}/{relative_path}"
#                     
#                     # Upload file to Supabase storage
#                     result = supabase.storage.from_("repo-files").upload(
#                         path=storage_path,
#                         file=file_content,
#                         file_options={"content-type": content_type}
#                     )
#                     
#                     if isinstance(result, dict) and result.get("error"):
#                         print(f"Warning: Failed to upload {relative_path}: {result['error']}")
#                         continue
#                     elif hasattr(result, 'data') and result.data is None:
#                         print(f"Warning: Failed to upload {relative_path}: No data returned")
#                         continue
#                     
#                     # Get public URL for the file
#                     public_url = supabase.storage.from_("repo-files").get_public_url(storage_path)
#                     
#                     stored_files.append({
#                         "path": relative_path,
#                         "storage_path": storage_path,
#                         "public_url": public_url,
#                         "size": len(file_content),
#                         "extension": file_ext,
#                         "content_type": content_type
#                     })
#                     
#                     file_metadata.append({
#                         "relative_path": relative_path,
#                         "storage_path": storage_path,
#                         "public_url": public_url,
#                         "size_bytes": len(file_content),
#                         "file_extension": file_ext,
#                         "content_type": content_type
#                     })
#         
#         return {
#             "base_path": base_path,
#             "file_count": len(stored_files),
#             "files": stored_files,
#             "file_metadata": file_metadata,
#             "skipped_files": skipped_files,
#             "skipped_count": len(skipped_files)
#         }
#         
#     except Exception as e:
#         print(f"DEBUG: File extraction and storage exception: {str(e)}")
#         raise StorageError(f"File extraction and storage failed: {str(e)}")


async def extract_and_store_files_contents_api(client: httpx.AsyncClient, owner: str, repo: str, repo_id: str, user_id: str, ref: str = "main") -> Dict[str, Any]:
    """Extract and store individual files using GitHub Contents API for better file size handling."""
    if not supabase:
        raise StorageError("Supabase client not initialized")
    
    print(f"DEBUG: extract_and_store_files_contents_api - repo_id: {repo_id}, user_id: {user_id}, ref: {ref}")
    
    # Create timestamp for this extraction
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    base_path = f"repos/{user_id}/{repo_id}/{ref}_{timestamp}"
    
    stored_files = []
    file_metadata = []
    skipped_files = []
    
    try:
        # Get all repository files recursively
        print(f"DEBUG: Getting repository contents for {owner}/{repo}")
        all_files = await get_repo_contents_recursive(client, owner, repo, ref)
        print(f"DEBUG: Found {len(all_files)} files in repository")
        
        # Process files with concurrency control - reduced for stability
        semaphore = asyncio.Semaphore(2)  # Limit concurrent downloads
        
        async def process_file(file_info: Dict[str, Any]) -> None:
            async with semaphore:
                relative_path = file_info["path"]
                file_size = file_info.get("size", 0)
                
                print(f"DEBUG: Processing file: {relative_path}, size: {file_size} bytes")
                
                # Skip certain files/directories
                if should_skip_file(relative_path):
                    print(f"DEBUG: Skipping file based on pattern: {relative_path}")
                    skipped_files.append({"path": relative_path, "reason": "pattern_match"})
                    return
                
                # Handle file size limits according to GitHub API documentation
                if file_size > 100 * 1024 * 1024:  # 100MB limit
                    print(f"DEBUG: Skipping file due to size (>100MB): {relative_path} ({file_size} bytes)")
                    skipped_files.append({"path": relative_path, "reason": "file_too_large", "size_bytes": file_size})
                    return
                
                # Skip binary files (check by extension)
                file_ext = os.path.splitext(relative_path)[1].lower()
                if is_binary_file(file_ext):
                    print(f"DEBUG: Skipping binary file: {relative_path}")
                    skipped_files.append({"path": relative_path, "reason": "binary_file", "extension": file_ext})
                    return
                
                try:
                    # Download file content
                    file_content = await download_file_content(client, file_info)
                    
                    # Small delay between GitHub API requests
                    await asyncio.sleep(0.1)
                    
                    # Additional size check for Supabase (50MB limit)
                    if len(file_content) > 50 * 1024 * 1024:
                        print(f"DEBUG: Skipping file due to Supabase size limit: {relative_path} ({len(file_content)} bytes)")
                        skipped_files.append({"path": relative_path, "reason": "supabase_size_limit", "size_bytes": len(file_content)})
                        return
                    
                    # Determine content type
                    content_type = get_content_type(file_ext)
                    
                    # Create storage path
                    storage_path = f"{base_path}/{relative_path}"
                    
                    # Upload file to Supabase storage
                    result = supabase.storage.from_("repo-files").upload(
                        path=storage_path,
                        file=file_content,
                        file_options={"content-type": content_type}
                    )
                    
                    if isinstance(result, dict) and result.get("error"):
                        print(f"Warning: Failed to upload {relative_path}: {result['error']}")
                        skipped_files.append({"path": relative_path, "reason": "upload_failed", "error": result['error']})
                        return
                    elif hasattr(result, 'data') and result.data is None:
                        print(f"Warning: Failed to upload {relative_path}: No data returned")
                        skipped_files.append({"path": relative_path, "reason": "upload_failed", "error": "No data returned"})
                        return
                    
                    # Get public URL for the file
                    public_url = supabase.storage.from_("repo-files").get_public_url(storage_path)
                    
                    # Small delay between file uploads to be gentle on APIs
                    await asyncio.sleep(0.2)
                    
                    stored_files.append({
                        "path": relative_path,
                        "storage_path": storage_path,
                        "public_url": public_url,
                        "size": len(file_content),
                        "extension": file_ext,
                        "content_type": content_type
                    })
                    
                    file_metadata.append({
                        "relative_path": relative_path,
                        "storage_path": storage_path,
                        "public_url": public_url,
                        "size_bytes": len(file_content),
                        "file_extension": file_ext,
                        "content_type": content_type
                    })
                    
                except Exception as e:
                    error_msg = str(e)
                    if "handshake operation timed out" in error_msg:
                        print(f"DEBUG: SSL timeout for file {relative_path}, will retry later")
                        skipped_files.append({"path": relative_path, "reason": "ssl_timeout", "error": error_msg})
                    else:
                        print(f"DEBUG: Error processing file {relative_path}: {error_msg}")
                        skipped_files.append({"path": relative_path, "reason": "processing_failed", "error": error_msg})
        
        # Process files in batches to avoid overwhelming the API
        batch_size = 10
        for i in range(0, len(all_files), batch_size):
            batch = all_files[i:i + batch_size]
            await asyncio.gather(*[process_file(file_info) for file_info in batch])
            
            # Delay between batches to be gentle on APIs
            if i + batch_size < len(all_files):
                await asyncio.sleep(2)
        
        return {
            "base_path": base_path,
            "file_count": len(stored_files),
            "files": stored_files,
            "file_metadata": file_metadata,
            "skipped_files": skipped_files,
            "skipped_count": len(skipped_files)
        }
        
    except Exception as e:
        print(f"DEBUG: File extraction and storage exception: {str(e)}")
        raise StorageError(f"File extraction and storage failed: {str(e)}")


def is_binary_file(file_ext: str) -> bool:
    """Determine if a file extension indicates a binary file."""
    binary_extensions = {
        '.exe', '.dll', '.so', '.dylib', '.bin', '.app', '.deb', '.rpm', '.msi',
        '.zip', '.tar', '.gz', '.rar', '.7z', '.bz2', '.xz',
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg', '.ico', '.webp',
        '.mp3', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm',
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        '.woff', '.woff2', '.ttf', '.otf', '.eot',
        '.db', '.sqlite', '.sqlite3', '.mdb', '.accdb',
        '.pyc', '.pyo', '.class', '.jar', '.war', '.ear',
        '.o', '.obj', '.lib', '.a', '.dylib', '.so',
        '.map', '.min.js', '.min.css'
    }
    return file_ext.lower() in binary_extensions


def should_skip_file(relative_path: str) -> bool:
    """Determine if a file should be skipped based on its path."""
    if not relative_path:
        return True
        
    skip_patterns = [
        '.git/',
        'node_modules/',
        '__pycache__/',
        '.pytest_cache/',
        '.venv/',
        'venv/',
        'env/',
        '.env',
        '.DS_Store',
        'Thumbs.db',
        '.gitignore',
        '.gitattributes',
        'package-lock.json',
        'yarn.lock',
        'Pipfile.lock',
        'poetry.lock'
    ]
    
    return any(pattern in relative_path for pattern in skip_patterns)


def get_content_type(file_ext: str) -> str:
    """Get content type based on file extension."""
    content_types = {
        '.py': 'text/x-python',
        '.js': 'text/javascript',
        '.jsx': 'text/javascript',
        '.ts': 'text/typescript',
        '.tsx': 'text/typescript',
        '.java': 'text/x-java-source',
        '.c': 'text/x-c',
        '.cpp': 'text/x-c++',
        '.h': 'text/x-c',
        '.hpp': 'text/x-c++',
        '.cs': 'text/x-csharp',
        '.php': 'text/x-php',
        '.rb': 'text/x-ruby',
        '.go': 'text/x-go',
        '.rs': 'text/x-rust',
        '.swift': 'text/x-swift',
        '.kt': 'text/x-kotlin',
        '.scala': 'text/x-scala',
        '.dart': 'text/x-dart',
        '.html': 'text/html',
        '.css': 'text/css',
        '.scss': 'text/x-scss',
        '.sass': 'text/x-sass',
        '.less': 'text/x-less',
        '.json': 'application/json',
        '.xml': 'application/xml',
        '.yaml': 'text/yaml',
        '.yml': 'text/yaml',
        '.md': 'text/markdown',
        '.txt': 'text/plain',
        '.sql': 'text/x-sql',
        '.sh': 'text/x-shellscript',
        '.bash': 'text/x-shellscript',
        '.zsh': 'text/x-shellscript',
        '.fish': 'text/x-shellscript',
        '.dockerfile': 'text/x-dockerfile',
        '.dockerignore': 'text/plain',
        '.gitignore': 'text/plain',
        '.gitattributes': 'text/plain'
    }
    
    return content_types.get(file_ext, 'text/plain')


def save_repo_to_database(owner: str, repo: str, repo_data: Dict[str, Any], 
                         analysis_result: Dict[str, Any], file_storage_info: Dict[str, Any], 
                         user_id: str, window_days: int, max_commits: int) -> str:
    """Save repository and analysis data to consolidated repos table."""
    print(f"DEBUG: save_repo_to_database - owner: {owner}, repo: {repo}, user_id: {user_id}")
    print(f"DEBUG: repo_data: {repo_data}")
    print(f"DEBUG: analysis_result keys: {list(analysis_result.keys()) if analysis_result else 'None'}")
    
    if not supabase:
        raise DatabaseError("Supabase client not initialized")
    
    try:
        # Prepare file metadata for JSONB storage
        file_metadata = file_storage_info.get("file_metadata", [])
        print(f"DEBUG: file_metadata: {file_metadata}")
        
        # Create consolidated repository record
        repo_insert = {
            "user_id": str(user_id),
            "owner": owner,
            "name": repo,
            "full_name": f"{owner}/{repo}",
            "description": repo_data.get("description"),
            "html_url": repo_data.get("html_url", f"https://github.com/{owner}/{repo}"),
            "clone_url": repo_data.get("clone_url"),
            "default_branch": repo_data.get("default_branch", "main"),
            "language": repo_data.get("language"),
            "stars_count": repo_data.get("stargazers_count", 0),
            "forks_count": repo_data.get("forks_count", 0),
            "size_bytes": repo_data.get("size", 0),
            "window_days": window_days,
            "max_commits": max_commits,
            "languages": analysis_result.get("languages", {}),
            "team_data": analysis_result.get("team", {}),
            "commits_data": analysis_result.get("commits", {}),
            "raw_analysis": analysis_result,
            "file_storage_base_path": file_storage_info.get("base_path"),
            "file_count": file_storage_info.get("file_count", 0),
            "files_ready_for_embedding": file_storage_info.get("file_count", 0) > 0,
            "file_metadata": file_metadata
        }
        
        # Upsert the repository (update if exists, insert if new)
        repo_result = supabase.table("repos").upsert(
            repo_insert, 
            on_conflict="full_name"
        ).execute()
        
        if repo_result.data:
            return repo_result.data[0]["id"]
        else:
            raise DatabaseError("Failed to save repository")
            
    except Exception as e:
        raise DatabaseError(f"Database operation failed: {str(e)}")


async def get_repo_info(client: httpx.AsyncClient, owner: str, repo: str) -> Dict[str, Any]:
    """Get basic repository information from GitHub."""
    url = f"https://api.github.com/repos/{owner}/{repo}"
    response = await make_github_request(client, url)
    return response.json()


async def analyze_repo(repo_url: str, window_days: int = 3650, max_commits: int = 500) -> Dict[str, Any]:
    """Analyze a GitHub repository using REST API with proper error handling."""
    owner, repo = parse_repo(repo_url)
    since = (datetime.utcnow() - timedelta(days=window_days)).isoformat() + "Z"

    timeout = httpx.Timeout(60.0, connect=30.0, read=30.0, write=30.0, pool=30.0)
    limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)

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


async def analyze_and_store_repo(repo_url: str, user_id: str, window_days: int = 3650, 
                                max_commits: int = 500, download_zipball: bool = True) -> Dict[str, Any]:
    """Analyze a GitHub repository and store results in database with file extraction for vector embedding."""
    print(f"DEBUG: Starting analyze_and_store_repo with repo_url: {repo_url}, user_id: {user_id}")
    try:
        owner, repo = parse_repo(repo_url)
        print(f"DEBUG: Parsed repo - owner: {owner}, repo: {repo}")
    except Exception as e:
        print(f"DEBUG: Error parsing repo URL: {e}")
        raise
    since = (datetime.utcnow() - timedelta(days=window_days)).isoformat() + "Z"

    timeout = httpx.Timeout(60.0, connect=30.0, read=30.0, write=30.0, pool=30.0)
    limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)

    try:
        async with httpx.AsyncClient(timeout=timeout, limits=limits) as client:
            # Get basic repo info
            print(f"DEBUG: Getting repo info for {owner}/{repo}")
            repo_data = await get_repo_info(client, owner, repo)
            print(f"DEBUG: Repo data: {repo_data}")
            
            # Perform analysis
            print(f"DEBUG: Starting analysis for {repo_url}")
            analysis_result = await analyze_repo(repo_url, window_days, max_commits)
            print(f"DEBUG: Analysis result: {analysis_result}")
            
            # Check if analysis was successful
            if not analysis_result:
                return {"error": "Analysis returned no results"}
            
            if "error" in analysis_result:
                return analysis_result
            
            # Save to database first to get repo_id
            repo_id = save_repo_to_database(owner, repo, repo_data, analysis_result, {}, user_id, window_days, max_commits)
            
            file_storage_info = None
            if download_zipball:
                print(f"DEBUG: File download enabled, starting file extraction...")
                try:
                    # Use Contents API instead of zipball for better file size handling
                    file_storage_info = await extract_and_store_files_contents_api(
                        client, owner, repo, repo_id, user_id, repo_data.get("default_branch", "main")
                    )
                    
                    analysis_result["file_storage"] = {
                        "base_path": file_storage_info["base_path"],
                        "file_count": file_storage_info["file_count"],
                        "files_ready_for_embedding": True,
                        "skipped_files": file_storage_info.get("skipped_files", []),
                        "skipped_count": file_storage_info.get("skipped_count", 0)
                    }
                    
                except (GitHubAPIError, StorageError) as e:
                    # Continue without file extraction if download/upload fails
                    analysis_result["warning"] = f"Failed to download/extract files: {str(e)}"
                    file_storage_info = {"base_path": None, "file_count": 0, "file_metadata": []}
            
            # Update the repository record with file storage info
            if file_storage_info:
                update_data = {
                    "file_storage_base_path": file_storage_info.get("base_path"),
                    "file_count": file_storage_info.get("file_count", 0),
                    "files_ready_for_embedding": file_storage_info.get("file_count", 0) > 0,
                    "file_metadata": file_storage_info.get("file_metadata", [])
                }
                supabase.table("repos").update(update_data).eq("id", repo_id).execute()
            
            analysis_result["repo_id"] = repo_id
            analysis_result["stored_in_db"] = True
            
            if file_storage_info and file_storage_info.get("file_count", 0) > 0:
                analysis_result["files_stored"] = True
                analysis_result["file_count"] = file_storage_info.get("file_count", 0)
            else:
                analysis_result["files_stored"] = False
            
            return analysis_result
                    
    except DatabaseError as e:
        analysis_result["warning"] = f"Failed to save to database: {str(e)}"
        analysis_result["stored_in_db"] = False
            
        return analysis_result
            
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
