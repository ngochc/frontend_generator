@echo off
echo 🚀 Frontend Generator Notebooks Setup
echo ======================================

REM Check Python version
python --version
if %errorlevel% neq 0 (
    echo ❌ Python not found. Please install Python 3.8+ first
    pause
    exit /b 1
)

REM Check if we're in the right directory
if not exist "requirements-notebooks.txt" (
    echo ❌ Error: requirements-notebooks.txt not found
    echo 💡 Please run this script from the notebooks directory
    pause
    exit /b 1
)

echo 🪟 Detected: Windows

REM Check available memory
echo 💾 Checking system memory...
for /f "tokens=2 delims==" %%i in ('wmic computersystem get TotalPhysicalMemory /value') do set memory_bytes=%%i
set /a memory_gb=%memory_bytes:~0,-10%
echo 📊 Total RAM: %memory_gb%GB

REM Install dependencies
echo.
echo 📦 Installing Python dependencies...
python -m pip install --upgrade pip

REM Install core requirements
echo 🔧 Installing core requirements...
python -m pip install -r requirements-notebooks.txt

REM Windows-specific optimizations
echo 🪟 Windows optimizations...

REM Check for CUDA
nvidia-smi >nul 2>&1
if %errorlevel% equ 0 (
    echo 🎮 NVIDIA GPU detected
    python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
) else (
    echo 🖥️ No NVIDIA GPU detected - using CPU version
    python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
)

echo 🤖 Installing vLLM for local model inference...
python -m pip install vllm
if %errorlevel% neq 0 (
    echo ⚠️ vLLM installation failed - you can still use OpenAI API
)

REM Verify installations
echo.
echo 🔍 Verifying installations...

REM Check vLLM
python -c "import vllm" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ vLLM: Installed successfully
) else (
    echo ❌ vLLM: Not available (you can still use OpenAI API^)
)

REM Check PyTorch
python -c "import torch; print(f'PyTorch: {torch.__version__}')" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ PyTorch: Available
) else (
    echo ❌ PyTorch: Installation failed
)

REM Check Transformers
python -c "import transformers; print(f'Transformers: {transformers.__version__}')" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Transformers: Available
) else (
    echo ❌ Transformers: Installation failed
)

REM Check Jupyter
python -c "import jupyter" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Jupyter: Available
) else (
    echo ❌ Jupyter: Installation failed
)

REM Model recommendations
echo.
echo 🎯 Model Recommendations:

if %memory_gb% geq 18 (
    echo 💪 18GB+ RAM detected:
    echo    🥇 Recommended: deepseek-coder-6.7b-instruct (local^)
    echo    🥈 Alternative: deepseek-coder-1.3b-instruct (faster^)
    echo    🥉 Backup: OpenAI API (gpt-4o-mini^)
) else if %memory_gb% geq 12 (
    echo 💻 12-18GB RAM detected:
    echo    🥇 Recommended: deepseek-coder-1.3b-instruct (local^)
    echo    🥈 Alternative: OpenAI API (gpt-3.5-turbo^)
) else if %memory_gb% geq 8 (
    echo 📱 8-12GB RAM detected:
    echo    🥇 Recommended: OpenAI API (gpt-3.5-turbo^)
    echo    🥈 Alternative: Cloud notebooks (Colab/Kaggle^)
) else (
    echo ☁️ Limited RAM detected:
    echo    🥇 Recommended: Cloud notebooks (Colab/Kaggle^)
    echo    🥈 Alternative: OpenAI API
)

REM Next steps
echo.
echo 🎉 Setup Complete!
echo ==================
echo.
echo 📚 Next Steps:
echo 1. Choose your notebook based on your platform:

if %memory_gb% geq 16 (
    echo    💻 Use: Frontend_Generator_Mac_Local.ipynb (works on Windows too^)
) else (
    echo    ☁️ Use: Frontend_Generator_Google_Colab.ipynb (cloud-based^)
)

echo    🏆 Alternative: Frontend_Generator_Kaggle.ipynb (powerful GPUs^)
echo.
echo 2. Start Jupyter:
echo    jupyter notebook
echo.
echo 3. Open your chosen notebook and follow the instructions
echo.
echo 💡 Pro Tips:
echo    - Start with simple projects to test your setup
echo    - Monitor memory usage during generation
echo    - Use model caching to speed up subsequent runs
echo.
echo 🤝 Need help? Check the README.md or open an issue!
echo.
echo Happy coding! 🚀
echo.
pause
