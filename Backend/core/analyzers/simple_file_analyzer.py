import ast
import re
from typing import List, Dict, Any, Optional
import httpx
import asyncio

async def analyze_file_content(file_url: str, file_path: str, file_type: str = "python") -> Dict[str, Any]:
    """Simple file analyzer that fetches and analyzes file content."""
    try:
        # Fetch file content
        async with httpx.AsyncClient() as client:
            response = await client.get(file_url, timeout=10.0)
            content = response.text
            
        issues = []
        
        # Security patterns
        security_patterns = [
            (r'eval\s*\(', 'Use of eval() function', 'security', 'high'),
            (r'exec\s*\(', 'Use of exec() function', 'security', 'high'),
            (r'pickle\.loads?', 'Unsafe deserialization with pickle', 'security', 'high'),
            (r'password\s*=\s*["\']', 'Hardcoded password', 'security', 'medium'),
            (r'api_key\s*=\s*["\']', 'Hardcoded API key', 'security', 'high'),
        ]
        
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for pattern, desc, category, severity in security_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append({
                        'file': file_path,
                        'line': line_num,
                        'category': category,
                        'severity': severity,
                        'type': 'security_pattern',
                        'description': desc,
                        'snippet': line.strip(),
                        'column': 0
                    })
        
        # Quality patterns
        quality_patterns = [
            (r'except\s*:', 'Bare except clause', 'quality', 'medium'),
            (r'if\s+True:', 'Redundant if True condition', 'quality', 'low'),
            (r'if\s+False:', 'Dead code - if False condition', 'quality', 'medium'),
            (r'import\s+\*', 'Wildcard import', 'quality', 'low'),
        ]
        
        for line_num, line in enumerate(lines, 1):
            for pattern, desc, category, severity in quality_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append({
                        'file': file_path,
                        'line': line_num,
                        'category': category,
                        'severity': severity,
                        'type': 'quality_pattern',
                        'description': desc,
                        'snippet': line.strip(),
                        'column': 0
                    })
        
        # Calculate basic metrics
        loc = len([l for l in lines if l.strip() and not l.strip().startswith('#')])
        complexity = content.count('if ') + content.count('while ') + content.count('for ')
        
        return {
            'file_path': file_path,
            'issues': issues,
            'metrics': {
                'lines_of_code': loc,
                'cyclomatic_complexity': complexity
            }
        }
        
    except Exception as e:
        return {
            'file_path': file_path,
            'issues': [],
            'metrics': {'lines_of_code': 0, 'cyclomatic_complexity': 0}
        }

async def analyze_repository_files(file_metadata: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze all files in repository."""
    results = []
    
    for file_info in file_metadata[:20]:  # Limit to first 20 files
        file_type = file_info.get('file_extension', '').replace('.', '')
        result = await analyze_file_content(
            file_info['public_url'],
            file_info['relative_path'],
            file_type
        )
        results.append(result)
        
    # Categorize issues by score type
    score_issues = {
        'Security': [],
        'Quality': [],
        'Style': []
    }
    
    for result in results:
        for issue in result['issues']:
            category = issue['category']
            if category in score_issues:
                score_issues[category].append(issue)
    
    return {
        'file_analyses': results,
        'score_issues': score_issues
    }

