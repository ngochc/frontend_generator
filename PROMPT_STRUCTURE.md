# 📋 Frontend Generator Prompt Structure

This document outlines the complete prompt structure used in the Frontend Generator's three-stage pipeline.

## 🎯 Overview

The Frontend Generator uses a sophisticated prompt engineering approach with three specialized stages:

1. **🏗️ Planning Stage**: Architectural planning and technology selection
2. **🔍 Analysis Stage**: Detailed component design and technical specifications  
3. **⚛️ Coding Stage**: Individual component code generation

## 📝 Stage 1: Planning Prompts

### System Prompt (Planning)
```python
{
    'role': "system", 
    'content': """You are an expert frontend architect and React developer with deep understanding of modern web development practices and user experience design.

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

Format your response as a detailed implementation plan with clear sections and actionable steps."""
}
```

### User Prompt (Planning)
```python
{
    'role': "user", 
    'content': """Project Name: {project_name}

Requirements:
{requirements_content}

Please create a comprehensive frontend development plan for this React application."""
}
```

## 🔍 Stage 2: Analysis Prompts

### System Prompt (Analysis)
```python
{
    'role': "system", 
    'content': """You are an expert frontend architect, UX/UI designer, and React developer with deep understanding of component design patterns, state management, and modern web development practices.

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

Format your response as detailed technical specifications that can be directly implemented by developers."""
}
```

### User Prompt (Analysis)
```python
{
    'role': "user", 
    'content': """Project Name: {project_name}

Original Requirements:
{requirements_content}

Planning Output:
{planning_context}

Please provide detailed technical analysis and component specifications for this React frontend application."""
}
```

## ⚛️ Stage 3: Coding Prompts

### System Prompt (Coding) - Per Component
```python
{
    'role': "system", 
    'content': """You are an expert React developer and TypeScript specialist with deep knowledge of modern frontend development practices, component architecture, and code quality.

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

Generate ONLY the component code for {component_name} ({component_type}).
Include all necessary imports, types, and styling.
Make sure the code is complete and ready to use.

Format your response with the complete component code wrapped in ```tsx code blocks."""
}
```

### User Prompt (Coding) - Per Component
```python
{
    'role': "user", 
    'content': """Project Name: {project_name}

Component to Generate: {component_name} ({component_type})
Description: {component_description}
File Path: {component_path}

Original Requirements:
{requirements_content}

Technical Analysis:
{analysis_context}

Generate the complete React component code for {component_name}."""
}
```

## 🔄 Prompt Flow & Context Passing

### Context Chain
```
Requirements Document
       ↓
[Planning Stage]
   Input: Requirements
   Output: Architecture Plan
       ↓
[Analysis Stage]  
   Input: Requirements + Planning Output
   Output: Technical Specifications
       ↓
[Coding Stage]
   Input: Requirements + Analysis Output (per component)
   Output: React Component Code
```

### Component Generation Loop
```python
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
    # ... more components
]

for component in components_to_generate:
    # Generate individual coding prompt for each component
    # Use same requirements + analysis context
    # Customize for specific component type and purpose
```

## 🎛️ Prompt Parameters

### OpenAI Configuration
```python
response = client.chat.completions.create(
    model="o3-mini",                    # Model selection
    messages=prompt_messages,           # Prompt array
    temperature=0.2-0.7,               # Creativity (planning: 0.7, coding: 0.2)
    max_tokens=3000-6000,              # Response length
)
```

### vLLM Configuration  
```python
sampling_params = SamplingParams(
    temperature=0.2-0.7,               # Creativity level
    max_tokens=3000-6000,              # Response length
    top_p=0.95                         # Nucleus sampling
)

# Format for vLLM chat template
prompt = f"""<|im_start|>system
{system_content}<|im_end|>
<|im_start|>user  
{user_content}<|im_end|>
<|im_start|>assistant
"""
```

## 🎯 Prompt Engineering Strategies

### 1. **Role-Based Personas**
- **Planning**: Frontend architect and strategic planner
- **Analysis**: UX/UI designer and technical architect  
- **Coding**: React developer and TypeScript specialist

### 2. **Structured Instructions**
- Clear numbered sections for expected outputs
- Specific format requirements
- Technology constraints and preferences
- Quality standards and best practices

### 3. **Context Preservation**
- Requirements passed through all stages
- Previous stage outputs included in next stage
- Component-specific context for code generation

### 4. **Temperature Control**
- **Planning (0.7)**: Higher creativity for architectural decisions
- **Analysis (0.3)**: Balanced creativity for technical design
- **Coding (0.2)**: Lower creativity for consistent code quality

### 5. **Output Formatting**
- Markdown for documentation stages
- Code blocks for implementation
- Structured JSON where applicable

## 🔧 Prompt Customization

### Requirements Format Detection
```python
if requirements_format == "markdown":
    # Adjust prompts for markdown parsing
elif requirements_format == "json": 
    # Adjust prompts for JSON structure
elif requirements_format == "text":
    # Adjust prompts for plain text
```

### Complexity-Based Adjustments
```python
# Prompts adapt based on detected complexity
if "enterprise" in requirements:
    # Add enterprise-specific considerations
elif "healthcare" in requirements:
    # Add HIPAA and compliance considerations  
elif "trading" in requirements:
    # Add performance and real-time considerations
```

## 📊 Prompt Effectiveness Metrics

### Success Indicators
- **Planning**: Comprehensive architecture with technology decisions
- **Analysis**: Detailed component specifications with TypeScript interfaces
- **Coding**: Compilable React components with proper imports and styling

### Quality Measures
- **Consistency**: Components follow established patterns
- **Completeness**: All required functionality implemented
- **Best Practices**: Modern React patterns and TypeScript usage
- **Production Readiness**: Error handling, accessibility, performance

This prompt structure ensures consistent, high-quality React application generation across different project complexities and requirements.
