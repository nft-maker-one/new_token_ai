#!/usr/bin/env python3
"""
自动化测试脚本 - 修复前端问题并启动服务
"""

import os
import sys
import subprocess
import time
import json
import threading
from pathlib import Path

def print_step(step, color="blue"):
    colors = {
        "red": "\033[91m",
        "green": "\033[92m", 
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "purple": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "end": "\033[0m"
    }
    print(f"\n{colors.get(color, '')}{step}{colors['end']}")
    print("-" * 60)

def run_command(command, cwd=None, timeout=30):
    """运行命令并返回结果"""
    print(f"💻 执行: {command}")
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            cwd=cwd, 
            timeout=timeout,
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr and result.returncode != 0:
            print(f"错误: {result.stderr}")
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"⏰ 命令超时 ({timeout}秒)")
        return False
    except Exception as e:
        print(f"❌ 命令执行失败: {e}")
        return False

def fix_frontend():
    """修复前端配置"""
    print_step("🔧 修复前端配置", "yellow")
    
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("❌ frontend目录不存在")
        return False
    
    # 1. 清理缓存
    print("🧹 清理缓存...")
    node_modules = frontend_dir / "node_modules"
    package_lock = frontend_dir / "package-lock.json"
    
    if node_modules.exists():
        import shutil
        shutil.rmtree(node_modules)
        print("✓ node_modules已删除")
    
    if package_lock.exists():
        package_lock.unlink()
        print("✓ package-lock.json已删除")
    
    # 2. 更新.env文件
    env_file = frontend_dir / ".env"
    env_content = """SKIP_PREFLIGHT_CHECK=true
GENERATE_SOURCEMAP=false
FAST_REFRESH=false
WDS_SOCKET_HOST=localhost
WDS_SOCKET_PORT=3000
CHOKIDAR_USEPOLLING=true
"""
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(env_content)
    print("✓ .env文件已更新")
    
    # 3. 重新安装依赖
    print("📦 重新安装依赖...")
    if not run_command("npm install", cwd=frontend_dir, timeout=120):
        print("❌ npm install失败")
        return False
    
    print("✓ 前端修复完成")
    return True

def start_backend():
    """启动后端服务"""
    print_step("🚀 启动后端服务", "green")
    
    # 检查虚拟环境
    if not Path("venv").exists():
        print("❌ 虚拟环境不存在，请先运行 python -m venv venv")
        return None
    
    # 检查依赖
    if os.name == 'nt':  # Windows
        python_cmd = "venv\\Scripts\\python"
        pip_cmd = "venv\\Scripts\\pip"
    else:
        python_cmd = "venv/bin/python"
        pip_cmd = "venv/bin/pip"
    
    # 安装后端依赖
    print("📦 检查后端依赖...")
    run_command(f"{pip_cmd} install -r requirements.txt", timeout=120)
    
    # 启动后端
    print("🔥 启动后端服务...")
    try:
        process = subprocess.Popen(
            [python_cmd, "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 等待服务启动
        time.sleep(5)
        
        if process.poll() is None:
            print("✓ 后端服务启动成功 (PID: {})".format(process.pid))
            print("📍 后端地址: http://localhost:8000")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ 后端启动失败")
            print(f"输出: {stdout}")
            print(f"错误: {stderr}")
            return None
            
    except Exception as e:
        print(f"❌ 启动后端失败: {e}")
        return None

def start_frontend():
    """启动前端服务"""
    print_step("🎨 启动前端服务", "cyan")
    
    frontend_dir = Path("frontend")
    
    # 设置环境变量
    env = os.environ.copy()
    env.update({
        "SKIP_PREFLIGHT_CHECK": "true",
        "GENERATE_SOURCEMAP": "false",
        "FAST_REFRESH": "false",
        "WDS_SOCKET_HOST": "localhost",
        "WDS_SOCKET_PORT": "3000"
    })
    
    try:
        print("🔥 启动前端服务...")
        process = subprocess.Popen(
            ["npm", "start"],
            cwd=frontend_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 等待服务启动
        time.sleep(10)
        
        if process.poll() is None:
            print("✓ 前端服务启动成功 (PID: {})".format(process.pid))
            print("📍 前端地址: http://localhost:3000")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ 前端启动失败")
            print(f"输出: {stdout}")
            print(f"错误: {stderr}")
            return None
            
    except Exception as e:
        print(f"❌ 启动前端失败: {e}")
        return None

def test_services():
    """测试服务是否正常"""
    print_step("🧪 测试服务", "purple")
    
    import requests
    
    # 测试后端
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            print("✓ 后端服务正常")
        else:
            print(f"⚠️ 后端响应异常: {response.status_code}")
    except Exception as e:
        print(f"❌ 后端测试失败: {e}")
    
    # 测试前端
    try:
        response = requests.get("http://localhost:3000/", timeout=5)
        if response.status_code == 200:
            print("✓ 前端服务正常")
        else:
            print(f"⚠️ 前端响应异常: {response.status_code}")
    except Exception as e:
        print(f"❌ 前端测试失败: {e}")

def monitor_services(backend_process, frontend_process):
    """监控服务状态"""
    print_step("📊 服务监控", "white")
    
    print("🎯 服务已启动，监控中...")
    print("📍 前端地址: http://localhost:3000")
    print("📍 后端地址: http://localhost:8000")
    print("📍 API文档: http://localhost:8000/docs")
    print("⚠️  按Ctrl+C停止所有服务")
    
    try:
        while True:
            time.sleep(5)
            
            # 检查进程状态
            if backend_process and backend_process.poll() is not None:
                print("❌ 后端服务已停止")
                break
                
            if frontend_process and frontend_process.poll() is not None:
                print("❌ 前端服务已停止")
                break
                
    except KeyboardInterrupt:
        print("\n👋 用户请求停止服务")
    
    # 停止服务
    if backend_process and backend_process.poll() is None:
        print("🛑 停止后端服务...")
        backend_process.terminate()
        backend_process.wait()
    
    if frontend_process and frontend_process.poll() is None:
        print("🛑 停止前端服务...")
        frontend_process.terminate()
        frontend_process.wait()
    
    print("✓ 所有服务已停止")

def main():
    """主函数"""
    print("🤖 AI Crypto Token Analysis 自动化测试")
    print("=" * 60)
    
    # 检查环境
    if not Path("frontend").exists() or not Path("backend").exists():
        print("❌ 请在项目根目录运行此脚本")
        sys.exit(1)
    
    # 步骤1: 修复前端
    if not fix_frontend():
        print("❌ 前端修复失败")
        sys.exit(1)
    
    # 步骤2: 启动后端
    backend_process = start_backend()
    if not backend_process:
        print("❌ 后端启动失败")
        sys.exit(1)
    
    # 步骤3: 启动前端
    frontend_process = start_frontend()
    if not frontend_process:
        print("❌ 前端启动失败")
        if backend_process:
            backend_process.terminate()
        sys.exit(1)
    
    # 步骤4: 测试服务
    time.sleep(3)
    test_services()
    
    # 步骤5: 监控服务
    monitor_services(backend_process, frontend_process)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
