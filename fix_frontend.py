#!/usr/bin/env python3
"""
修复前端启动问题的脚本
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def print_step(step):
    print(f"\n🔧 {step}")
    print("-" * 50)

def run_command(command, cwd=None):
    """运行命令并返回结果"""
    print(f"💻 执行: {command}")
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            cwd=cwd, 
            check=True,
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 命令执行失败: {e}")
        if e.stderr:
            print(f"错误信息: {e.stderr}")
        return False

def check_node_version():
    """检查Node.js版本"""
    print_step("检查Node.js版本")
    
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✓ Node.js版本: {version}")
            
            # 检查版本是否过高
            version_num = version.replace('v', '').split('.')[0]
            if int(version_num) >= 17:
                print("⚠️  检测到Node.js 17+版本，可能需要特殊配置")
                return "high_version"
            return True
        else:
            print("❌ Node.js未安装")
            return False
    except FileNotFoundError:
        print("❌ Node.js未安装")
        return False

def clear_cache():
    """清理缓存"""
    print_step("清理缓存和node_modules")
    
    frontend_dir = Path("frontend")
    
    # 删除node_modules
    node_modules = frontend_dir / "node_modules"
    if node_modules.exists():
        print("🗑️  删除node_modules...")
        import shutil
        shutil.rmtree(node_modules)
        print("✓ node_modules已删除")
    
    # 删除package-lock.json
    package_lock = frontend_dir / "package-lock.json"
    if package_lock.exists():
        package_lock.unlink()
        print("✓ package-lock.json已删除")
    
    # 清理npm缓存
    print("🧹 清理npm缓存...")
    run_command("npm cache clean --force")
    
    return True

def update_package_json():
    """更新package.json配置"""
    print_step("更新package.json配置")
    
    frontend_dir = Path("frontend")
    package_json_path = frontend_dir / "package.json"
    
    if not package_json_path.exists():
        print("❌ package.json不存在")
        return False
    
    # 读取现有配置
    with open(package_json_path, 'r', encoding='utf-8') as f:
        package_data = json.load(f)
    
    # 更新react-scripts版本
    package_data["dependencies"]["react-scripts"] = "5.0.1"
    
    # 添加resolutions来解决依赖冲突
    package_data["resolutions"] = {
        "webpack": "5.74.0"
    }
    
    # 更新scripts
    package_data["scripts"]["start"] = "set SKIP_PREFLIGHT_CHECK=true && react-scripts start"
    
    # 写回文件
    with open(package_json_path, 'w', encoding='utf-8') as f:
        json.dump(package_data, f, indent=2, ensure_ascii=False)
    
    print("✓ package.json已更新")
    return True

def create_env_file():
    """创建.env文件"""
    print_step("创建前端.env文件")
    
    frontend_dir = Path("frontend")
    env_path = frontend_dir / ".env"
    
    env_content = """GENERATE_SOURCEMAP=false
SKIP_PREFLIGHT_CHECK=true
FAST_REFRESH=false
WDS_SOCKET_HOST=localhost
WDS_SOCKET_PORT=3000
CHOKIDAR_USEPOLLING=true
"""
    
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print("✓ .env文件已创建")
    return True

def install_dependencies():
    """重新安装依赖"""
    print_step("重新安装依赖")
    
    frontend_dir = Path("frontend")
    
    # 使用npm install
    if not run_command("npm install", cwd=frontend_dir):
        print("❌ npm install失败，尝试使用yarn...")
        if not run_command("yarn install", cwd=frontend_dir):
            return False
    
    print("✓ 依赖安装完成")
    return True

def create_start_script():
    """创建启动脚本"""
    print_step("创建启动脚本")
    
    # Windows批处理文件
    start_frontend_bat = """@echo off
echo Starting React Frontend...
cd frontend
set SKIP_PREFLIGHT_CHECK=true
set GENERATE_SOURCEMAP=false
set FAST_REFRESH=false
npm start
"""
    
    with open("start_frontend.bat", "w", encoding="utf-8") as f:
        f.write(start_frontend_bat)
    
    # PowerShell脚本
    start_frontend_ps1 = """Write-Host "Starting React Frontend..." -ForegroundColor Green
Set-Location frontend
$env:SKIP_PREFLIGHT_CHECK = "true"
$env:GENERATE_SOURCEMAP = "false"
$env:FAST_REFRESH = "false"
npm start
"""
    
    with open("start_frontend.ps1", "w", encoding="utf-8") as f:
        f.write(start_frontend_ps1)
    
    print("✓ 启动脚本已创建")
    print("  - start_frontend.bat (命令提示符)")
    print("  - start_frontend.ps1 (PowerShell)")
    
    return True

def test_start():
    """测试启动"""
    print_step("测试启动")
    
    print("⚠️  即将测试启动前端服务...")
    print("如果出现错误，请按Ctrl+C停止")
    
    response = input("是否继续测试? (y/N): ")
    if response.lower() != 'y':
        print("跳过测试")
        return True
    
    frontend_dir = Path("frontend")
    
    # 设置环境变量
    env = os.environ.copy()
    env["SKIP_PREFLIGHT_CHECK"] = "true"
    env["GENERATE_SOURCEMAP"] = "false"
    env["FAST_REFRESH"] = "false"
    
    try:
        print("🚀 启动React开发服务器...")
        process = subprocess.Popen(
            ["npm", "start"],
            cwd=frontend_dir,
            env=env
        )
        
        # 等待几秒钟
        import time
        time.sleep(10)
        
        if process.poll() is None:
            print("✓ 前端服务启动成功！")
            print("请在浏览器中访问: http://localhost:3000")
            
            input("按Enter键停止服务...")
            process.terminate()
            return True
        else:
            print("❌ 前端服务启动失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试启动失败: {e}")
        return False

def main():
    """主函数"""
    print("🔧 AI Crypto Frontend 修复工具")
    print("=" * 60)
    
    # 检查当前目录
    if not Path("frontend").exists():
        print("❌ 请在项目根目录运行此脚本")
        sys.exit(1)
    
    steps = [
        ("检查Node.js版本", check_node_version),
        ("清理缓存", clear_cache),
        ("更新package.json", update_package_json),
        ("创建.env文件", create_env_file),
        ("重新安装依赖", install_dependencies),
        ("创建启动脚本", create_start_script),
    ]
    
    failed_steps = []
    
    for step_name, step_func in steps:
        try:
            result = step_func()
            if not result:
                failed_steps.append(step_name)
        except Exception as e:
            print(f"❌ {step_name} 执行异常: {e}")
            failed_steps.append(step_name)
    
    # 输出结果
    print("\n" + "=" * 60)
    print("📋 修复结果汇总")
    print("=" * 60)
    
    if failed_steps:
        print("❌ 以下步骤失败:")
        for step in failed_steps:
            print(f"   - {step}")
        print("\n请检查错误信息并手动修复")
    else:
        print("🎉 修复完成！")
        print("\n📖 启动方法:")
        print("1. 使用批处理文件: start_frontend.bat")
        print("2. 使用PowerShell: .\\start_frontend.ps1")
        print("3. 手动启动:")
        print("   cd frontend")
        print("   set SKIP_PREFLIGHT_CHECK=true")
        print("   npm start")
        
        # 询问是否测试启动
        test_start()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 修复被用户中断")
    except Exception as e:
        print(f"\n❌ 修复失败: {e}")
        sys.exit(1)
