from openai import OpenAI
import json
import os
from tqdm import tqdm
import re
import sys
import copy
from utils import (
    extract_frontend_planning, 
    content_to_json, 
    extract_react_code_from_content, 
    print_response, 
    print_log_cost, 
    load_accumulated_cost, 
    save_accumulated_cost,
    generate_package_json,
    create_folder_structure
)
import argparse

parser = argparse.ArgumentParser()

parser.add_argument('--project_name', type=str, required=True)
parser.add_argument('--gpt_version', type=str, default="o3-mini")
parser.add_argument('--requirements_format', type=str, default="markdown", choices=["markdown", "json", "text"])
parser.add_argument('--requirements_path', type=str, required=True)
parser.add_argument('--output_dir', type=str, default="")
parser.add_argument('--output_repo_dir', type=str, default="")

args = parser.parse_args()
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

project_name = args.project_name
gpt_version = args.gpt_version
requirements_format = args.requirements_format
requirements_path = args.requirements_path
output_dir = args.output_dir
output_repo_dir = args.output_repo_dir

# Load requirements content
if requirements_format == "markdown":
    with open(f'{requirements_path}') as f:
        requirements_content = f.read()
elif requirements_format == "json":
    with open(f'{requirements_path}') as f:
        requirements_content = json.load(f)
elif requirements_format == "text":
    with open(f'{requirements_path}') as f:
        requirements_content = f.read()
else:
    print(f"[ERROR] Invalid requirements format. Please select 'markdown', 'json', or 'text'.")
    sys.exit(0)

# Extract context from previous stages
context_lst = extract_frontend_planning(f'{output_dir}/analysis_trajectories.json')

# Create project folder structure
project_path = create_folder_structure(output_repo_dir, project_name)

# Define components to generate based on analysis
components_to_generate = [
    {
        "name": "App",
        "type": "main",
        "path": "src/App.tsx",
        "description": "Main application component with routing"
    },
    {
        "name": "Layout",
        "type": "layout",
        "path": "src/components/Layout.tsx",
        "description": "Main layout component with header, sidebar, footer"
    },
    {
        "name": "Header",
        "type": "component",
        "path": "src/components/Header.tsx",
        "description": "Application header with navigation"
    },
    {
        "name": "Sidebar",
        "type": "component", 
        "path": "src/components/Sidebar.tsx",
        "description": "Navigation sidebar component"
    },
    {
        "name": "Dashboard",
        "type": "page",
        "path": "src/pages/Dashboard.tsx",
        "description": "Main dashboard page"
    }
]

# Initialize cost tracking
cost_data = load_accumulated_cost(os.path.join(output_dir, "accumulated_cost.json"))

print(f"⚛️ Generating React components for: {project_name}")
print("=" * 60)

generated_files = {}

# Generate each component
for component in tqdm(components_to_generate, desc="Generating components"):
    
    coding_msg = [
        {'role': "system", "content": f"""You are an expert React developer and TypeScript specialist with deep knowledge of modern frontend development practices, component architecture, and code quality.

You will receive project requirements and technical analysis to generate high-quality React components.

Your task is to generate production-ready React component code that:

1. **Modern React Patterns**:
   - Functional components with hooks
   - TypeScript with proper type definitions
   - Clean, readable, and maintainable code

2. **Code Quality**:
   - Proper error handling
   - Loading states
   - Accessibility (ARIA labels, semantic HTML)
   - Performance optimizations (useMemo, useCallback when needed)

3. **Styling**:
   - Use CSS modules or styled-components
   - Responsive design
   - Modern CSS practices

4. **Component Structure**:
   - Clear props interface
   - Proper component composition
   - Reusable and testable

5. **Best Practices**:
   - ESLint and Prettier compliant
   - Consistent naming conventions
   - Clear comments for complex logic

Generate ONLY the component code for {component['name']} ({component['type']}).
Include all necessary imports, types, and styling.
Make sure the code is complete and ready to use.

Format your response with the complete component code wrapped in ```tsx code blocks."""},
        
        {'role': "user", "content": f"""Project Name: {project_name}

Component to Generate: {component['name']} ({component['type']})
Description: {component['description']}
File Path: {component['path']}

Original Requirements:
{requirements_content}

Technical Analysis:
{context_lst[0] if context_lst else "No analysis context available"}

Generate the complete React component code for {component['name']}."""}
    ]
    
    try:
        response = client.chat.completions.create(
            model=gpt_version,
            messages=coding_msg,
            temperature=0.2,
            max_tokens=3000
        )
        
        coding_response = response.choices[0].message.content
        
        # Log usage and cost
        if hasattr(response, 'usage'):
            print_log_cost(response.usage._asdict(), gpt_version)
            
            # Update accumulated cost
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens
            
            if 'gpt-4' in gpt_version.lower():
                cost = (prompt_tokens * 0.03 + completion_tokens * 0.06) / 1000
            elif 'gpt-3.5' in gpt_version.lower():
                cost = (prompt_tokens * 0.001 + completion_tokens * 0.002) / 1000
            else:
                cost = total_tokens * 0.001 / 1000
            
            cost_data["total_cost"] += cost
            cost_data["total_tokens"] += total_tokens
        
        # Extract and save component code
        code_blocks = extract_react_code_from_content(coding_response)
        
        if code_blocks:
            component_code = code_blocks[0]  # Take the first/main code block
            
            # Save component file
            full_file_path = os.path.join(project_path, component['path'])
            os.makedirs(os.path.dirname(full_file_path), exist_ok=True)
            
            with open(full_file_path, 'w', encoding='utf-8') as f:
                f.write(component_code)
            
            generated_files[component['name']] = {
                'path': component['path'],
                'code': component_code,
                'full_response': coding_response
            }
            
            print(f"✅ Generated {component['name']} component")
        
        # Save full response for debugging
        response_file = os.path.join(output_dir, f"coding_{component['name'].lower()}_response.md")
        print_response(coding_response, response_file)
        
    except Exception as e:
        print(f"❌ Error generating {component['name']}: {str(e)}")
        continue

# Generate package.json
package_json = generate_package_json(project_name, str(requirements_content))
package_json_path = os.path.join(project_path, "package.json")
with open(package_json_path, 'w', encoding='utf-8') as f:
    json.dump(package_json, f, indent=2)

print(f"✅ Generated package.json")

# Generate basic files
basic_files = {
    "public/index.html": '''<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <link rel="icon" href="%PUBLIC_URL%/favicon.ico" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#000000" />
    <meta name="description" content="Generated React application" />
    <title>''' + project_name + '''</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>''',
    
    "src/index.tsx": '''import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);''',
    
    "src/index.css": '''body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

code {
  font-family: source-code-pro, Menlo, Monaco, Consolas, 'Courier New',
    monospace;
}

* {
  box-sizing: border-box;
}''',

    "README.md": f'''# {project_name}

This React application was generated automatically from project requirements.

## Getting Started

### Prerequisites
- Node.js (version 14 or higher)
- npm or yarn

### Installation

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm start
```

3. Open [http://localhost:3000](http://localhost:3000) to view it in the browser.

## Available Scripts

- `npm start` - Runs the app in development mode
- `npm test` - Launches the test runner
- `npm run build` - Builds the app for production
- `npm run eject` - Ejects from Create React App (one-way operation)

## Project Structure

```
src/
├── components/     # Reusable UI components
├── pages/         # Page components
├── hooks/         # Custom React hooks
├── utils/         # Utility functions
├── types/         # TypeScript type definitions
└── styles/        # CSS and styling files
```

## Technologies Used

- React 18+
- TypeScript
- CSS Modules / Styled Components
- React Router (if routing is implemented)

## Generated Components

{chr(10).join([f"- {name}: {info['path']}" for name, info in generated_files.items()])}
'''
}

# Create basic files
for file_path, content in basic_files.items():
    full_path = os.path.join(project_path, file_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(content)

# Save generation summary
summary = {
    "project_name": project_name,
    "generated_components": len(generated_files),
    "components": list(generated_files.keys()),
    "project_path": project_path,
    "total_cost": cost_data["total_cost"],
    "total_tokens": cost_data["total_tokens"]
}

with open(os.path.join(output_dir, "generation_summary.json"), 'w') as f:
    json.dump(summary, f, indent=2)

# Update accumulated cost
save_accumulated_cost(cost_data, os.path.join(output_dir, "accumulated_cost.json"))

print(f"\n🎉 React application generation completed!")
print(f"📁 Project created at: {project_path}")
print(f"⚛️ Generated {len(generated_files)} components")
print(f"💰 Total cost: ${cost_data['total_cost']:.4f}")
print(f"\n🚀 To run the application:")
print(f"   cd {project_path}")
print(f"   npm install")
print(f"   npm start")
