from openai import OpenAI
import os
import argparse
import sys
from pathlib import Path
import json

parser = argparse.ArgumentParser()
parser.add_argument('--project_path', type=str, required=True)
parser.add_argument('--gpt_version', type=str, default="gpt-4")
parser.add_argument('--review_focus', type=str, default="performance,accessibility,security")
parser.add_argument('--output_format', type=str, default="markdown", choices=["markdown", "json"])
parser.add_argument('--output_file', type=str, default="")

args = parser.parse_args()

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

project_path = args.project_path
gpt_version = args.gpt_version
review_focus = args.review_focus
output_format = args.output_format
output_file = args.output_file

def analyze_code_files(project_path):
    """Analyze React code files in the project."""
    project_dir = Path(project_path)
    code_files = {}
    
    # Collect TypeScript/JavaScript files
    for file_path in project_dir.rglob("src/**/*.{ts,tsx,js,jsx}"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                relative_path = str(file_path.relative_to(project_dir))
                code_files[relative_path] = content
        except Exception as e:
            print(f"⚠️ Could not read {file_path}: {str(e)}")
    
    return code_files

def generate_review_prompt(code_files, review_focus):
    """Generate comprehensive code review prompt."""
    
    focus_areas = [area.strip() for area in review_focus.split(',')]
    
    system_prompt = """You are an expert React code reviewer with deep knowledge of modern JavaScript/TypeScript, React best practices, performance optimization, accessibility standards, and security considerations.

Provide a comprehensive code review focusing on the specified areas. For each issue found, provide:
1. Severity level (Critical, High, Medium, Low)
2. Clear description of the issue
3. Specific line references where applicable
4. Actionable recommendations for improvement
5. Code examples showing the fix

Focus areas for this review:
"""
    
    for area in focus_areas:
        if area == 'performance':
            system_prompt += "\n- **Performance**: Bundle size, rendering efficiency, memory usage, lazy loading"
        elif area == 'accessibility':
            system_prompt += "\n- **Accessibility**: WCAG compliance, ARIA labels, keyboard navigation, screen readers"
        elif area == 'security':
            system_prompt += "\n- **Security**: XSS prevention, data validation, secure API calls, dependency vulnerabilities"
        elif area == 'maintainability':
            system_prompt += "\n- **Maintainability**: Code organization, naming conventions, documentation, reusability"
        elif area == 'testing':
            system_prompt += "\n- **Testing**: Test coverage, testability, mocking strategies, edge cases"
    
    # Create file content summary
    files_summary = "\n\n## Code Files to Review:\n"
    for file_path, content in code_files.items():
        lines_count = len(content.split('\n'))
        files_summary += f"\n### {file_path} ({lines_count} lines)\n```typescript\n{content[:1000]}{'...' if len(content) > 1000 else ''}\n```\n"
    
    user_prompt = f"""Please conduct a comprehensive code review of this React application.

{files_summary}

Provide detailed feedback organized by:
1. Critical Issues (must fix)
2. Performance Improvements
3. Accessibility Enhancements
4. Security Considerations
5. Best Practices & Maintainability
6. Overall Recommendations

For each finding, include:
- Severity level
- File location
- Issue description
- Recommended solution
- Code example (if applicable)
"""
    
    return system_prompt, user_prompt

def conduct_code_review(code_files):
    """Conduct code review using OpenAI."""
    
    system_prompt, user_prompt = generate_review_prompt(code_files, review_focus)
    
    try:
        response = client.chat.completions.create(
            model=gpt_version,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ],
            temperature=0.1,
            max_tokens=6000
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"❌ Code review failed: {str(e)}")
        return None

def format_review_output(review_content):
    """Format the review output."""
    
    if output_format == "json":
        # Convert markdown-style review to JSON structure
        review_json = {
            "timestamp": "2024-01-01T00:00:00Z",
            "summary": "Code review completed",
            "findings": [],
            "recommendations": [],
            "raw_content": review_content
        }
        return json.dumps(review_json, indent=2)
    
    else:  # markdown
        header = f"""# 🔍 AI Code Review Report

**Generated:** {Path.cwd()}
**Review Focus:** Performance, Accessibility, Security, Best Practices

---

"""
        return header + review_content

# Validate project path
if not os.path.exists(project_path):
    print(f"❌ Error: Project path not found: {project_path}")
    sys.exit(1)

print(f"🔍 AI Code Review")
print(f"=====================================")
print(f"📁 Project: {project_path}")
print(f"🤖 Model: {gpt_version}")
print(f"🎯 Focus: {review_focus}")
print(f"📄 Format: {output_format}")
print(f"=====================================\n")

# Analyze code files
print("📊 Analyzing code files...")
code_files = analyze_code_files(project_path)
print(f"Found {len(code_files)} code files")

if not code_files:
    print("❌ No code files found to review")
    sys.exit(1)

# Conduct review
print("🚀 Conducting AI code review...")
review_content = conduct_code_review(code_files)

if not review_content:
    print("❌ Code review failed")
    sys.exit(1)

# Format output
formatted_review = format_review_output(review_content)

# Save or display results
if output_file:
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(formatted_review)
        print(f"✅ Review saved to: {output_file}")
    except Exception as e:
        print(f"❌ Failed to save review: {str(e)}")
else:
    print("\n" + "="*50)
    print("📋 CODE REVIEW RESULTS")
    print("="*50)
    print(formatted_review)

print(f"\n🎉 Code Review Completed!")
