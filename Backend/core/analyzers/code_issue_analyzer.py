"""
Code Issue Analyzer for detecting code quality, security, and style issues.
Analyzes stored repository files and returns specific issues with line numbers.
"""

import os
import ast
import re
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class CodeIssue:
    """Represents a code issue found in a file."""
    file_path: str
    line_number: int
    issue_type: str
    severity: str  # 'error', 'warning', 'info'
    category: str  # 'quality', 'security', 'style', 'originality'
    message: str
    code_snippet: str
    suggestion: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "file": os.path.basename(self.file_path),
            "path": self.file_path,
            "line": self.line_number,
            "issue": self.message,
            "issue_type": self.issue_type,
            "severity": self.severity,
            "category": self.category,
            "codeSnippet": self.code_snippet,
            "suggestion": self.suggestion
        }


class CodeIssueAnalyzer:
    """Analyzes code files for quality, security, and style issues."""
    
    def __init__(self):
        self.issues: List[CodeIssue] = []
    
    def analyze_file(self, file_path: str, file_content: str, file_type: str = None) -> List[CodeIssue]:
        """
        Analyze a single file for code issues.
        
        Args:
            file_path: Path to the file
            file_content: Contents of the file
            file_type: Type of file (python, javascript, etc.)
        
        Returns:
            List of CodeIssue objects
        """
        self.issues = []
        
        if file_type is None:
            file_type = self._detect_file_type(file_path)
        
        if file_type == 'python':
            self._analyze_python(file_path, file_content)
        elif file_type == 'javascript' or file_type == 'typescript':
            self._analyze_javascript(file_path, file_content)
        else:
            self._analyze_generic(file_path, file_content)
        
        return self.issues
    
    def _detect_file_type(self, file_path: str) -> str:
        """Detect file type from extension."""
        ext = os.path.splitext(file_path)[1].lower()
        type_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.go': 'go',
            '.rs': 'rust',
            '.cpp': 'cpp',
            '.c': 'c',
        }
        return type_map.get(ext, 'generic')
    
    def _analyze_python(self, file_path: str, content: str):
        """Analyze Python code for issues."""
        try:
            lines = content.split('\n')
            
            # Parse AST to analyze code structure
            tree = ast.parse(content)
            
            # Check for various issues
            self._check_missing_type_hints(tree, lines, file_path)
            self._check_complex_functions(tree, lines, file_path)
            self._check_missing_docstrings(tree, lines, file_path)
            self._check_long_lines(lines, file_path)
            self._check_duplicate_code(tree, lines, file_path)
            self._check_security_issues(tree, lines, file_path)
            self._check_style_issues(lines, file_path)
            
        except SyntaxError as e:
            logger.warning(f"Could not parse {file_path}: {str(e)}")
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {str(e)}")
    
    def _check_missing_type_hints(self, tree: ast.AST, lines: List[str], file_path: str):
        """Check for missing type hints in functions."""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check if function has type hints
                if not node.args.args:
                    continue
                
                has_type_hints = any(
                    arg.annotation is not None 
                    for arg in node.args.args
                )
                
                if not has_type_hints and len(node.args.args) > 0:
                    # Get function code
                    func_line = node.lineno
                    func_code = self._get_code_snippet(lines, func_line, func_line + 3)
                    
                    self.issues.append(CodeIssue(
                        file_path=file_path,
                        line_number=func_line,
                        issue_type="missing_type_hints",
                        severity="warning",
                        category="quality",
                        message="Function missing type hints",
                        code_snippet=func_code,
                        suggestion="Add type hints: def function_name(param: type) -> return_type:"
                    ))
    
    def _check_complex_functions(self, tree: ast.AST, lines: List[str], file_path: str):
        """Check for overly complex functions (high cyclomatic complexity)."""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                complexity = self._calculate_complexity(node)
                
                if complexity > 5:  # Lower threshold for better detection
                    func_code = self._get_code_snippet(lines, node.lineno, min(node.lineno + 5, len(lines)))
                    
                    self.issues.append(CodeIssue(
                        file_path=file_path,
                        line_number=node.lineno,
                        issue_type="complex_function",
                        severity="warning",
                        category="quality",
                        message=f"Function has high cyclomatic complexity ({complexity})",
                        code_snippet=func_code,
                        suggestion="Consider breaking this function into smaller, more focused functions"
                    ))
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.ExceptHandler, ast.With, ast.For)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _check_missing_docstrings(self, tree: ast.AST, lines: List[str], file_path: str):
        """Check for missing docstrings in classes and functions."""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                if not node.body:
                    continue
                
                # Check if first statement is a docstring
                has_docstring = (node.body and 
                                isinstance(node.body[0], ast.Expr) and 
                                isinstance(node.body[0].value, (ast.Constant, ast.Str)))
                
                if not has_docstring:
                    # Check if it's a significant function/class
                    if isinstance(node, ast.FunctionDef):
                        if node.name.startswith('_') and len(node.args.args) > 0:
                            continue  # Skip private methods unless they're important
                    
                    node_code = self._get_code_snippet(lines, node.lineno, node.lineno + 3)
                    
                    self.issues.append(CodeIssue(
                        file_path=file_path,
                        line_number=node.lineno,
                        issue_type="missing_docstring",
                        severity="info",
                        category="style",
                        message="Missing docstring",
                        code_snippet=node_code,
                        suggestion="Add a docstring describing the purpose and parameters"
                    ))
    
    def _check_long_lines(self, lines: List[str], file_path: str):
        """Check for lines that are too long."""
        for i, line in enumerate(lines, start=1):
            if len(line) > 120:
                self.issues.append(CodeIssue(
                    file_path=file_path,
                    line_number=i,
                    issue_type="line_too_long",
                    severity="info",
                    category="style",
                    message=f"Line is too long ({len(line)} characters)",
                    code_snippet=line[:150] + "..." if len(line) > 150 else line,
                    suggestion="Break long lines into multiple lines for better readability"
                ))
    
    def _check_duplicate_code(self, tree: ast.AST, lines: List[str], file_path: str):
        """Check for duplicate code patterns."""
        # Simple duplicate detection based on function bodies
        function_signatures = {}
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Get function body hash
                body_lines = [lines[i] for i in range(node.lineno - 1, min(node.lineno + len(node.body), len(lines)))]
                body_hash = hash(''.join(body_lines))
                
                if body_hash in function_signatures:
                    # Potential duplicate
                    self.issues.append(CodeIssue(
                        file_path=file_path,
                        line_number=node.lineno,
                        issue_type="potential_duplicate_code",
                        severity="warning",
                        category="quality",
                        message="Potential code duplication detected",
                        code_snippet=self._get_code_snippet(lines, node.lineno, node.lineno + 3),
                        suggestion="Consider refactoring to eliminate duplication"
                    ))
                else:
                    function_signatures[body_hash] = node.lineno
    
    def _check_security_issues(self, tree: ast.AST, lines: List[str], file_path: str):
        """Check for common security vulnerabilities with better detection."""
        security_patterns = [
            # Dangerous functions
            (r'\beval\s*\(', 'dangerous_eval', 'Use of eval() is dangerous - can execute arbitrary code'),
            (r'\bexec\s*\(', 'dangerous_exec', 'Use of exec() is dangerous - can execute arbitrary code'),
            
            # Unsafe deserialization
            (r'pickle\.(loads?|load)', 'unsafe_pickle', 'Unsafe pickle loading can execute malicious code'),
            (r'yaml\.load\s*\(', 'unsafe_yaml', 'Unsafe YAML loading can execute arbitrary code'),
            
            # Hardcoded credentials - More comprehensive detection
            (r'(password|pwd|passwd)\s*[:=]\s*["\'][^"\']+["\']', 'hardcoded_password', 'Hardcoded password detected'),
            (r'(api_key|apikey|api[-_]?key)\s*[:=]\s*["\'][^"\']+["\']', 'hardcoded_api_key', 'Hardcoded API key detected'),
            (r'(secret|secret_key)\s*[:=]\s*["\'][^"\']+["\']', 'hardcoded_secret', 'Hardcoded secret detected'),
            (r'(token|access_token)\s*[:=]\s*["\'][^"\']+["\']', 'hardcoded_token', 'Hardcoded access token detected'),
            
            # SQL injection risks
            (r'query\s*[+=]\s*["\']\s*\$\{|\+.*request\.|%s', 'sql_injection_risk', 'Potential SQL injection vulnerability'),
            
            # Shell injection risks
            (r'os\.system\s*\(|subprocess\.call\s*\(|commands\.getoutput\s*\(', 'shell_injection_risk', 'Shell command execution - potential injection risk'),
        ]
        
        for i, line in enumerate(lines, start=1):
            for pattern, issue_type, message in security_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    # Get more context around the line
                    context = self._get_code_snippet(lines, i, i + 2)
                    
                    self.issues.append(CodeIssue(
                        file_path=file_path,
                        line_number=i,
                        issue_type=issue_type,
                        severity="error",
                        category="security",
                        message=message,
                        code_snippet=context,
                        suggestion=self._get_security_suggestion(issue_type)
                    ))
    
    def _check_style_issues(self, lines: List[str], file_path: str):
        """Check for common style issues."""
        for i, line in enumerate(lines, start=1):
            # Check for trailing whitespace
            if line and line[-1] == ' ':
                self.issues.append(CodeIssue(
                    file_path=file_path,
                    line_number=i,
                    issue_type="trailing_whitespace",
                    severity="info",
                    category="style",
                    message="Trailing whitespace detected",
                    code_snippet=line,
                    suggestion="Remove trailing whitespace"
                ))
            
            # Check for too many blank lines
            if i > 1 and not line.strip() and not lines[i-2].strip():
                self.issues.append(CodeIssue(
                    file_path=file_path,
                    line_number=i,
                    issue_type="extra_blank_line",
                    severity="info",
                    category="style",
                    message="Multiple blank lines",
                    code_snippet=line,
                    suggestion="Use single blank lines to separate sections"
                ))
    
    def _analyze_javascript(self, file_path: str, content: str):
        """Analyze JavaScript/TypeScript code for issues."""
        lines = content.split('\n')
        
        # Check for console.log statements
        for i, line in enumerate(lines, start=1):
            if 'console.log' in line or 'console.error' in line:
                self.issues.append(CodeIssue(
                    file_path=file_path,
                    line_number=i,
                    issue_type="console_log",
                    severity="warning",
                    category="quality",
                    message="Console statement left in code",
                    code_snippet=line,
                    suggestion="Remove console statements from production code"
                ))
        
        # Check for common JavaScript issues
        self._check_long_lines(lines, file_path)
        self._check_style_issues(lines, file_path)
    
    def _analyze_generic(self, file_path: str, content: str):
        """Generic analysis for files without specific parsers."""
        lines = content.split('\n')
        self._check_long_lines(lines, file_path)
        self._check_style_issues(lines, file_path)
    
    def _get_security_suggestion(self, issue_type: str) -> str:
        """Get security-specific suggestion based on issue type."""
        suggestions = {
            'dangerous_eval': 'Use safer alternatives like ast.literal_eval() or avoid dynamic code execution',
            'dangerous_exec': 'Avoid exec() - use importlib for dynamic imports or safer alternatives',
            'unsafe_pickle': 'Use pickle.loads only with trusted data, or use JSON for untrusted data',
            'unsafe_yaml': 'Use yaml.safe_load() instead of yaml.load()',
            'hardcoded_password': 'Move to environment variables (os.getenv()) or use a secrets manager',
            'hardcoded_api_key': 'Store API keys in environment variables or use a secrets manager like AWS Secrets Manager',
            'hardcoded_secret': 'Use environment variables or secrets management service (AWS Secrets Manager, Vault, etc.)',
            'hardcoded_token': 'Store tokens securely using environment variables or secure credential storage',
            'sql_injection_risk': 'Use parameterized queries or ORM methods instead of string concatenation',
            'shell_injection_risk': 'Avoid shell=True or use shlex.quote() to sanitize input before shell execution'
        }
        return suggestions.get(issue_type, 'Review and fix the security vulnerability')
    
    def _get_code_snippet(self, lines: List[str], start_line: int, end_line: int, context: int = 2) -> str:
        """Get code snippet with context."""
        start = max(0, start_line - context - 1)
        end = min(len(lines), end_line + context)
        
        snippet_lines = lines[start:end]
        snippet = '\n'.join(snippet_lines)
        
        return snippet[:200] + "..." if len(snippet) > 200 else snippet
    
    def categorize_issues(self, issues: List[CodeIssue]) -> Dict[str, List[CodeIssue]]:
        """Categorize issues by category."""
        categorized = {
            'quality': [],
            'security': [],
            'style': [],
            'originality': [],
            'team': []
        }
        
        for issue in issues:
            categorized[issue.category].append(issue)
        
        return categorized


def analyze_repository_files(file_metadata: List[Dict[str, Any]], repo_path: str) -> Dict[str, Any]:
    """
    Analyze all files in a repository for code issues.
    
    Args:
        file_metadata: List of file metadata from database
        repo_path: Path to stored repository files
    
    Returns:
        Dictionary with categorized issues
    """
    analyzer = CodeIssueAnalyzer()
    all_issues = []
    
    for file_info in file_metadata:
        file_path = file_info.get('path', '')
        file_extension = file_info.get('file_extension', '')
        
        # Construct full path
        full_path = os.path.join(repo_path, file_path)
        
        if os.path.exists(full_path):
            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                file_type = analyzer._detect_file_type(file_path)
                issues = analyzer.analyze_file(full_path, content, file_type)
                all_issues.extend(issues)
            
            except Exception as e:
                logger.warning(f"Could not analyze file {full_path}: {str(e)}")
    
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
