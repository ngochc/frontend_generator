from openai import OpenAI
import json
from tqdm import tqdm
import argparse
import os
import sys
from utils import print_response, print_log_cost, load_accumulated_cost, save_accumulated_cost

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

plan_msg = [
    {'role': "system", "content": f"""You are an expert frontend architect and React developer with deep understanding of modern web development practices and user experience design.

You will receive project requirements in {requirements_format} format.
Your task is to create a detailed and efficient plan to build a React frontend application that meets all the specified requirements.

This plan should include:
1. Component architecture and hierarchy
2. State management strategy
3. Routing structure
4. UI/UX considerations
5. Technology stack selection
6. Development approach

Instructions:

1. Align with Requirements: Your plan must strictly follow the features, user stories, and technical specifications described in the requirements.
2. React Best Practices: Use modern React patterns, hooks, and functional components.
3. Component Design: Plan for reusable, maintainable, and testable components.
4. State Management: Choose appropriate state management (useState, useContext, Redux, Zustand) based on complexity.
5. Responsive Design: Ensure mobile-first responsive design approach.
6. Accessibility: Consider WCAG guidelines and semantic HTML.
7. Performance: Plan for code splitting, lazy loading, and optimization.
8. Testing Strategy: Include unit tests and integration tests planning.

Format your response as a detailed implementation plan with clear sections and actionable steps."""},
    
    {'role': "user", "content": f"""Project Name: {project_name}

Requirements:
{requirements_content}

Please create a comprehensive frontend development plan for this React application."""}
]

# Initialize cost tracking
cost_data = load_accumulated_cost(os.path.join(output_dir, "accumulated_cost.json"))

print(f"🎯 Planning frontend architecture for: {project_name}")
print("=" * 60)

try:
    response = client.chat.completions.create(
        model=gpt_version,
        messages=plan_msg,
        temperature=0.7,
        max_tokens=4000
    )
    
    plan_response = response.choices[0].message.content
    
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
    print_response(plan_response, os.path.join(output_dir, "planning_response.md"))
    
    # Save trajectories for next stage
    trajectories = [
        {'role': 'user', 'content': plan_msg[1]['content']},
        {'role': 'assistant', 'content': plan_response}
    ]
    
    with open(os.path.join(output_dir, "planning_trajectories.json"), 'w') as f:
        json.dump(trajectories, f, indent=2)
    
    print(f"\n✅ Planning completed successfully!")
    print(f"📁 Output saved to: {output_dir}")
    print(f"💰 Total accumulated cost: ${cost_data['total_cost']:.4f}")
    
except Exception as e:
    print(f"❌ Error during planning: {str(e)}")
    sys.exit(1)
