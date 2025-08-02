import json
import argparse
import os
import sys
from utils import print_response, extract_frontend_planning
from transformers import AutoTokenizer
from vllm import LLM, SamplingParams

parser = argparse.ArgumentParser()

parser.add_argument('--project_name', type=str, required=True)
parser.add_argument('--model_name', type=str, default="deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct")
parser.add_argument('--tp_size', type=int, default=2)
parser.add_argument('--temperature', type=float, default=0.7)
parser.add_argument('--max_model_len', type=int, default=128000)
parser.add_argument('--requirements_format', type=str, default="markdown", choices=["markdown", "json", "text"])
parser.add_argument('--requirements_path', type=str, required=True)
parser.add_argument('--output_dir', type=str, default="")

args = parser.parse_args()

project_name = args.project_name
requirements_format = args.requirements_format
requirements_path = args.requirements_path
output_dir = args.output_dir

model_name = args.model_name
tp_size = args.tp_size
max_model_len = args.max_model_len
temperature = args.temperature

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

print(f"🤖 Loading model: {model_name}")

# Initialize vLLM
try:
    llm = LLM(
        model=model_name,
        tensor_parallel_size=tp_size,
        max_model_len=max_model_len,
        trust_remote_code=True
    )
    
    # Set up sampling parameters
    sampling_params = SamplingParams(
        temperature=temperature,
        max_tokens=4000,
        top_p=0.95
    )
    
    print(f"🎯 Planning frontend architecture for: {project_name}")
    print("=" * 60)
    
    # Format prompt for the model
    prompt = f"""<|im_start|>system
{plan_msg[0]['content']}<|im_end|>
<|im_start|>user
{plan_msg[1]['content']}<|im_end|>
<|im_start|>assistant
"""

    # Generate response
    outputs = llm.generate([prompt], sampling_params)
    plan_response = outputs[0].outputs[0].text
    
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
    
except Exception as e:
    print(f"❌ Error during planning: {str(e)}")
    sys.exit(1)
