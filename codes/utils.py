import json
import re
import os
from datetime import datetime

def extract_frontend_planning(trajectories_json_file_path):
    """Extract planning context for frontend generation"""
    with open(trajectories_json_file_path) as f:
        traj = json.load(f)

    context_lst = []
    for turn in traj:
        if turn['role'] == 'assistant':
            content = turn['content']
            if "</think>" in content:
                content = content.split("</think>")[-1].strip()
            context_lst.append(content)

    context_lst = context_lst[:3] 
    return context_lst

def content_to_json(data):
    """Convert content string to JSON format"""
    clean_data = re.sub(r'\[CONTENT\]|\[/CONTENT\]', '', data).strip()
    clean_data = re.sub(r'(".*?"),\s*#.*', r'\1,', clean_data)
    
    try:
        return json.loads(clean_data)
    except json.JSONDecodeError:
        # Fallback parsing for malformed JSON
        return {"error": "Failed to parse JSON", "raw_content": clean_data}

def extract_react_code_from_content(content):
    """Extract React component code from LLM response"""
    code_blocks = []
    
    # Pattern for code blocks with language specification
    pattern = r'```(?:jsx?|typescript?|tsx?)\n(.*?)\n```'
    matches = re.findall(pattern, content, re.DOTALL)
    
    for match in matches:
        code_blocks.append(match.strip())
    
    # Also extract plain code blocks
    pattern = r'```\n(.*?)\n```'
    plain_matches = re.findall(pattern, content, re.DOTALL)
    
    for match in plain_matches:
        if match.strip() not in code_blocks:
            code_blocks.append(match.strip())
    
    return code_blocks

def parse_component_structure(content):
    """Parse component structure from planning output"""
    try:
        # Look for component hierarchy in the content
        lines = content.split('\n')
        components = []
        
        for line in lines:
            # Look for component mentions
            if 'component' in line.lower() or 'page' in line.lower():
                # Extract component name
                component_match = re.search(r'(\w+(?:Component|Page))', line)
                if component_match:
                    components.append(component_match.group(1))
        
        return components
    except Exception as e:
        print(f"Error parsing component structure: {e}")
        return []

def generate_package_json(project_name, requirements):
    """Generate package.json based on requirements"""
    base_dependencies = {
        "react": "^18.2.0",
        "react-dom": "^18.2.0",
        "react-scripts": "5.0.1",
        "typescript": "^4.9.5",
        "@types/react": "^18.2.0",
        "@types/react-dom": "^18.2.0"
    }
    
    dev_dependencies = {
        "@testing-library/jest-dom": "^5.16.4",
        "@testing-library/react": "^13.4.0",
        "@testing-library/user-event": "^13.5.0",
        "@types/jest": "^27.5.2",
        "@types/node": "^16.18.0"
    }
    
    # Add dependencies based on requirements
    if 'tailwind' in requirements.lower():
        base_dependencies.update({
            "tailwindcss": "^3.3.0",
            "autoprefixer": "^10.4.14",
            "postcss": "^8.4.24"
        })
    
    if 'material-ui' in requirements.lower() or 'mui' in requirements.lower():
        base_dependencies.update({
            "@mui/material": "^5.13.0",
            "@emotion/react": "^11.11.0",
            "@emotion/styled": "^11.11.0"
        })
    
    if 'redux' in requirements.lower():
        base_dependencies.update({
            "@reduxjs/toolkit": "^1.9.5",
            "react-redux": "^8.1.0"
        })
    
    if 'router' in requirements.lower():
        base_dependencies["react-router-dom"] = "^6.13.0"
    
    package_json = {
        "name": project_name.lower().replace(' ', '-'),
        "version": "0.1.0",
        "private": True,
        "dependencies": base_dependencies,
        "devDependencies": dev_dependencies,
        "scripts": {
            "start": "react-scripts start",
            "build": "react-scripts build",
            "test": "react-scripts test",
            "eject": "react-scripts eject"
        },
        "eslintConfig": {
            "extends": [
                "react-app",
                "react-app/jest"
            ]
        },
        "browserslist": {
            "production": [
                ">0.2%",
                "not dead",
                "not op_mini all"
            ],
            "development": [
                "last 1 chrome version",
                "last 1 firefox version",
                "last 1 safari version"
            ]
        }
    }
    
    return package_json

def print_response(response, output_path=None):
    """Print and optionally save LLM response"""
    print("=" * 50)
    print("LLM Response:")
    print("=" * 50)
    print(response)
    print("=" * 50)
    
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(response)

def print_log_cost(usage, model_name="unknown"):
    """Print token usage and estimated cost"""
    if usage:
        prompt_tokens = usage.get('prompt_tokens', 0)
        completion_tokens = usage.get('completion_tokens', 0)
        total_tokens = usage.get('total_tokens', 0)
        
        print(f"\n--- Token Usage for {model_name} ---")
        print(f"Prompt tokens: {prompt_tokens}")
        print(f"Completion tokens: {completion_tokens}")
        print(f"Total tokens: {total_tokens}")
        
        # Rough cost estimation (varies by model)
        if 'gpt-4' in model_name.lower():
            cost = (prompt_tokens * 0.03 + completion_tokens * 0.06) / 1000
        elif 'gpt-3.5' in model_name.lower():
            cost = (prompt_tokens * 0.001 + completion_tokens * 0.002) / 1000
        else:
            cost = total_tokens * 0.001 / 1000  # Default estimation
            
        print(f"Estimated cost: ${cost:.4f}")

def load_accumulated_cost(cost_file="accumulated_cost.json"):
    """Load accumulated cost from file"""
    if os.path.exists(cost_file):
        with open(cost_file, 'r') as f:
            return json.load(f)
    return {"total_cost": 0, "total_tokens": 0}

def save_accumulated_cost(cost_data, cost_file="accumulated_cost.json"):
    """Save accumulated cost to file"""
    with open(cost_file, 'w') as f:
        json.dump(cost_data, f, indent=2)

def create_folder_structure(base_path, project_name):
    """Create React project folder structure"""
    project_path = os.path.join(base_path, f"{project_name}_frontend")
    
    folders = [
        "src/components",
        "src/pages",
        "src/hooks",
        "src/utils",
        "src/types",
        "src/styles",
        "src/assets",
        "public"
    ]
    
    for folder in folders:
        os.makedirs(os.path.join(project_path, folder), exist_ok=True)
    
    return project_path
