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
parser.add_argument('--temperature', type=float, default=0.3)
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

# Extract planning context
context_lst = extract_frontend_planning(f'{output_dir}/planning_trajectories.json')

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
        max_tokens=6000,
        top_p=0.95
    )
    
    print(f"🔍 Analyzing technical specifications for: {project_name}")
    print("=" * 60)
    
    # Format prompt for the model
    prompt = f"""<|im_start|>system
{analysis_msg[0]['content']}<|im_end|>
<|im_start|>user
{analysis_msg[1]['content']}<|im_end|>
<|im_start|>assistant
"""

    # Generate response
    outputs = llm.generate([prompt], sampling_params)
    analysis_response = outputs[0].outputs[0].text
    
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
    
except Exception as e:
    print(f"❌ Error during analysis: {str(e)}")
    sys.exit(1)
