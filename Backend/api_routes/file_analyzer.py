"""
API endpoint for analyzing individual files and returning quality scores
"""
from fastapi import APIRouter, HTTPException
from core.services.supabase import supabase
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/repos", tags=["File Analysis"])

@router.get("/{repo_id}/files/{file_path:path}/analyze")
async def analyze_file(repo_id: str, file_path: str):
    """
    Analyze a specific file and return quality score and issues.
    This runs analysis on-demand when viewing a file.
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        # Get repository
        result = supabase.table("repos").select("*").eq("id", repo_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Repository not found")
        
        repo = result.data[0]
        file_metadata = repo.get("file_metadata", [])
        
        # Find the file in metadata
        file_info = None
        for file in file_metadata:
            if file.get('relative_path') == file_path or file.get('path') == file_path:
                file_info = file
                break
        
        if not file_info:
            raise HTTPException(status_code=404, detail="File not found in repository")
        
        # Download file content
        storage_path = file_info.get('storage_path')
        if not storage_path:
            raise HTTPException(status_code=404, detail="Storage path not found")
        
        file_data = supabase.storage.from_("repo-files").download(storage_path)
        
        if not file_data:
            raise HTTPException(status_code=404, detail="Could not download file")
        
        content = file_data.decode('utf-8')
        
        # Analyze the file content
        from core.analyzers.code_issue_analyzer import CodeIssueAnalyzer
        analyzer = CodeIssueAnalyzer()
        
        # Analyze for issues
        logger.info(f"Analyzing file: {file_path}")
        issue_list = analyzer.analyze_file(file_path, content)
        
        # Group issues by category
        issues = {
            'quality': [],
            'security': [],
            'style': []
        }
        
        for issue in issue_list:
            category = issue.category.lower()
            if category in issues:
                issues[category].append({
                    'line': issue.line_number,
                    'severity': issue.severity,
                    'issue': issue.message,
                    'suggestion': issue.suggestion,
                    'category': issue.category
                })
        
        # Calculate quality score based on issues found
        quality_score = 100
        issue_summary = []
        
        for category, issue_list in issues.items():
            for issue in issue_list:
                severity = issue.get('severity', 'info').lower()
                
                if severity in ['error', 'high']:
                    quality_score -= 15
                    issue_summary.append({
                        'category': category,
                        'severity': severity,
                        'issue': issue.get('issue', ''),
                        'line': issue.get('line', 0)
                    })
                elif severity in ['warning', 'medium']:
                    quality_score -= 5
                    issue_summary.append({
                        'category': category,
                        'severity': severity,
                        'issue': issue.get('issue', ''),
                        'line': issue.get('line', 0)
                    })
                else:
                    quality_score -= 1
                    issue_summary.append({
                        'category': category,
                        'severity': severity,
                        'issue': issue.get('issue', ''),
                        'line': issue.get('line', 0)
                    })
        
        # Ensure score doesn't go negative
        quality_score = max(0, quality_score)
        
        logger.info(f"File {file_path}: quality_score={quality_score}, issues={len(issue_summary)}")
        
        return {
            "file_path": file_path,
            "quality_score": quality_score,
            "issues_found": len(issue_summary),
            "issues": issue_summary,
            "categories": list(issues.keys())
        }
        
    except Exception as e:
        logger.error(f"Error analyzing file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to analyze file: {str(e)}")

