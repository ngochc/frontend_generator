from openai import OpenAI
import json
import os
import argparse
import sys
from pathlib import Path
from utils import print_response, print_log_cost, load_accumulated_cost, save_accumulated_cost

parser = argparse.ArgumentParser()
parser.add_argument('--project_name', type=str, required=True)
parser.add_argument('--gpt_version', type=str, default="gpt-4")
parser.add_argument('--project_path', type=str, required=True)
parser.add_argument('--requirements_path', type=str, required=True)
parser.add_argument('--test_types', type=str, default="unit,integration")
parser.add_argument('--test_framework', type=str, default="jest", choices=["jest", "vitest"])
parser.add_argument('--coverage_threshold', type=int, default=80)
parser.add_argument('--include_accessibility', type=bool, default=True)
parser.add_argument('--output_dir', type=str, default="")

args = parser.parse_args()

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

project_name = args.project_name
gpt_version = args.gpt_version
project_path = args.project_path
requirements_path = args.requirements_path
test_types = args.test_types
test_framework = args.test_framework
coverage_threshold = args.coverage_threshold
include_accessibility = args.include_accessibility
output_dir = args.output_dir

def load_project_structure(project_path):
    """Analyze the generated React project structure."""
    components = []
    pages = []
    utils = []
    
    project_dir = Path(project_path)
    
    # Find React components
    if (project_dir / "src" / "components").exists():
        for component_file in (project_dir / "src" / "components").rglob("*.tsx"):
            components.append(str(component_file.relative_to(project_dir)))
    
    # Find pages
    if (project_dir / "src" / "pages").exists():
        for page_file in (project_dir / "src" / "pages").rglob("*.tsx"):
            pages.append(str(page_file.relative_to(project_dir)))
    
    # Find utilities
    if (project_dir / "src" / "utils").exists():
        for util_file in (project_dir / "src" / "utils").rglob("*.ts"):
            utils.append(str(util_file.relative_to(project_dir)))
    
    return {
        "components": components,
        "pages": pages,
        "utils": utils,
        "src_structure": list(project_dir.rglob("src/**/*.{ts,tsx}"))
    }

def generate_test_prompts(requirements_content, project_structure):
    """Generate prompts for different test types."""
    
    test_type_list = [t.strip() for t in test_types.split(',')]
    prompts = {}
    
    # Base system prompt for test generation
    base_system_prompt = f"""You are an expert React testing engineer specializing in comprehensive test suite generation using {test_framework}, React Testing Library, and modern testing practices.

You will generate high-quality, production-ready tests for a React application based on:
1. Original project requirements
2. Generated component structure
3. Specific test type requirements

Your tests should follow these principles:
- Use modern testing patterns and best practices
- Include proper setup and teardown
- Test both happy paths and edge cases
- Include accessibility testing where applicable
- Provide clear, descriptive test names
- Include proper mocking for external dependencies
- Achieve high code coverage while maintaining meaningful tests

Testing Framework: {test_framework}
Coverage Threshold: {coverage_threshold}%
Accessibility Testing: {'Enabled' if include_accessibility else 'Disabled'}
"""

    # Unit Tests
    if 'unit' in test_type_list:
        prompts['unit'] = {
            'role': "system", 
            'content': base_system_prompt
        }
    
    # Integration Tests
    if 'integration' in test_type_list:
        prompts['integration'] = {
            'role': "system",
            'content': base_system_prompt
        }
    
    # E2E Tests
    if 'e2e' in test_type_list:
        prompts['e2e'] = {
            'role': "system",
            'content': base_system_prompt + "\n\nSpecialize in end-to-end testing using Playwright or Cypress for complete user journey validation."
        }
    
    # Accessibility Tests
    if 'accessibility' in test_type_list or include_accessibility:
        prompts['accessibility'] = {
            'role': "system",
            'content': base_system_prompt + "\n\nSpecialize in accessibility testing using jest-axe and manual accessibility validation."
        }
    
    return prompts

def generate_tests_with_openai(prompts, requirements_content, project_structure):
    """Generate tests using OpenAI API."""
    generated_tests = {}
    total_cost = 0.0
    
    for test_type, system_prompt in prompts.items():
        print(f"\n🧪 Generating {test_type} tests...")
        
        user_content = f"""Project: {project_name}

Original Requirements:
{requirements_content}

Project Structure:
Components: {project_structure['components']}
Pages: {project_structure['pages']}
Utils: {project_structure['utils']}

Generate comprehensive {test_type} tests with proper imports and setup. Use {test_framework} and React Testing Library."""
        
        try:
            response = client.chat.completions.create(
                model=gpt_version,
                messages=[
                    system_prompt,
                    {'role': 'user', 'content': user_content}
                ],
                temperature=0.2,
                max_tokens=6000
            )
            
            generated_tests[test_type] = response.choices[0].message.content
            
            # Calculate cost (approximate)
            input_tokens = len(system_prompt['content'] + user_content) // 4
            output_tokens = len(response.choices[0].message.content) // 4
            cost = (input_tokens * 0.00001) + (output_tokens * 0.00003)
            total_cost += cost
            
            print(f"✅ {test_type.capitalize()} tests generated successfully")
            
        except Exception as e:
            print(f"❌ Failed to generate {test_type} tests: {str(e)}")
            generated_tests[test_type] = None
    
    return generated_tests, total_cost

def save_test_files(generated_tests, project_path):
    """Save generated test files to the project."""
    project_dir = Path(project_path)
    test_dir = project_dir / "src" / "__tests__"
    
    # Create test directories
    test_dir.mkdir(exist_ok=True)
    (test_dir / "unit").mkdir(exist_ok=True)
    (test_dir / "integration").mkdir(exist_ok=True)
    (test_dir / "e2e").mkdir(exist_ok=True)
    (test_dir / "accessibility").mkdir(exist_ok=True)
    
    saved_files = []
    
    for test_type, content in generated_tests.items():
        if content is None:
            continue
            
        # Extract test files from the generated content
        test_files = extract_test_files_from_content(content, test_type)
        
        for filename, file_content in test_files.items():
            file_path = test_dir / test_type / filename
            
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(file_content)
                saved_files.append(str(file_path.relative_to(project_dir)))
                print(f"📝 Saved: {file_path.relative_to(project_dir)}")
            except Exception as e:
                print(f"❌ Failed to save {filename}: {str(e)}")
    
    return saved_files

def extract_test_files_from_content(content, test_type):
    """Extract individual test files from generated content."""
    import re
    
    # Pattern to match code blocks with filenames
    pattern = r'```(?:typescript|javascript|tsx?)\s*(?://\s*(.+\.(?:test|spec)\.(ts|tsx|js|jsx))\s*)?\n(.*?)\n```'
    matches = re.findall(pattern, content, re.DOTALL)
    
    test_files = {}
    
    for i, match in enumerate(matches):
        filename = match[0] if match[0] else f"{test_type}_test_{i+1}.test.tsx"
        file_content = match[2].strip()
        
        # Ensure proper file extension
        if not filename.endswith(('.test.ts', '.test.tsx', '.spec.ts', '.spec.tsx')):
            filename = f"{filename.replace('.ts', '').replace('.tsx', '')}.test.tsx"
        
        test_files[filename] = file_content
    
    # If no specific files found, create a general test file
    if not test_files:
        test_files[f"{test_type}_tests.test.tsx"] = content
    
    return test_files

def generate_test_config_files(project_path):
    """Generate test configuration files."""
    project_dir = Path(project_path)
    
    # Jest configuration
    jest_config = {
        "preset": "ts-jest",
        "testEnvironment": "jsdom",
        "setupFilesAfterEnv": ["<rootDir>/src/setupTests.ts"],
        "moduleNameMapping": {
            "^@/(.*)$": "<rootDir>/src/$1"
        },
        "collectCoverageFrom": [
            "src/**/*.{ts,tsx}",
            "!src/**/*.d.ts",
            "!src/index.tsx",
            "!src/reportWebVitals.ts"
        ],
        "coverageThreshold": {
            "global": {
                "branches": coverage_threshold,
                "functions": coverage_threshold,
                "lines": coverage_threshold,
                "statements": coverage_threshold
            }
        }
    }
    
    # Setup file for tests
    setup_content = '''import '@testing-library/jest-dom';
import 'jest-axe/extend-expect';

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  observe() { return null; }
  disconnect() { return null; }
  unobserve() { return null; }
};
'''
    
    try:
        # Save Jest config
        with open(project_dir / "jest.config.js", 'w') as f:
            f.write(f"module.exports = {json.dumps(jest_config, indent=2)};")
        
        # Save setup file
        with open(project_dir / "src" / "setupTests.ts", 'w') as f:
            f.write(setup_content)
        
        print("📋 Test configuration files generated")
        
    except Exception as e:
        print(f"❌ Failed to generate config files: {str(e)}")

# Load requirements content
if not os.path.exists(project_path):
    print(f"❌ Error: Project path not found: {project_path}")
    sys.exit(1)

try:
    with open(requirements_path, 'r', encoding='utf-8') as f:
        requirements_content = f.read()
except Exception as e:
    print(f"❌ Error loading requirements: {str(e)}")
    sys.exit(1)

print(f"🧪 Test Generator - OpenAI Version")
print(f"=====================================")
print(f"📁 Project: {project_name}")
print(f"🤖 Model: {gpt_version}")
print(f"📍 Project Path: {project_path}")
print(f"🧾 Test Types: {test_types}")
print(f"🎯 Coverage Target: {coverage_threshold}%")
print(f"=====================================\n")

# Analyze project structure
print("📊 Analyzing project structure...")
project_structure = load_project_structure(project_path)
print(f"Found {len(project_structure['components'])} components, {len(project_structure['pages'])} pages")

# Generate test prompts
print("🎨 Preparing test generation prompts...")
prompts = generate_test_prompts(requirements_content, project_structure)

# Generate tests
print("🚀 Generating test suites...")
generated_tests, total_cost = generate_tests_with_openai(prompts, requirements_content, project_structure)

# Save test files
print("\n💾 Saving test files...")
saved_files = save_test_files(generated_tests, project_path)

# Generate configuration files
print("\n⚙️ Generating test configuration...")
generate_test_config_files(project_path)

# Summary
print(f"\n🎉 Test Generation Completed!")
print(f"=====================================")
print(f"📁 Test files generated: {len(saved_files)}")
print(f"💰 Estimated cost: ${total_cost:.4f}")
print(f"📋 Configuration files created")
print(f"=====================================")

print(f"\n🚀 To run your tests:")
print(f"   cd {project_path}")
print(f"   npm install --save-dev @testing-library/react @testing-library/jest-dom jest-axe")
print(f"   npm test")
print(f"\n📊 To check coverage:")
print(f"   npm test -- --coverage")
