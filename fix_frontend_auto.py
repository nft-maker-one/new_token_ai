#!/usr/bin/env python3
"""
自动修复前端启动问题的脚本
"""

import os
import sys
import subprocess
import json
import time
import shutil
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

def run_command(command, cwd=None, timeout=120):
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

def fix_package_json():
    """修复package.json配置"""
    print_step("🔧 修复package.json配置", "yellow")
    
    frontend_dir = Path("frontend")
    package_json_path = frontend_dir / "package.json"
    
    if not package_json_path.exists():
        print("❌ package.json不存在")
        return False
    
    # 读取现有配置
    with open(package_json_path, 'r', encoding='utf-8') as f:
        package_data = json.load(f)
    
    # 更新react-scripts版本到最新稳定版
    package_data["dependencies"]["react-scripts"] = "5.0.1"
    
    # 移除可能导致问题的resolutions
    if "resolutions" in package_data:
        del package_data["resolutions"]
    
    # 更新scripts，使用CRACO来覆盖webpack配置
    package_data["scripts"] = {
        "start": "react-scripts start",
        "build": "react-scripts build",
        "test": "react-scripts test",
        "eject": "react-scripts eject"
    }
    
    # 添加browserslist配置
    package_data["browserslist"] = {
        "production": [
            ">0.2%",
            "not dead",
            "not op_mini all"
        ],
        "development": [
            "last 1 chrome version",
            "last 1 firefox version",
            "last 1 safari version"
        ]
    }
    
    # 写回文件
    with open(package_json_path, 'w', encoding='utf-8') as f:
        json.dump(package_data, f, indent=2, ensure_ascii=False)
    
    print("✓ package.json已更新")
    return True

def fix_env_file():
    """修复.env文件"""
    print_step("🔧 修复.env文件", "yellow")
    
    frontend_dir = Path("frontend")
    env_path = frontend_dir / ".env"
    
    env_content = """SKIP_PREFLIGHT_CHECK=true
GENERATE_SOURCEMAP=false
FAST_REFRESH=false
WDS_SOCKET_HOST=localhost
WDS_SOCKET_PORT=3000
CHOKIDAR_USEPOLLING=true
DISABLE_ESLINT_PLUGIN=true
"""
    
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print("✓ .env文件已更新")
    return True

def create_webpack_config():
    """创建webpack配置覆盖"""
    print_step("🔧 创建webpack配置", "yellow")
    
    frontend_dir = Path("frontend")
    
    # 创建craco.config.js来覆盖webpack配置
    craco_config = """const path = require('path');

module.exports = {
  webpack: {
    configure: (webpackConfig, { env, paths }) => {
      // 修复allowedHosts问题
      if (webpackConfig.devServer) {
        webpackConfig.devServer.allowedHosts = 'all';
        webpackConfig.devServer.host = 'localhost';
        webpackConfig.devServer.port = 3000;
        webpackConfig.devServer.client = {
          webSocketURL: {
            hostname: 'localhost',
            pathname: '/ws',
            port: 3000,
          },
        };
      }
      return webpackConfig;
    },
  },
  devServer: {
    allowedHosts: 'all',
    host: 'localhost',
    port: 3000,
  },
};
"""
    
    craco_path = frontend_dir / "craco.config.js"
    with open(craco_path, 'w', encoding='utf-8') as f:
        f.write(craco_config)
    
    print("✓ craco.config.js已创建")
    return True

def install_craco():
    """安装CRACO"""
    print_step("📦 安装CRACO", "cyan")
    
    frontend_dir = Path("frontend")
    
    # 安装CRACO
    if not run_command("npm install @craco/craco --save-dev", cwd=frontend_dir):
        print("❌ CRACO安装失败")
        return False
    
    # 更新package.json使用CRACO
    package_json_path = frontend_dir / "package.json"
    with open(package_json_path, 'r', encoding='utf-8') as f:
        package_data = json.load(f)
    
    package_data["scripts"]["start"] = "craco start"
    package_data["scripts"]["build"] = "craco build"
    package_data["scripts"]["test"] = "craco test"
    
    with open(package_json_path, 'w', encoding='utf-8') as f:
        json.dump(package_data, f, indent=2, ensure_ascii=False)
    
    print("✓ CRACO配置完成")
    return True

def clean_install():
    """清理并重新安装依赖"""
    print_step("🧹 清理并重新安装依赖", "yellow")
    
    frontend_dir = Path("frontend")
    
    # 删除node_modules和package-lock.json
    node_modules = frontend_dir / "node_modules"
    package_lock = frontend_dir / "package-lock.json"
    
    if node_modules.exists():
        print("🗑️  删除node_modules...")
        shutil.rmtree(node_modules)
    
    if package_lock.exists():
        package_lock.unlink()
        print("🗑️  删除package-lock.json...")
    
    # 清理npm缓存
    run_command("npm cache clean --force")
    
    # 重新安装依赖
    print("📦 重新安装依赖...")
    if not run_command("npm install", cwd=frontend_dir):
        print("❌ 依赖安装失败")
        return False
    
    print("✓ 依赖重新安装完成")
    return True

def test_start():
    """测试启动前端"""
    print_step("🧪 测试启动前端", "purple")
    
    frontend_dir = Path("frontend")
    
    # 设置环境变量
    env = os.environ.copy()
    env.update({
        "SKIP_PREFLIGHT_CHECK": "true",
        "GENERATE_SOURCEMAP": "false",
        "FAST_REFRESH": "false",
        "DISABLE_ESLINT_PLUGIN": "true"
    })
    
    try:
        print("🚀 测试启动前端服务...")
        process = subprocess.Popen(
            ["npm", "start"],
            cwd=frontend_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 等待启动
        time.sleep(15)
        
        if process.poll() is None:
            print("✓ 前端服务启动成功！")
            print("📍 前端地址: http://localhost:3000")
            
            # 询问是否继续运行
            try:
                response = input("\n前端服务正在运行，按Enter键停止测试...")
                process.terminate()
                process.wait()
                return True
            except KeyboardInterrupt:
                process.terminate()
                process.wait()
                return True
        else:
            stdout, stderr = process.communicate()
            print(f"❌ 前端启动失败")
            print(f"输出: {stdout}")
            print(f"错误: {stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 测试启动失败: {e}")
        return False

def create_final_start_script():
    """创建最终的启动脚本"""
    print_step("📝 创建启动脚本", "green")
    
    # Windows批处理文件
    bat_content = """@echo off
echo ========================================
echo   AI Crypto Frontend (Fixed)
echo ========================================
echo.

cd /d "%~dp0frontend"

echo Setting environment variables...
set SKIP_PREFLIGHT_CHECK=true
set GENERATE_SOURCEMAP=false
set FAST_REFRESH=false
set DISABLE_ESLINT_PLUGIN=true

echo.
echo Starting React development server...
echo Frontend: http://localhost:3000
echo Backend: http://localhost:8000
echo.

npm start

pause
"""
    
    with open("start_frontend_fixed.bat", "w", encoding="utf-8") as f:
        f.write(bat_content)
    
    # PowerShell脚本
    ps1_content = """Write-Host "AI Crypto Frontend (Fixed)" -ForegroundColor Green
Write-Host ("=" * 50) -ForegroundColor Blue

Set-Location frontend

$env:SKIP_PREFLIGHT_CHECK = "true"
$env:GENERATE_SOURCEMAP = "false"
$env:FAST_REFRESH = "false"
$env:DISABLE_ESLINT_PLUGIN = "true"

Write-Host "Environment variables set" -ForegroundColor Green
Write-Host "Starting React server..." -ForegroundColor Cyan
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Yellow
Write-Host "Backend: http://localhost:8000" -ForegroundColor Yellow

npm start
"""
    
    with open("start_frontend_fixed.ps1", "w", encoding="utf-8") as f:
        f.write(ps1_content)
    
    print("✓ 启动脚本已创建")
    print("  - start_frontend_fixed.bat")
    print("  - start_frontend_fixed.ps1")
    
    return True

def main():
    """主函数"""
    print("🔧 前端启动问题自动修复工具")
    print("=" * 60)
    
    # 检查环境
    if not Path("frontend").exists():
        print("❌ frontend目录不存在")
        sys.exit(1)
    
    steps = [
        ("修复package.json", fix_package_json),
        ("修复.env文件", fix_env_file),
        ("清理并重新安装依赖", clean_install),
        ("创建webpack配置", create_webpack_config),
        ("安装CRACO", install_craco),
        ("创建启动脚本", create_final_start_script),
        ("测试启动", test_start),
    ]
    
    failed_steps = []
    
    for step_name, step_func in steps:
        try:
            if not step_func():
                failed_steps.append(step_name)
                if step_name == "测试启动":
                    # 测试失败不算致命错误
                    continue
        except Exception as e:
            print(f"❌ {step_name} 执行异常: {e}")
            failed_steps.append(step_name)
    
    # 输出结果
    print("\n" + "=" * 60)
    print("📋 修复结果汇总")
    print("=" * 60)
    
    if failed_steps:
        print("⚠️ 以下步骤需要注意:")
        for step in failed_steps:
            print(f"   - {step}")
    
    print("\n🎉 修复完成！")
    print("\n📖 启动方法:")
    print("1. 双击: start_frontend_fixed.bat")
    print("2. PowerShell: .\\start_frontend_fixed.ps1")
    print("3. 手动: cd frontend && npm start")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 修复被用户中断")
    except Exception as e:
        print(f"\n❌ 修复失败: {e}")
        sys.exit(1)
