# File-Level Code Issues Display - Implementation Plan

## 🎯 **Overview**
Transform the hardcoded category scores (Quality, Security, Git, Style, Originality, Team) to show **actual code issues** with specific line numbers and file locations.

## 📋 **Current State Analysis**

### **Frontend (Currently Shows):**
- Generic score cards (0-100 for each category)
- Basic file list with scores
- Hardcoded recommendations

### **Backend (Currently Provides):**
- Overall metrics (languages, team data, commits)
- File metadata without specific issues
- Generic scoring from ChatGPT

## 🚀 **Implementation Plan**

### **Phase 1: Backend Enhancement** 🔧

#### **1.1 Add File Content Scanning**
```python
# New endpoint: Backend/api_routes/repo_analysis.py
@router.get("/repos/{repo_id}/issues")
async def get_code_issues(repo_id: str, category: str = None):
    """Get specific code issues for files with line numbers."""
    
    # Extract issues from stored files
    # Return format:
    {
        "quality_issues": [
            {
                "file": "src/main.py",
                "line": 42,
                "issue": "Missing type hints",
                "severity": "warning",
                "category": "quality"
            }
        ],
        "security_issues": [...],
        "style_issues": [...]
    }
```

#### **1.2 Implement Code Analysis**
- Use existing file storage to analyze code
- Parse AST (Abstract Syntax Tree) for code structure
- Use linting tools (pylint, eslint) for issues
- Integrate with ChatGPT for intelligent issue detection

#### **1.3 Issue Classification by Category**

**Quality Issues:**
- Missing type hints
- Complex functions (high cyclomatic complexity)
- Duplicate code
- Large files/functions
- Poor variable naming

**Security Issues:**
- SQL injection vulnerabilities
- XSS vulnerabilities
- Hardcoded secrets/passwords
- Insecure dependencies
- Missing input validation

**Style Issues:**
- Inconsistent formatting
- Missing docstrings
- Long lines
- Unused imports
- PEP/style guide violations

**Originality Issues:**
- Suspected AI-generated patterns
- Highly generic code
- Lack of custom implementations

**Team Balance Issues:**
- Files with single author
- Highly uneven contributions
- Merge conflicts patterns

### **Phase 2: Frontend Display Enhancement** 🎨

#### **2.1 Enhanced ScoreCard Component**
Update to show issue counts instead of just scores:

```tsx
// Show: "Quality: 85 (12 issues found)"
// Click to expand and see specific issues
```

#### **2.2 Create IssueDetailModal Component**
```tsx
<IssueDetailModal 
  category="Quality"
  issues={[
    {
      file: "src/main.py",
      line: 42,
      issue: "Missing type hints",
      severity: "warning",
      codeSnippet: "def calculate(x, y):  # Missing types"
    }
  ]}
/>
```

#### **2.3 File Tree with Issue Indicators**
```
📁 src/
  ├── 🐍 main.py (3 issues)
  │   └── Line 42: Missing type hints
  │   └── Line 67: Complex function
  │   └── Line 89: Duplicate code
  ├── 🐍 utils.py (5 issues)
  └── 📄 config.py (1 issue)
```

#### **2.4 Code Snippet Viewer**
- Show problematic code with syntax highlighting
- Highlight specific lines with issues
- Provide context around issues

### **Phase 3: Interactive Features** 🎮

#### **3.1 Click Score Cards → Show Issues**
- Click "Quality: 85" → Shows 12 quality issues
- Filter by severity (error, warning, info)
- Sort by file or line number

#### **3.2 Click File Name → Show File Details**
- Opens file with all issues highlighted
- Line-by-line breakdown
- Navigate between issues

#### **3.3 Issue Categorization**
```tsx
<Tabs>
  <Tabs.Trigger>Quality Issues</Tabs.Trigger>
  <Tabs.Trigger>Security Issues</Tabs.Trigger>
  <Tabs.Trigger>Style Issues</Tabs.Trigger>
</Tabs>
```

### **Phase 4: Backend Integration** 🔌

#### **4.1 Update ScoringResponse Interface**
```typescript
interface ScoringResponse {
  scores: [...],
  radar_data: [...],
  files: [
    {
      name: string,
      path: string,
      score: number,
      issues: [
        {
          line: number,
          issue: string,
          severity: 'error' | 'warning' | 'info',
          category: 'quality' | 'security' | 'style' | 'originality',
          codeSnippet: string,
          suggestion: string
        }
      ]
    }
  ],
  analysis: string,
  recommendations: string[]
}
```

#### **4.2 Backend Issue Analysis**
- Scan stored files for common patterns
- Use ChatGPT to identify issues in code snippets
- Map issues to categories

## 📊 **Data Structure**

### **Issue Object:**
```typescript
interface CodeIssue {
  id: string;
  file: string;
  path: string;
  line: number;
  column?: number;
  issue: string;
  severity: 'error' | 'warning' | 'info';
  category: 'quality' | 'security' | 'style' | 'originality' | 'team';
  codeSnippet: string;
  surroundingLines?: string[]; // Context
  suggestion?: string;
  relatedFiles?: string[];
}
```

### **Category Breakdown:**
```typescript
interface CategoryIssues {
  category: string;
  totalIssues: number;
  errors: number;
  warnings: number;
  info: number;
  issues: CodeIssue[];
}
```

## 🎨 **UI/UX Design**

### **Score Cards Enhancement:**
```
┌─────────────────────────────┐
│ Quality         85 / 100    │
│ 12 issues • 3 errors • 9 warnings
│ [View Issues] [↓]
└─────────────────────────────┘
```

### **Issue Modal:**
```
┌─────────────────────────────────────┐
│ Quality Issues (12)               │
├─────────────────────────────────────┤
│ 📁 src/main.py                     │
│   Line 42: Missing type hints       │
│     def calculate(x, y):            │
│   ⟶ def calculate(x: int, y: int):  │
│                                    │
│   Line 67: Complex function        │
│   (Cyclomatic complexity: 15)     │
└─────────────────────────────────────┘
```

## 🔄 **Implementation Steps**

### **Step 1: Backend - Add Issue Analysis** (Priority: High)
1. Create `code_issue_analyzer.py`
2. Add AST parsing for Python files
3. Integrate with stored files
4. Return structured issues

### **Step 2: Backend - Update API** (Priority: High)
1. Add `/repos/{repo_id}/issues` endpoint
2. Enhance scoring response with issues
3. Filter issues by category

### **Step 3: Frontend - Update Interfaces** (Priority: Medium)
1. Update `ScoringResponse` interface
2. Add `CodeIssue` interface
3. Update mock data with examples

### **Step 4: Frontend - Issue Display** (Priority: High)
1. Create `IssueDetailModal` component
2. Enhance `FileList` with clickable issues
3. Add file tree with indicators

### **Step 5: Frontend - Code Viewer** (Priority: Medium)
1. Add syntax highlighting
2. Create code snippet viewer
3. Add line navigation

### **Step 6: Testing** (Priority: High)
1. Test with real repositories
2. Verify issue detection accuracy
3. Test UI responsiveness

## 🎯 **Expected Outcome**

### **Before:**
- Generic score: "Quality: 85"
- No specific issues shown
- Recommendations are generic

### **After:**
- Score with count: "Quality: 85 (12 issues found)"
- Click to see:
  - Specific files with issues
  - Line numbers
  - Code snippets
  - Categorized issues (quality, security, style)
  - Suggestions for fixes

## 💡 **Key Benefits**

1. **Actionable**: Users see exactly what's wrong and where
2. **Educational**: Learn from specific examples
3. **Categorized**: Issues organized by type
4. **Contextual**: See surrounding code
5. **Prioritized**: Severity levels help focus

## 🚧 **Challenges & Solutions**

### **Challenge 1: Large Codebases**
- **Solution**: Pagination and lazy loading
- Show top issues first, load more on demand

### **Challenge 2: Issue Detection Accuracy**
- **Solution**: Combine multiple techniques
- AST + Linting + ChatGPT + Pattern matching

### **Challenge 3: Performance**
- **Solution**: Cache results
- Analyze once, store in database
- Update only when code changes

### **Challenge 4: Multiple Languages**
- **Solution**: Abstract parser interface
- Python: ast module
- JavaScript: acorn/eslint
- Generic: file-level analysis

## 📈 **Next Steps**

1. ✅ **Plan created** (this document)
2. 🔄 **Implement backend issue analysis**
3. 🔄 **Update API endpoints**
4. 🔄 **Create frontend components**
5. 🔄 **Test with real repositories**
6. 🔄 **Deploy and iterate**

---

## 🎯 **Summary**

Transform from "Quality: 85" to "Quality: 85 (12 issues found)" with:
- ✅ Specific files and line numbers
- ✅ Code snippets with syntax highlighting
- ✅ Categorized issues (quality, security, style, originality)
- ✅ Actionable suggestions
- ✅ Interactive file tree navigation

**This will make VibeCheck a powerful tool for real code review!** 🚀
