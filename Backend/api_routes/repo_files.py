"""
API route to get repository files directly from database with quality scores
"""
from fastapi import APIRouter, HTTPException
from core.services.supabase import supabase
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/repos", tags=["Repository Files"])

def calculate_file_quality_score(file_metadata: Dict, all_issues: Dict) -> int:
    """Calculate a quality score (0-100) for a file based on issues"""
    # Start with a baseline score
    score = 100
    
    # Get file path
    file_path = file_metadata.get('relative_path', file_metadata.get('path', ''))
    
    # Count issues for this file
    issue_counts = {'error': 0, 'warning': 0, 'info': 0}
    
    for category, issues in all_issues.items():
        for issue in issues:
            if issue.get('file_path') == file_path or issue.get('file') == file_path:
                severity = issue.get('severity', 'info').lower()
                if severity in ['error', 'high']:
                    issue_counts['error'] += 1
                    score -= 15  # Heavy penalty for errors
                elif severity in ['warning', 'medium']:
                    issue_counts['warning'] += 1
                    score -= 5  # Medium penalty for warnings
                else:
                    issue_counts['info'] += 1
                    score -= 1  # Light penalty for info
    
    # Ensure score doesn't go below 0
    return max(0, min(100, score))

@router.get("/{repo_id}/files/list")
async def get_repo_files_list(repo_id: str):
    """Get list of all files in a repository with quality scores"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        result = supabase.table("repos").select("*").eq("id", repo_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Repository not found")
        
        repo = result.data[0]
        file_metadata = repo.get("file_metadata", [])
        
        # Get all issues for scoring
        all_issues = {}
        try:
            # Try to get issues from file_analysis or score_issues
            file_analysis = repo.get("file_analysis", [])
            score_issues = repo.get("score_issues", {})
            
            logger.info(f"File analysis entries: {len(file_analysis)}, Score issues: {list(score_issues.keys())}")
            
            # Merge issues by category
            for category in ['quality', 'security', 'style']:
                category_issues = []
                
                # Check file_analysis
                for analysis in file_analysis:
                    issues_list = analysis.get('issues', [])
                    if issues_list:
                        category_issues.extend(issues_list)
                
                # Check score_issues (case-insensitive)
                for key, issues in score_issues.items():
                    if key.lower() == category:
                        category_issues.extend(issues)
                
                all_issues[category] = category_issues
                logger.info(f"Category {category}: {len(category_issues)} issues")
                
        except Exception as e:
            logger.warning(f"Could not load issues for scoring: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        files = []
        for file in file_metadata:
            # Calculate quality score
            quality_score = calculate_file_quality_score(file, all_issues)
            
            # Extract filename from path
            file_path = file.get('relative_path', file.get('path', ''))
            file_name = file_path.split('/')[-1] if file_path else 'unknown'
            
            files.append({
                "name": file_name,
                "path": file_path,
                "score": quality_score,
                "issues": [],
                "aiPercentage": 0,
                "quality": quality_score
            })
        
        logger.info(f"Generated quality scores for {len(files)} files")
        return {"files": files, "count": len(files)}
        
    except Exception as e:
        logger.error(f"Error getting repo files: {e}")
        raise HTTPException(status_code=500, detail=str(e))

