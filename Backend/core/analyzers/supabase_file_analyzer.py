"""
Alternative code issue analyzer that works with Supabase stored files.
Since files are stored in Supabase Storage, we need to download them first.
"""

from core.analyzers.code_issue_analyzer import CodeIssueAnalyzer
from core.services.supabase import supabase
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


async def analyze_repository_files_from_supabase(file_metadata: List[Dict[str, Any]], base_path: str) -> Dict[str, Any]:
    """
    Analyze repository files stored in Supabase Storage.
    
    Args:
        file_metadata: List of file metadata from database
        base_path: Base path in Supabase storage
    
    Returns:
        Dictionary with categorized issues
    """
    if not supabase:
        logger.error("Supabase client not initialized")
        return {
            "total_issues": 0,
            "issues": {},
            "summary": {}
        }
    
    analyzer = CodeIssueAnalyzer()
    all_issues = []
    
    # Download and analyze files from Supabase
    for file_info in file_metadata:
        storage_path = file_info.get('storage_path', '')
        file_path = file_info.get('relative_path', file_info.get('path', ''))
        file_extension = file_info.get('file_extension', '')
        
        if not storage_path:
            logger.warning(f"Skipping file without storage_path: {file_info}")
            continue
        
        try:
            # Download file from Supabase storage
            file_data = supabase.storage.from_("repo-files").download(storage_path)
            
            if file_data:
                # Convert bytes to string for analysis
                try:
                    content = file_data.decode('utf-8')
                except UnicodeDecodeError:
                    # Skip binary files
                    logger.warning(f"Skipping binary file: {file_path}")
                    continue
                
                # Analyze the file
                try:
                    file_type = analyzer._detect_file_type(file_path)
                    issues = analyzer.analyze_file(file_path, content, file_type)
                    logger.info(f"Analyzed {file_path}: Found {len(issues)} issues")
                    all_issues.extend(issues)
                except Exception as e:
                    logger.error(f"Error analyzing file {file_path}: {str(e)}")
                    continue
            
        except Exception as e:
            logger.warning(f"Could not analyze file {storage_path}: {str(e)}")
    
    # Categorize issues
    categorized = analyzer.categorize_issues(all_issues)
    
    # Format for API response
    result = {
        'total_issues': len(all_issues),
        'issues': {cat: [issue.to_dict() for issue in issues] for cat, issues in categorized.items()},
        'summary': {
            cat: {
                'total': len(issues),
                'errors': len([i for i in issues if i.severity == 'error']),
                'warnings': len([i for i in issues if i.severity == 'warning']),
                'info': len([i for i in issues if i.severity == 'info'])
            }
            for cat, issues in categorized.items()
        }
    }
    
    return result
