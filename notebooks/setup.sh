#!/bin/bash

# Frontend Generator Notebooks Setup Script
# This script sets up the environment for running the notebooks

echo "🚀 Frontend Generator Notebooks Setup"
echo "======================================"

# Check Python version
python_version=$(python --version 2>&1)
echo "📍 Python version: $python_version"

# Check if we're in the right directory
if [ ! -f "requirements-notebooks.txt" ]; then
    echo "❌ Error: requirements-notebooks.txt not found"
    echo "💡 Please run this script from the notebooks directory"
    exit 1
fi

# Detect platform
if [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="mac"
    echo "🍎 Detected: macOS"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    PLATFORM="linux"
    echo "🐧 Detected: Linux"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    PLATFORM="windows"
    echo "🪟 Detected: Windows"
else
    PLATFORM="unknown"
    echo "❓ Unknown platform: $OSTYPE"
fi

# Check available memory
echo "💾 Checking system memory..."
if command -v free &> /dev/null; then
    memory_gb=$(free -g | awk '/^Mem:/{print $2}')
    echo "📊 Total RAM: ${memory_gb}GB"
elif [[ "$PLATFORM" == "mac" ]]; then
    memory_bytes=$(sysctl -n hw.memsize)
    memory_gb=$((memory_bytes / 1024 / 1024 / 1024))
    echo "📊 Total RAM: ${memory_gb}GB"
fi

# Install dependencies
echo ""
echo "📦 Installing Python dependencies..."
pip install --upgrade pip

# Install core requirements
echo "🔧 Installing core requirements..."
pip install -r requirements-notebooks.txt

# Platform-specific optimizations
if [[ "$PLATFORM" == "mac" ]]; then
    echo "🍎 Mac-specific optimizations..."
    
    # Check if we have Apple Silicon
    if [[ $(uname -m) == "arm64" ]]; then
        echo "🚀 Apple Silicon detected - installing optimized PyTorch"
        pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
    fi
    
    # Try to install vLLM for local inference
    echo "🤖 Installing vLLM for local model inference..."
    pip install vllm || echo "⚠️ vLLM installation failed - you can still use OpenAI API"
    
elif [[ "$PLATFORM" == "linux" ]]; then
    echo "🐧 Linux optimizations..."
    
    # Check for CUDA
    if command -v nvidia-smi &> /dev/null; then
        echo "🎮 NVIDIA GPU detected"
        pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
    else
        echo "🖥️ No NVIDIA GPU detected - using CPU version"
        pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
    fi
    
    pip install vllm || echo "⚠️ vLLM installation failed - you can still use OpenAI API"
fi

# Verify installations
echo ""
echo "🔍 Verifying installations..."

# Check vLLM
if python -c "import vllm" 2>/dev/null; then
    echo "✅ vLLM: Installed successfully"
else
    echo "❌ vLLM: Not available (you can still use OpenAI API)"
fi

# Check PyTorch
if python -c "import torch; print(f'PyTorch: {torch.__version__}')" 2>/dev/null; then
    echo "✅ PyTorch: Available"
else
    echo "❌ PyTorch: Installation failed"
fi

# Check Transformers
if python -c "import transformers; print(f'Transformers: {transformers.__version__}')" 2>/dev/null; then
    echo "✅ Transformers: Available"
else
    echo "❌ Transformers: Installation failed"
fi

# Check Jupyter
if python -c "import jupyter" 2>/dev/null; then
    echo "✅ Jupyter: Available"
else
    echo "❌ Jupyter: Installation failed"
fi

# Model recommendations
echo ""
echo "🎯 Model Recommendations:"

if [[ ${memory_gb:-0} -ge 18 ]]; then
    echo "💪 18GB+ RAM detected:"
    echo "   🥇 Recommended: deepseek-coder-6.7b-instruct (local)"
    echo "   🥈 Alternative: deepseek-coder-1.3b-instruct (faster)"
    echo "   🥉 Backup: OpenAI API (gpt-4o-mini)"
elif [[ ${memory_gb:-0} -ge 12 ]]; then
    echo "💻 12-18GB RAM detected:"
    echo "   🥇 Recommended: deepseek-coder-1.3b-instruct (local)"
    echo "   🥈 Alternative: OpenAI API (gpt-3.5-turbo)"
elif [[ ${memory_gb:-0} -ge 8 ]]; then
    echo "📱 8-12GB RAM detected:"
    echo "   🥇 Recommended: OpenAI API (gpt-3.5-turbo)"
    echo "   🥈 Alternative: Cloud notebooks (Colab/Kaggle)"
else
    echo "☁️ Limited RAM detected:"
    echo "   🥇 Recommended: Cloud notebooks (Colab/Kaggle)"
    echo "   🥈 Alternative: OpenAI API"
fi

# Next steps
echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "📚 Next Steps:"
echo "1. Choose your notebook based on your platform:"

if [[ "$PLATFORM" == "mac" ]] && [[ ${memory_gb:-0} -ge 16 ]]; then
    echo "   🍎 Use: Frontend_Generator_Mac_Local.ipynb (recommended for your system)"
else
    echo "   ☁️ Use: Frontend_Generator_Google_Colab.ipynb (cloud-based)"
fi

echo "   🏆 Alternative: Frontend_Generator_Kaggle.ipynb (powerful GPUs)"
echo ""
echo "2. Start Jupyter:"
echo "   jupyter notebook"
echo ""
echo "3. Open your chosen notebook and follow the instructions"
echo ""
echo "💡 Pro Tips:"
echo "   - Start with simple projects to test your setup"
echo "   - Monitor memory usage during generation"
echo "   - Use model caching to speed up subsequent runs"
echo ""
echo "🤝 Need help? Check the README.md or open an issue!"
echo ""
echo "Happy coding! 🚀"
