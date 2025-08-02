from openai import OpenAI
import json
import os
from tqdm import tqdm
import sys
from utils import extract_frontend_planning, content_to_json, print_response, print_log_cost, load_accumulated_cost, save_accumulated_cost
import copy
import argparse

parser = argparse.ArgumentParser()

parser.add_argument('--project_name', type=str, required=True)
parser.add_argument('--gpt_version', type=str, default="o3-mini")
parser.add_argument('--requirements_format', type=str, default="markdown", choices=["markdown", "json", "text"])
parser.add_argument('--requirements_path', type=str, required=True)
parser.add_argument('--output_dir', type=str, default="")

args = parser.parse_args()

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

project_name = args.project_name
gpt_version = args.gpt_version
requirements_format = args.requirements_format
requirements_path = args.requirements_path
output_dir = args.output_dir

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

# Extract planning context
context_lst = extract_frontend_planning(f'{output_dir}/planning_trajectories.json')

# Load planning config if exists
planning_config = ""
if os.path.exists(f'{output_dir}/planning_config.yaml'):
    with open(f'{output_dir}/planning_config.yaml') as f:
        planning_config = f.read()

analysis_msg = [
    {'role': "system", "content": f"""You are an expert frontend architect, UX/UI designer, and React developer with deep understanding of component design patterns, state management, and modern web development practices.

You will receive project requirements in {requirements_format} format along with the planning output from the previous stage.
Your task is to create detailed technical analysis and component specifications for the React frontend application.

This analysis should include:

1. **Component Breakdown**: Detailed specification of each React component with:
   - Props interface (TypeScript)
   - State requirements
   - Event handlers
   - Styling approach
   - Accessibility considerations

2. **State Management Design**: 
   - Global state structure
   - Local component state
   - Data flow patterns
   - API integration points

3. **Routing Architecture**:
   - Route definitions
   - Protected routes
   - Navigation structure
   - URL parameters

4. **UI/UX Specifications**:
   - Layout system
   - Responsive breakpoints
   - Color scheme and theming
   - Typography scale
   - Animation and transitions

5. **Data Models**:
   - TypeScript interfaces
   - API response types
   - Form validation schemas

6. **Integration Requirements**:
   - External APIs
   - Authentication flow
   - Error handling
   - Loading states

Format your response as detailed technical specifications that can be directly implemented by developers."""},
    
    {'role': "user", "content": f"""Project Name: {project_name}

Original Requirements:
{requirements_content}

Planning Output:
{context_lst[0] if context_lst else "No planning context available"}

Please provide detailed technical analysis and component specifications for this React frontend application."""}
]

# Initialize cost tracking
cost_data = load_accumulated_cost(os.path.join(output_dir, "accumulated_cost.json"))

print(f"🔍 Analyzing technical specifications for: {project_name}")
print("=" * 60)

try:
    response = client.chat.completions.create(
        model=gpt_version,
        messages=analysis_msg,
        temperature=0.3,
        max_tokens=6000
    )
    
    analysis_response = response.choices[0].message.content
    
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
        save_accumulated_cost(cost_data, os.path.join(output_dir, "accumulated_cost.json"))
    
    # Print and save response
    print_response(analysis_response, os.path.join(output_dir, "analysis_response.md"))
    
    # Update trajectories for next stage
    if os.path.exists(f'{output_dir}/planning_trajectories.json'):
        with open(f'{output_dir}/planning_trajectories.json', 'r') as f:
            trajectories = json.load(f)
    else:
        trajectories = []
    
    trajectories.extend([
        {'role': 'user', 'content': analysis_msg[1]['content']},
        {'role': 'assistant', 'content': analysis_response}
    ])
    
    with open(os.path.join(output_dir, "analysis_trajectories.json"), 'w') as f:
        json.dump(trajectories, f, indent=2)
    
    print(f"\n✅ Technical analysis completed successfully!")
    print(f"📁 Output saved to: {output_dir}")
    print(f"💰 Total accumulated cost: ${cost_data['total_cost']:.4f}")
    
except Exception as e:
    print(f"❌ Error during analysis: {str(e)}")
    sys.exit(1)
