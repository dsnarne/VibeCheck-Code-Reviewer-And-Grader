import os
import json
from typing import Dict, List, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def analyze_code_quality_with_chatgpt(analysis_data: Dict[str, Any], file_metadata: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Use ChatGPT to analyze code quality and provide scoring based on repository analysis data.
    """
    try:
        # Prepare the analysis data for ChatGPT
        prompt_data = prepare_analysis_for_chatgpt(analysis_data, file_metadata)
        
        # Create the prompt for ChatGPT
        prompt = create_scoring_prompt(prompt_data)
        
        # Call ChatGPT API
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert code reviewer and software engineer. Analyze the provided repository data and provide detailed scoring across multiple dimensions. Return your response as valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        # Parse the response
        scoring_result = json.loads(response.choices[0].message.content)
        
        return scoring_result
        
    except Exception as e:
        print(f"Error in ChatGPT analysis: {str(e)}")
        # Return default scoring if ChatGPT fails
        return get_default_scoring(analysis_data)

def prepare_analysis_for_chatgpt(analysis_data: Dict[str, Any], file_metadata: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Prepare analysis data in a format suitable for ChatGPT processing."""
    
    # Extract key metrics
    languages = analysis_data.get("languages", {})
    team_data = analysis_data.get("team", {})
    commits_data = analysis_data.get("commits", {})
    
    # Calculate some basic metrics
    total_commits = commits_data.get("count", 0)
    gini_contribution = team_data.get("giniContribution", 0)
    top_contributors_share = team_data.get("topContributorsShare", 0)
    median_compartmentalization = commits_data.get("medianCompartmentalization", 1.0)
    
    # Get file information
    file_count = len(file_metadata)
    file_types = {}
    for file_info in file_metadata:
        ext = file_info.get("file_extension", "").lower()
        if ext:
            file_types[ext] = file_types.get(ext, 0) + 1
    
    # Get top contributors
    contributions = team_data.get("contributions", [])
    top_contributors = sorted(contributions, key=lambda x: x.get("netLines", 0), reverse=True)[:5]
    
    return {
        "repository_info": {
            "repo_name": analysis_data.get("repo", "Unknown"),
            "total_commits": total_commits,
            "file_count": file_count,
            "languages": languages,
            "file_types": file_types
        },
        "team_metrics": {
            "gini_contribution": gini_contribution,
            "top_contributors_share": top_contributors_share,
            "top_contributors": top_contributors,
            "total_contributors": len(contributions)
        },
        "code_metrics": {
            "median_compartmentalization": median_compartmentalization,
            "mean_compartmentalization": commits_data.get("meanCompartmentalization", 1.0)
        },
        "file_metadata": file_metadata[:20]  # Limit to first 20 files for context
    }

def create_scoring_prompt(data: Dict[str, Any]) -> str:
    """Create a detailed prompt for ChatGPT to analyze the repository."""
    
    repo_info = data["repository_info"]
    team_metrics = data["team_metrics"]
    code_metrics = data["code_metrics"]
    
    prompt = f"""
Analyze this GitHub repository and provide a comprehensive scoring across multiple dimensions. Here's the data:

REPOSITORY: {repo_info['repo_name']}
- Total commits: {repo_info['total_commits']}
- File count: {repo_info['file_count']}
- Languages: {json.dumps(repo_info['languages'], indent=2)}
- File types: {json.dumps(repo_info['file_types'], indent=2)}

TEAM METRICS:
- Gini coefficient (contribution inequality): {team_metrics['gini_contribution']:.3f}
- Top contributors share: {team_metrics['top_contributors_share']:.3f}
- Total contributors: {team_metrics['total_contributors']}
- Top contributors: {json.dumps(team_metrics['top_contributors'], indent=2)}

CODE METRICS:
- Median compartmentalization: {code_metrics['median_compartmentalization']:.3f}
- Mean compartmentalization: {code_metrics['mean_compartmentalization']:.3f}

Please provide a JSON response with the following structure:
{{
    "overall_score": <number 0-100>,
    "ai_percentage": <estimated percentage of AI-generated code 0-100>,
    "previous_score": <optional previous score for comparison>,
    "scores": [
        {{
            "title": "Quality",
            "score": <number 0-100>,
            "color": "hsl(var(--quality))",
            "description": "Code maintainability & complexity"
        }},
        {{
            "title": "Security",
            "score": <number 0-100>,
            "color": "hsl(var(--security))",
            "description": "Vulnerabilities & best practices"
        }},
        {{
            "title": "Git Hygiene",
            "score": <number 0-100>,
            "color": "hsl(var(--git))",
            "description": "Commit quality & PR practices"
        }},
        {{
            "title": "Style",
            "score": <number 0-100>,
            "color": "hsl(var(--style))",
            "description": "Consistency & conventions"
        }},
        {{
            "title": "Originality",
            "score": <number 0-100>,
            "color": "hsl(var(--originality))",
            "description": "Unique implementations"
        }},
        {{
            "title": "Team Balance",
            "score": <number 0-100>,
            "color": "hsl(var(--team))",
            "description": "Contribution distribution"
        }}
    ],
    "radar_data": [
        {{"category": "Quality", "score": <number>, "fullMark": 100}},
        {{"category": "Security", "score": <number>, "fullMark": 100}},
        {{"category": "Git", "score": <number>, "fullMark": 100}},
        {{"category": "Style", "score": <number>, "fullMark": 100}},
        {{"category": "Originality", "score": <number>, "fullMark": 100}},
        {{"category": "Team", "score": <number>, "fullMark": 100}}
    ],
    "files": [
        {{
            "name": "<filename>",
            "path": "<filepath>",
            "ai_percentage": <estimated AI percentage>,
            "quality": <quality score 0-100>,
            "flags": ["<flag1>", "<flag2>"]
        }}
    ],
    "analysis": "<detailed analysis text>",
    "recommendations": ["<recommendation1>", "<recommendation2>", "<recommendation3>"]
}}

Scoring guidelines:
- Quality: Based on code structure, maintainability, and complexity
- Security: Based on potential vulnerabilities and security practices
- Git Hygiene: Based on commit patterns, PR practices, and version control discipline
- Style: Based on code consistency, naming conventions, and formatting
- Originality: Based on unique implementations vs copy-paste patterns
- Team Balance: Based on contribution distribution and collaboration patterns

AI Percentage estimation:
- Look for patterns that suggest AI-generated code (repetitive structures, generic variable names, etc.)
- Consider the complexity and originality of implementations
- Factor in the team's coding patterns and consistency

Provide realistic scores based on the actual data provided. Be critical but fair in your assessment.
"""
    
    return prompt

def get_default_scoring(analysis_data: Dict[str, Any]) -> Dict[str, Any]:
    """Provide default scoring when ChatGPT analysis fails."""
    
    # Calculate basic scores from available data
    languages = analysis_data.get("languages", {})
    team_data = analysis_data.get("team", {})
    commits_data = analysis_data.get("commits", {})
    
    # Basic quality score based on compartmentalization
    quality_score = min(95, max(60, int(commits_data.get("medianCompartmentalization", 0.5) * 100)))
    
    # Security score (default to moderate)
    security_score = 75
    
    # Git hygiene based on commit patterns
    commit_count = commits_data.get("count", 0)
    git_score = min(90, max(50, 60 + (commit_count // 10)))
    
    # Style score (default to good)
    style_score = 80
    
    # Originality based on team distribution
    gini = team_data.get("giniContribution", 0.5)
    originality_score = min(90, max(40, int(100 - (gini * 50))))
    
    # Team balance
    team_score = min(95, max(50, int(100 - (team_data.get("giniContribution", 0.5) * 100))))
    
    overall_score = int((quality_score + security_score + git_score + style_score + originality_score + team_score) / 6)
    
    return {
        "overall_score": overall_score,
        "ai_percentage": 25,  # Default moderate AI percentage
        "scores": [
            {
                "title": "Quality",
                "score": quality_score,
                "color": "hsl(var(--quality))",
                "description": "Code maintainability & complexity"
            },
            {
                "title": "Security",
                "score": security_score,
                "color": "hsl(var(--security))",
                "description": "Vulnerabilities & best practices"
            },
            {
                "title": "Git Hygiene",
                "score": git_score,
                "color": "hsl(var(--git))",
                "description": "Commit quality & PR practices"
            },
            {
                "title": "Style",
                "score": style_score,
                "color": "hsl(var(--style))",
                "description": "Consistency & conventions"
            },
            {
                "title": "Originality",
                "score": originality_score,
                "color": "hsl(var(--originality))",
                "description": "Unique implementations"
            },
            {
                "title": "Team Balance",
                "score": team_score,
                "color": "hsl(var(--team))",
                "description": "Contribution distribution"
            }
        ],
        "radar_data": [
            {"category": "Quality", "score": quality_score, "fullMark": 100},
            {"category": "Security", "score": security_score, "fullMark": 100},
            {"category": "Git", "score": git_score, "fullMark": 100},
            {"category": "Style", "score": style_score, "fullMark": 100},
            {"category": "Originality", "score": originality_score, "fullMark": 100},
            {"category": "Team", "score": team_score, "fullMark": 100}
        ],
        "files": [],
        "analysis": "Default analysis based on available metrics. ChatGPT analysis was not available.",
        "recommendations": [
            "Improve code compartmentalization",
            "Enhance team contribution balance",
            "Consider security best practices review"
        ]
    }
