#!/bin/bash

# Frontend Generator with vLLM - React Application Generation Script
# Usage: bash run_frontend_llm.sh

# Default values
PROJECT_NAME="sample-dashboard"
REQUIREMENTS_PATH="../examples/dashboard_requirements.md"
OUTPUT_BASE_DIR="../outputs"
MODEL_NAME="deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct"

# Override with environment variables if set
PROJECT_NAME=${PROJECT_NAME:-"sample-dashboard"}
REQUIREMENTS_PATH=${REQUIREMENTS_PATH:-"../examples/dashboard_requirements.md"}
OUTPUT_BASE_DIR=${OUTPUT_BASE_DIR:-"../outputs"}
MODEL_NAME=${MODEL_NAME:-"deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct"}

# Check if requirements file exists
if [ ! -f "$REQUIREMENTS_PATH" ]; then
    echo "❌ Error: Requirements file not found at $REQUIREMENTS_PATH"
    echo "Please provide a valid requirements file path"
    exit 1
fi

# Create output directories
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
OUTPUT_DIR="$OUTPUT_BASE_DIR/$PROJECT_NAME"
REPO_OUTPUT_DIR="$OUTPUT_BASE_DIR"

mkdir -p "$OUTPUT_DIR/planning_artifacts"
mkdir -p "$OUTPUT_DIR/analyzing_artifacts" 
mkdir -p "$OUTPUT_DIR/coding_artifacts"

echo "🎨 Frontend Generator with vLLM - React Application Creation"
echo "==========================================================="
echo "📁 Project Name: $PROJECT_NAME"
echo "📄 Requirements: $REQUIREMENTS_PATH"
echo "🤖 Model: $MODEL_NAME"
echo "📂 Output Directory: $OUTPUT_DIR"
echo "==========================================================="
echo ""

# Stage 1: Planning with vLLM
echo "🎯 Stage 1: Frontend Architecture Planning (vLLM)"
echo "------------------------------------------------"
python ../codes/1_planning_llm.py \
    --project_name "$PROJECT_NAME" \
    --model_name "$MODEL_NAME" \
    --requirements_format "markdown" \
    --requirements_path "$REQUIREMENTS_PATH" \
    --output_dir "$OUTPUT_DIR/planning_artifacts" \
    --temperature 0.7 \
    --max_model_len 128000

if [ $? -ne 0 ]; then
    echo "❌ Planning stage failed"
    exit 1
fi

echo ""
echo "✅ Planning completed successfully"
echo ""

# Stage 2: Analysis with vLLM
echo "🔍 Stage 2: Technical Analysis & Component Design (vLLM)"
echo "-------------------------------------------------------"
python ../codes/2_analyzing_llm.py \
    --project_name "$PROJECT_NAME" \
    --model_name "$MODEL_NAME" \
    --requirements_format "markdown" \
    --requirements_path "$REQUIREMENTS_PATH" \
    --output_dir "$OUTPUT_DIR/analyzing_artifacts" \
    --temperature 0.3 \
    --max_model_len 128000

if [ $? -ne 0 ]; then
    echo "❌ Analysis stage failed"
    exit 1
fi

echo ""
echo "✅ Analysis completed successfully"
echo ""

# Stage 3: Code Generation with vLLM
echo "⚛️ Stage 3: React Code Generation (vLLM)"
echo "---------------------------------------"
python ../codes/3_coding_llm.py \
    --project_name "$PROJECT_NAME" \
    --model_name "$MODEL_NAME" \
    --requirements_format "markdown" \
    --requirements_path "$REQUIREMENTS_PATH" \
    --output_dir "$OUTPUT_DIR/coding_artifacts" \
    --output_repo_dir "$REPO_OUTPUT_DIR" \
    --temperature 0.2 \
    --max_model_len 128000

if [ $? -ne 0 ]; then
    echo "❌ Code generation stage failed"
    exit 1
fi

echo ""
echo "🎉 Frontend Generation Completed Successfully!"
echo "=============================================="
echo "📁 Project Location: $REPO_OUTPUT_DIR/${PROJECT_NAME}_frontend"
echo "📊 Artifacts: $OUTPUT_DIR"
echo ""

# Optional Stage 4: Test Generation
echo "🧪 Stage 4: Test Suite Generation (Optional)"
echo "-------------------------------------------"
read -p "Generate comprehensive test suite? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Generating test suite with vLLM..."
    
    python ../codes/4_testing_llm.py \
        --project_name "$PROJECT_NAME" \
        --model_name "$MODEL_NAME" \
        --project_path "$REPO_OUTPUT_DIR/${PROJECT_NAME}_frontend" \
        --requirements_path "$REQUIREMENTS_PATH" \
        --test_types "unit,integration" \
        --test_framework "jest" \
        --temperature 0.2 \
        --max_model_len 128000

    if [ $? -eq 0 ]; then
        echo "✅ Test generation completed successfully"
    else
        echo "⚠️ Test generation failed, but main application is ready"
    fi
    echo ""
fi

echo "🚀 To run your generated React application:"
echo "   cd $REPO_OUTPUT_DIR/${PROJECT_NAME}_frontend"
echo "   npm install"
echo "   npm start"
echo ""
echo "🧪 To run tests (if generated):"
echo "   npm test"
echo ""
echo "🌐 The application will be available at http://localhost:3000"
