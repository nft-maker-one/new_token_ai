#!/usr/bin/env python3
"""
修复WebSocket连接问题的脚本
"""

import os
import sys
import subprocess
import time
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

def check_processes():
    """检查是否有残留进程"""
    print_step("🔍 检查残留进程", "yellow")
    
    # 检查后端进程
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq python.exe"],
            capture_output=True,
            text=True
        )
        if "uvicorn" in result.stdout or "backend.main" in result.stdout:
            print("⚠️  发现后端进程正在运行")
            response = input("是否终止现有后端进程? (y/N): ")
            if response.lower() == 'y':
                run_command("taskkill /F /IM python.exe")
                time.sleep(2)
        else:
            print("✓ 没有发现残留的后端进程")
    except Exception as e:
        print(f"检查进程时出错: {e}")
    
    # 检查前端进程
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq node.exe"],
            capture_output=True,
            text=True
        )
        if "node.exe" in result.stdout:
            print("⚠️  发现Node.js进程正在运行")
            response = input("是否终止现有Node.js进程? (y/N): ")
            if response.lower() == 'y':
                run_command("taskkill /F /IM node.exe")
                time.sleep(2)
        else:
            print("✓ 没有发现残留的Node.js进程")
    except Exception as e:
        print(f"检查Node.js进程时出错: {e}")

def start_backend():
    """启动后端服务"""
    print_step("🚀 启动后端服务", "green")
    
    # 检查虚拟环境
    if not Path("venv").exists():
        print("❌ 虚拟环境不存在")
        return None
    
    # 启动后端
    if os.name == 'nt':  # Windows
        python_cmd = "venv\\Scripts\\python"
    else:
        python_cmd = "venv/bin/python"
    
    try:
        print("🔥 启动后端服务...")
        process = subprocess.Popen(
            [python_cmd, "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 等待服务启动
        time.sleep(5)
        
        if process.poll() is None:
            print("✓ 后端服务启动成功")
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
        "WDS_SOCKET_PORT": "3000",
        "CHOKIDAR_USEPOLLING": "true"
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
        time.sleep(15)
        
        if process.poll() is None:
            print("✓ 前端服务启动成功")
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

def test_websocket():
    """测试WebSocket连接"""
    print_step("🧪 测试WebSocket连接", "purple")
    
    try:
        import websockets
        import asyncio
        
        async def test_connection():
            try:
                uri = "ws://localhost:8000/ws"
                async with websockets.connect(uri) as websocket:
                    print("✓ WebSocket连接成功")
                    
                    # 发送ping消息
                    await websocket.send("ping")
                    response = await asyncio.wait_for(websocket.recv(), timeout=5)
                    
                    if response == "pong":
                        print("✓ WebSocket通信正常")
                        return True
                    else:
                        print(f"⚠️ 意外的响应: {response}")
                        return False
                        
            except Exception as e:
                print(f"❌ WebSocket测试失败: {e}")
                return False
        
        return asyncio.run(test_connection())
        
    except ImportError:
        print("⚠️ websockets库未安装，跳过WebSocket测试")
        return True
    except Exception as e:
        print(f"❌ WebSocket测试异常: {e}")
        return False

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
    print("🔧 WebSocket连接问题修复工具")
    print("=" * 60)
    
    # 检查环境
    if not Path("frontend").exists() or not Path("backend").exists():
        print("❌ 请在项目根目录运行此脚本")
        sys.exit(1)
    
    # 步骤1: 检查残留进程
    check_processes()
    
    # 步骤2: 启动后端
    backend_process = start_backend()
    if not backend_process:
        print("❌ 后端启动失败，无法继续")
        sys.exit(1)
    
    # 步骤3: 测试WebSocket
    time.sleep(3)
    if not test_websocket():
        print("⚠️ WebSocket测试失败，但继续启动前端")
    
    # 步骤4: 启动前端
    frontend_process = start_frontend()
    if not frontend_process:
        print("❌ 前端启动失败")
        if backend_process:
            backend_process.terminate()
        sys.exit(1)
    
    # 步骤5: 监控服务
    monitor_services(backend_process, frontend_process)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 修复被用户中断")
    except Exception as e:
        print(f"\n❌ 修复失败: {e}")
        sys.exit(1)
