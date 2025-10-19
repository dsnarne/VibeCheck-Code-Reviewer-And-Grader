import os
import json
import logging
from typing import Dict, List, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def clean_chatgpt_response(content: str) -> str:
    """
    Clean ChatGPT response content to extract valid JSON.
    Handles markdown code blocks and other formatting issues.
    """
    if not content:
        return content
    
    # Remove leading/trailing whitespace
    content = content.strip()
    
    # Check if content is wrapped in markdown code blocks
    if content.startswith("```json") and content.endswith("```"):
        # Extract content between ```json and ```
        start_marker = "```json"
        end_marker = "```"
        start_idx = content.find(start_marker) + len(start_marker)
        end_idx = content.rfind(end_marker)
        
        if start_idx > len(start_marker) - 1 and end_idx > start_idx:
            content = content[start_idx:end_idx].strip()
            logger.info("Extracted JSON from markdown code block")
    
    # Check for other markdown patterns
    elif content.startswith("```") and content.endswith("```"):
        # Generic code block without language specification
        start_marker = "```"
        end_marker = "```"
        start_idx = content.find(start_marker) + len(start_marker)
        end_idx = content.rfind(end_marker)
        
        if start_idx > len(start_marker) - 1 and end_idx > start_idx:
            content = content[start_idx:end_idx].strip()
            logger.info("Extracted JSON from generic markdown code block")
    
    # Remove any remaining markdown artifacts
    content = content.replace("```json", "").replace("```", "").strip()
    
    # Remove any leading/trailing non-JSON text
    lines = content.split('\n')
    json_start = 0
    json_end = len(lines)
    
    # Find the first line that looks like JSON (starts with { or [)
    for i, line in enumerate(lines):
        if line.strip().startswith(('{', '[')):
            json_start = i
            break
    
    # Find the last line that looks like JSON (ends with } or ])
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip().endswith(('}', ']')):
            json_end = i + 1
            break
    
    if json_start < json_end:
        content = '\n'.join(lines[json_start:json_end])
        logger.info(f"Extracted JSON from lines {json_start} to {json_end}")
    
    return content.strip()

def analyze_code_quality_with_chatgpt(analysis_data: Dict[str, Any], file_metadata: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Use ChatGPT to analyze code quality and provide scoring based on repository analysis data.
    """
    try:
        logger.info("Starting ChatGPT analysis...")
        
        # Check if API key is available
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY not found in environment variables")
            raise ValueError("OpenAI API key not configured")
        
        logger.info(f"OpenAI API key found: {api_key[:8]}...")
        
        # Prepare the analysis data for ChatGPT
        logger.info("Preparing analysis data for ChatGPT...")
        prompt_data = prepare_analysis_for_chatgpt(analysis_data, file_metadata)
        logger.info(f"Prepared data keys: {list(prompt_data.keys())}")
        
        # Create the prompt for ChatGPT
        logger.info("Creating scoring prompt...")
        prompt = create_scoring_prompt(prompt_data)
        logger.info(f"Prompt length: {len(prompt)} characters")
        
        # Log a sample of the prompt for debugging
        logger.info(f"Prompt sample (first 500 chars): {prompt[:500]}...")
        
        # Call ChatGPT API - try different models in order of preference
        models_to_try = ["gpt-4o-mini"]
        response = None
        
        for model in models_to_try:
            try:
                logger.info(f"Trying OpenAI API with model: {model}")
                response = client.chat.completions.create(
                    model=model,
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
                logger.info(f"Successfully connected to OpenAI API with model: {model}")
                break
            except Exception as e:
                logger.warning(f"Failed to connect with model {model}: {str(e)}")
                if "model_not_found" in str(e) or "does not have access" in str(e):
                    continue
                else:
                    raise e
        
        if response is None:
            raise Exception("No available OpenAI models found for this API key")
        
        logger.info("OpenAI API call successful")
        logger.info(f"Response object type: {type(response)}")
        logger.info(f"Response choices count: {len(response.choices) if hasattr(response, 'choices') else 'N/A'}")
        
        # Check if we have a valid response
        if not hasattr(response, 'choices') or not response.choices:
            logger.error("No choices in OpenAI response")
            raise ValueError("Invalid response from OpenAI API")
        
        # Get the content
        content = response.choices[0].message.content
        logger.info(f"Response content length: {len(content)} characters")
        logger.info(f"Response content sample (first 200 chars): {content[:200]}...")
        
        # Clean the response content before parsing
        logger.info("Cleaning response content...")
        cleaned_content = clean_chatgpt_response(content)
        logger.info(f"Cleaned content length: {len(cleaned_content)} characters")
        logger.info(f"Cleaned content sample (first 200 chars): {cleaned_content[:200]}...")
        
        # Parse the response
        logger.info("Parsing JSON response...")
        scoring_result = json.loads(cleaned_content)
        logger.info("JSON parsing successful")
        logger.info(f"Parsed result keys: {list(scoring_result.keys()) if isinstance(scoring_result, dict) else 'Not a dict'}")
        
        # Validate the response structure
        required_keys = ['overall_score', 'scores', 'radar_data']
        missing_keys = [key for key in required_keys if key not in scoring_result]
        if missing_keys:
            logger.warning(f"Missing required keys in response: {missing_keys}")
        
        logger.info("ChatGPT analysis completed successfully")
        return scoring_result
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {str(e)}")
        logger.error(f"Failed to parse cleaned content: {cleaned_content if 'cleaned_content' in locals() else 'Cleaned content not available'}")
        logger.error(f"Original content: {content if 'content' in locals() else 'Content not available'}")
        return get_default_scoring(analysis_data)
    except Exception as e:
        logger.error(f"Error in ChatGPT analysis: {str(e)}", exc_info=True)
        logger.error(f"Error type: {type(e).__name__}")
        # Return default scoring if ChatGPT fails
        return get_default_scoring(analysis_data)

def prepare_analysis_for_chatgpt(analysis_data: Dict[str, Any], file_metadata: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Prepare analysis data in a format suitable for ChatGPT processing."""
    
    logger.info("Preparing analysis data for ChatGPT...")
    logger.info(f"Input analysis_data keys: {list(analysis_data.keys())}")
    logger.info(f"File metadata count: {len(file_metadata)}")
    
    # Extract key metrics
    languages = analysis_data.get("languages", {})
    team_data = analysis_data.get("team", {})
    commits_data = analysis_data.get("commits", {})
    
    logger.info(f"Languages data: {languages}")
    logger.info(f"Team data keys: {list(team_data.keys())}")
    logger.info(f"Commits data keys: {list(commits_data.keys())}")
    
    # Calculate some basic metrics
    total_commits = commits_data.get("count", 0)
    gini_contribution = team_data.get("giniContribution", 0)
    top_contributors_share = team_data.get("topContributorsShare", 0)
    median_compartmentalization = commits_data.get("medianCompartmentalization", 1.0)
    
    logger.info(f"Calculated metrics - commits: {total_commits}, gini: {gini_contribution}, top_contributors_share: {top_contributors_share}")
    
    # Get file information
    file_count = len(file_metadata)
    file_types = {}
    for file_info in file_metadata:
        ext = file_info.get("file_extension", "").lower()
        if ext:
            file_types[ext] = file_types.get(ext, 0) + 1
    
    logger.info(f"File count: {file_count}, file types: {file_types}")
    
    # Get top contributors
    contributions = team_data.get("contributions", [])
    top_contributors = sorted(contributions, key=lambda x: x.get("netLines", 0), reverse=True)[:5]
    
    logger.info(f"Contributions count: {len(contributions)}")
    logger.info(f"Top contributors: {top_contributors}")
    
    prepared_data = {
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
    
    logger.info("Data preparation completed successfully")
    return prepared_data

def create_scoring_prompt(data: Dict[str, Any]) -> str:
    """Create a detailed prompt for ChatGPT to analyze the repository."""
    
    logger.info("Creating scoring prompt...")
    logger.info(f"Input data keys: {list(data.keys())}")
    
    repo_info = data["repository_info"]
    team_metrics = data["team_metrics"]
    code_metrics = data["code_metrics"]
    
    logger.info(f"Repository info: {repo_info}")
    logger.info(f"Team metrics: {team_metrics}")
    logger.info(f"Code metrics: {code_metrics}")
    
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
    
    logger.info(f"Prompt created successfully, length: {len(prompt)} characters")
    return prompt

def get_default_scoring(analysis_data: Dict[str, Any]) -> Dict[str, Any]:
    """Provide default scoring when ChatGPT analysis fails."""
    
    logger.warning("Using default scoring due to ChatGPT analysis failure")
    logger.info(f"Analysis data keys for default scoring: {list(analysis_data.keys())}")
    
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
    
    logger.info(f"Default scores calculated - Quality: {quality_score}, Security: {security_score}, Git: {git_score}, Style: {style_score}, Originality: {originality_score}, Team: {team_score}, Overall: {overall_score}")
    
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

def test_chatgpt_connection() -> bool:
    """Test function to verify ChatGPT API connection and configuration."""
    try:
        logger.info("Testing ChatGPT API connection...")
        
        # Check API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY not found in environment variables")
            return False
        
        # Test with a simple request - try different models
        models_to_try = ["gpt-3.5-turbo-1106", "gpt-3.5-turbo", "gpt-4o-mini", "gpt-4"]
        response = None
        
        for model in models_to_try:
            try:
                logger.info(f"Testing API connection with model: {model}")
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "user",
                            "content": "Respond with exactly: 'API connection successful'"
                        }
                    ],
                    max_tokens=10
                )
                logger.info(f"Successfully connected to OpenAI API with model: {model}")
                break
            except Exception as e:
                logger.warning(f"Failed to connect with model {model}: {str(e)}")
                if "model_not_found" in str(e) or "does not have access" in str(e):
                    continue
                else:
                    raise e
        
        if response is None:
            logger.error("No available OpenAI models found for this API key")
            return False
        
        content = response.choices[0].message.content
        cleaned_content = clean_chatgpt_response(content)
        logger.info(f"API test response: {cleaned_content}")
        
        if "successful" in cleaned_content.lower():
            logger.info("ChatGPT API connection test successful")
            return True
        else:
            logger.warning(f"Unexpected API response: {content}")
            return False
            
    except Exception as e:
        logger.error(f"ChatGPT API connection test failed: {str(e)}", exc_info=True)
        return False
