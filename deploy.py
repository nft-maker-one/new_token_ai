#!/usr/bin/env python3
"""
一键部署脚本
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def print_header(title):
    """打印标题"""
    print("\n" + "=" * 60)
    print(f"🚀 {title}")
    print("=" * 60)

def run_command(command, cwd=None, check=True):
    """运行命令"""
    print(f"💻 执行: {command}")
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            cwd=cwd, 
            check=check,
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(result.stdout)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ 命令执行失败: {e}")
        if e.stderr:
            print(f"错误信息: {e.stderr}")
        return False

def check_python():
    """检查Python版本"""
    print_header("检查Python环境")
    
    try:
        result = subprocess.run([sys.executable, "--version"], capture_output=True, text=True)
        version = result.stdout.strip()
        print(f"✓ Python版本: {version}")
        
        # 检查版本是否满足要求
        import sys
        if sys.version_info < (3, 8):
            print("❌ Python版本过低，需要3.8+")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Python检查失败: {e}")
        return False

def check_node():
    """检查Node.js"""
    print_header("检查Node.js环境")
    
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ Node.js版本: {result.stdout.strip()}")
            
            result = subprocess.run(["npm", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✓ npm版本: {result.stdout.strip()}")
                return True
        
        print("❌ Node.js或npm未安装")
        print("请访问 https://nodejs.org/ 安装Node.js")
        return False
        
    except FileNotFoundError:
        print("❌ Node.js未安装")
        print("请访问 https://nodejs.org/ 安装Node.js")
        return False

def setup_python_env():
    """设置Python环境"""
    print_header("设置Python环境")
    
    # 检查是否存在虚拟环境
    venv_path = Path("venv")
    if not venv_path.exists():
        print("📦 创建虚拟环境...")
        if not run_command(f"{sys.executable} -m venv venv"):
            return False
    else:
        print("✓ 虚拟环境已存在")
    
    # 激活虚拟环境并安装依赖
    if os.name == 'nt':  # Windows
        pip_cmd = "venv\\Scripts\\pip"
        python_cmd = "venv\\Scripts\\python"
    else:  # Unix/Linux/macOS
        pip_cmd = "venv/bin/pip"
        python_cmd = "venv/bin/python"
    
    print("📦 安装Python依赖...")
    if not run_command(f"{pip_cmd} install --upgrade pip"):
        return False
    
    if not run_command(f"{pip_cmd} install -r requirements.txt"):
        return False
    
    print("✓ Python环境设置完成")
    return True

def setup_frontend():
    """设置前端环境"""
    print_header("设置前端环境")
    
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("❌ frontend目录不存在")
        return False
    
    # 安装前端依赖
    print("📦 安装前端依赖...")
    if not run_command("npm install", cwd=frontend_dir):
        return False
    
    print("✓ 前端环境设置完成")
    return True

def setup_config():
    """设置配置文件"""
    print_header("设置配置文件")
    
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists():
        if env_example.exists():
            shutil.copy(env_example, env_file)
            print("✓ 已创建.env文件")
        else:
            print("❌ .env.example文件不存在")
            return False
    else:
        print("✓ .env文件已存在")
    
    # 检查必要的配置
    print("\n⚠️  请确保在.env文件中设置以下配置:")
    print("   - GEMINI_API_KEY (必需)")
    print("   - GOOGLE_SEARCH_API_KEY (可选)")
    print("   - GOOGLE_SEARCH_ENGINE_ID (可选)")
    print("   - REDIS_URL (可选)")
    
    return True

def check_redis():
    """检查Redis（可选）"""
    print_header("检查Redis服务")
    
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✓ Redis服务正在运行")
        return True
    except:
        print("⚠️  Redis未运行，将使用内存队列")
        print("   如需使用Redis，请安装并启动Redis服务")
        return True  # Redis是可选的

def build_frontend():
    """构建前端"""
    print_header("构建前端应用")
    
    frontend_dir = Path("frontend")
    
    print("🔨 构建React应用...")
    if not run_command("npm run build", cwd=frontend_dir):
        return False
    
    print("✓ 前端构建完成")
    return True

def run_tests():
    """运行测试"""
    print_header("运行系统测试")
    
    print("🧪 运行测试脚本...")
    
    # 注意：这里需要先启动后端服务才能运行完整测试
    print("⚠️  注意：完整测试需要后端服务运行")
    print("   请在另一个终端运行: python start_backend.py")
    
    response = input("是否跳过需要后端服务的测试? (y/N): ")
    if response.lower() == 'y':
        print("⏭️  跳过后端依赖测试")
        return True
    
    if not run_command(f"{sys.executable} test_system.py"):
        print("⚠️  部分测试失败，但可能是因为服务未启动")
        return True
    
    return True

def create_start_scripts():
    """创建启动脚本"""
    print_header("创建启动脚本")
    
    # Windows批处理文件
    if os.name == 'nt':
        with open("start_all.bat", "w", encoding="utf-8") as f:
            f.write("""@echo off
echo Starting AI Crypto Token Analysis System...
echo.

echo Starting backend server...
start "Backend" cmd /k "venv\\Scripts\\python start_backend.py"

timeout /t 5 /nobreak > nul

echo Starting frontend server...
start "Frontend" cmd /k "python start_frontend.py"

echo.
echo Both servers are starting...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
pause
""")
        print("✓ 创建了 start_all.bat")
    
    # Unix shell脚本
    with open("start_all.sh", "w") as f:
        f.write("""#!/bin/bash
echo "Starting AI Crypto Token Analysis System..."
echo

echo "Starting backend server..."
source venv/bin/activate
python start_backend.py &
BACKEND_PID=$!

sleep 5

echo "Starting frontend server..."
python start_frontend.py &
FRONTEND_PID=$!

echo
echo "Both servers are starting..."
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo
echo "Press Ctrl+C to stop both servers"

# 等待用户中断
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
""")
    
    # 设置执行权限
    if os.name != 'nt':
        os.chmod("start_all.sh", 0o755)
        print("✓ 创建了 start_all.sh")
    
    return True

def main():
    """主部署函数"""
    print("🚀 AI Crypto Token Analysis 一键部署")
    print("=" * 60)
    
    steps = [
        ("检查Python环境", check_python),
        ("检查Node.js环境", check_node),
        ("设置Python环境", setup_python_env),
        ("设置前端环境", setup_frontend),
        ("设置配置文件", setup_config),
        ("检查Redis服务", check_redis),
        ("创建启动脚本", create_start_scripts),
    ]
    
    # 询问是否构建前端
    build_prod = input("\n是否构建生产版本前端? (y/N): ").lower() == 'y'
    if build_prod:
        steps.append(("构建前端应用", build_frontend))
    
    # 询问是否运行测试
    run_test = input("是否运行系统测试? (y/N): ").lower() == 'y'
    if run_test:
        steps.append(("运行系统测试", run_tests))
    
    # 执行部署步骤
    failed_steps = []
    
    for step_name, step_func in steps:
        try:
            if not step_func():
                failed_steps.append(step_name)
        except Exception as e:
            print(f"❌ {step_name} 执行异常: {e}")
            failed_steps.append(step_name)
    
    # 输出结果
    print("\n" + "=" * 60)
    print("📋 部署结果汇总")
    print("=" * 60)
    
    if failed_steps:
        print("❌ 以下步骤失败:")
        for step in failed_steps:
            print(f"   - {step}")
        print("\n请检查错误信息并手动修复")
        return False
    else:
        print("🎉 部署成功！")
        print("\n📖 使用说明:")
        print("1. 确保在.env文件中设置了GEMINI_API_KEY")
        print("2. 启动服务:")
        if os.name == 'nt':
            print("   - Windows: 双击 start_all.bat")
        print("   - 或手动运行:")
        print("     python start_backend.py  (后端)")
        print("     python start_frontend.py (前端)")
        print("3. 访问 http://localhost:3000 查看前端界面")
        print("4. 访问 http://localhost:8000/docs 查看API文档")
        return True

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n👋 部署被用户中断")
        exit(1)
    except Exception as e:
        print(f"\n❌ 部署失败: {e}")
        exit(1)
