#!/usr/bin/env python3
"""
Frontend Generator Notebooks Setup Script
Cross-platform setup for notebook dependencies
"""

import sys
import subprocess
import platform
import os
import shutil
from pathlib import Path

def run_command(cmd, check=True, capture_output=True):
    """Run a command and return the result"""
    try:
        result = subprocess.run(cmd, shell=True, check=check, 
                              capture_output=capture_output, text=True)
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {cmd}")
        print(f"Error: {e}")
        return None

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    print(f"📍 Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ required")
        return False
    return True

def get_system_info():
    """Get system information"""
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    print(f"💻 System: {platform.system()} {platform.release()}")
    print(f"🔧 Architecture: {machine}")
    
    # Get memory info
    memory_gb = 0
    try:
        if system == "linux":
            result = run_command("free -g | awk '/^Mem:/{print $2}'")
            if result and result.stdout.strip():
                memory_gb = int(result.stdout.strip())
        elif system == "darwin":  # macOS
            result = run_command("sysctl -n hw.memsize")
            if result and result.stdout.strip():
                memory_bytes = int(result.stdout.strip())
                memory_gb = memory_bytes // (1024 ** 3)
        elif system == "windows":
            result = run_command('wmic computersystem get TotalPhysicalMemory /value | findstr "="')
            if result and result.stdout.strip():
                for line in result.stdout.split('\n'):
                    if 'TotalPhysicalMemory' in line:
                        memory_bytes = int(line.split('=')[1])
                        memory_gb = memory_bytes // (1024 ** 3)
                        break
    except:
        pass
    
    print(f"💾 Total RAM: {memory_gb}GB")
    return system, machine, memory_gb

def install_dependencies():
    """Install Python dependencies"""
    print("\n📦 Installing Python dependencies...")
    
    # Upgrade pip
    print("🔧 Upgrading pip...")
    run_command(f"{sys.executable} -m pip install --upgrade pip")
    
    # Check if requirements file exists
    req_file = "requirements-notebooks.txt"
    if not os.path.exists(req_file):
        print(f"❌ {req_file} not found")
        print("💡 Please run this script from the notebooks directory")
        return False
    
    # Install requirements
    print(f"📋 Installing from {req_file}...")
    result = run_command(f"{sys.executable} -m pip install -r {req_file}")
    
    if result and result.returncode == 0:
        print("✅ Core dependencies installed")
        return True
    else:
        print("❌ Failed to install some dependencies")
        return False

def install_pytorch(system, machine):
    """Install PyTorch with appropriate configuration"""
    print("\n🔥 Installing PyTorch...")
    
    # Check for CUDA
    cuda_available = False
    if system == "linux" or system == "windows":
        result = run_command("nvidia-smi", check=False)
        cuda_available = result and result.returncode == 0
    
    if cuda_available:
        print("🎮 NVIDIA GPU detected - installing CUDA version")
        cmd = f"{sys.executable} -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118"
    elif system == "darwin" and "arm" in machine:
        print("🍎 Apple Silicon detected - installing optimized version")
        cmd = f"{sys.executable} -m pip install torch torchvision"
    else:
        print("🖥️ Installing CPU version")
        cmd = f"{sys.executable} -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu"
    
    result = run_command(cmd)
    return result and result.returncode == 0

def install_vllm():
    """Install vLLM for local model inference"""
    print("\n🤖 Installing vLLM for local model inference...")
    
    result = run_command(f"{sys.executable} -m pip install vllm", check=False)
    
    if result and result.returncode == 0:
        print("✅ vLLM installed successfully")
        return True
    else:
        print("⚠️ vLLM installation failed - you can still use OpenAI API")
        print("💡 This is normal on some systems (Apple Silicon, older hardware)")
        return False

def verify_installations():
    """Verify that key packages are installed correctly"""
    print("\n🔍 Verifying installations...")
    
    packages = {
        "vllm": "vLLM",
        "torch": "PyTorch", 
        "transformers": "Transformers",
        "jupyter": "Jupyter",
        "openai": "OpenAI"
    }
    
    results = {}
    for package, name in packages.items():
        try:
            result = run_command(f"{sys.executable} -c 'import {package}'", check=False)
            if result and result.returncode == 0:
                print(f"✅ {name}: Available")
                results[package] = True
            else:
                print(f"❌ {name}: Not available")
                results[package] = False
        except:
            print(f"❌ {name}: Error checking")
            results[package] = False
    
    return results

def recommend_models(memory_gb, system):
    """Recommend models based on system capabilities"""
    print(f"\n🎯 Model Recommendations:")
    
    if memory_gb >= 18:
        print("💪 18GB+ RAM detected:")
        print("   🥇 Recommended: deepseek-coder-6.7b-instruct (local)")
        print("   🥈 Alternative: deepseek-coder-1.3b-instruct (faster)")
        print("   🥉 Backup: OpenAI API (gpt-4o-mini)")
        return "local-6.7b"
    elif memory_gb >= 12:
        print("💻 12-18GB RAM detected:")
        print("   🥇 Recommended: deepseek-coder-1.3b-instruct (local)")
        print("   🥈 Alternative: OpenAI API (gpt-3.5-turbo)")
        return "local-1.3b"
    elif memory_gb >= 8:
        print("📱 8-12GB RAM detected:")
        print("   🥇 Recommended: OpenAI API (gpt-3.5-turbo)")
        print("   🥈 Alternative: Cloud notebooks (Colab/Kaggle)")
        return "api"
    else:
        print("☁️ Limited RAM detected:")
        print("   🥇 Recommended: Cloud notebooks (Colab/Kaggle)")
        print("   🥈 Alternative: OpenAI API")
        return "cloud"

def recommend_notebook(memory_gb, system, vllm_available):
    """Recommend which notebook to use"""
    print(f"\n📚 Notebook Recommendations:")
    
    if system == "darwin" and memory_gb >= 16 and vllm_available:
        print("   🍎 Use: Frontend_Generator_Mac_Local.ipynb (optimal for your Mac)")
    elif memory_gb >= 16 and vllm_available:
        print("   💻 Use: Frontend_Generator_Mac_Local.ipynb (works on your system)")
    else:
        print("   ☁️ Use: Frontend_Generator_Google_Colab.ipynb (cloud-based)")
    
    print("   🏆 Alternative: Frontend_Generator_Kaggle.ipynb (powerful GPUs)")

def show_next_steps():
    """Show next steps for the user"""
    print(f"\n🎉 Setup Complete!")
    print("==================")
    print()
    print("📚 Next Steps:")
    print("1. Start Jupyter:")
    print("   jupyter notebook")
    print()
    print("2. Open your recommended notebook")
    print("3. Follow the instructions in the notebook")
    print()
    print("💡 Pro Tips:")
    print("   - Start with simple projects to test your setup")
    print("   - Monitor memory usage during generation")
    print("   - Use model caching to speed up subsequent runs")
    print()
    print("🤝 Need help? Check the README.md or open an issue!")
    print()
    print("Happy coding! 🚀")

def main():
    """Main setup function"""
    print("🚀 Frontend Generator Notebooks Setup")
    print("======================================")
    
    # Check Python version
    if not check_python_version():
        return 1
    
    # Get system information
    system, machine, memory_gb = get_system_info()
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Setup failed during dependency installation")
        return 1
    
    # Install PyTorch
    pytorch_success = install_pytorch(system, machine)
    if not pytorch_success:
        print("⚠️ PyTorch installation had issues")
    
    # Install vLLM
    vllm_success = install_vllm()
    
    # Verify installations
    results = verify_installations()
    
    # Recommend models and notebooks
    recommend_models(memory_gb, system)
    recommend_notebook(memory_gb, system, results.get('vllm', False))
    
    # Show next steps
    show_next_steps()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
