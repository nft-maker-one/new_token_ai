"""
环境变量加载器
确保在整个应用中正确加载.env文件
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)

def load_environment_variables():
    """
    加载环境变量，支持多种.env文件位置
    """
    # 获取当前文件的绝对路径，然后找到项目根目录
    current_file = Path(__file__).resolve()
    logger.info(f"current file = {current_file}")
    project_root = current_file.parent.parent.parent  # backend/utils/env_loader.py -> project_root

    # 可能的.env文件位置（按优先级排序）
    possible_env_paths = [
        project_root / ".env",  # 项目根目录（最优先）
        Path(".env"),  # 当前工作目录
        Path("../.env"),  # 上级目录
        Path("../../.env"),  # 上上级目录
    ]

    env_loaded = False

    logger.info(f"项目根目录: {project_root}")
    logger.info(f"当前工作目录: {Path.cwd()}")

    for env_path in possible_env_paths:
        abs_path = env_path.resolve()
        logger.info(f"尝试加载环境变量文件: {abs_path}")
        if env_path.exists():
            load_dotenv(env_path)
            env_loaded = True
            break
        else:
            logger.info(f"❌ 文件不存在: {abs_path}")
    
    if not env_loaded:
        logger.warning("⚠️ 未找到.env文件，将使用系统环境变量") 
    # 验证关键环境变量
    validate_environment_variables()
    
    return env_loaded

def validate_environment_variables():
    """
    验证关键环境变量是否正确设置
    """
    required_vars = {
        "GEMINI_API_KEY": "Gemini AI API密钥"
    }
    
    optional_vars = {
        "REDIS_URL": "Redis连接URL",
        "GOOGLE_SEARCH_API_KEY": "Google搜索API密钥",
        "GOOGLE_SEARCH_ENGINE_ID": "Google搜索引擎ID"
    }
    
    # 检查必需的环境变量
    missing_required = []
    for var_name, description in required_vars.items():
        value = os.getenv(var_name)
        if not value or value == f"your_{var_name.lower()}_here":
            missing_required.append(f"{var_name} ({description})")
            logger.error(f"❌ 缺少必需的环境变量: {var_name}")
            logger.error(f"   当前值: {value}")
        else:
            # 只显示前几个字符，保护敏感信息
            masked_value = value[:8] + "..." if len(value) > 8 else value
            logger.info(f"✅ {var_name}: {masked_value}")
    
    # 检查可选的环境变量
    for var_name, description in optional_vars.items():
        value = os.getenv(var_name)
        if value and value != f"your_{var_name.lower()}_here":
            masked_value = value[:8] + "..." if len(value) > 8 else value
            logger.info(f"✅ {var_name}: {masked_value}")
        else:
            logger.info(f"ℹ️ {var_name}: 未设置 ({description})")
    
    if missing_required:
        logger.error("❌ 以下必需的环境变量未正确设置:")
        for var in missing_required:
            logger.error(f"   - {var}")
        logger.error("请检查.env文件并设置正确的值")
        return False
    
    logger.info("✅ 所有必需的环境变量都已正确设置")
    return True

def get_env_var(var_name: str, default: str = None, required: bool = False) -> str:
    """
    安全地获取环境变量
    
    Args:
        var_name: 环境变量名
        default: 默认值
        required: 是否为必需变量
    
    Returns:
        环境变量值
    
    Raises:
        ValueError: 当required=True且变量未设置时
    """
    value = os.getenv(var_name, default)
    
    if required and (not value or value == f"your_{var_name.lower()}_here"):
        raise ValueError(f"必需的环境变量 {var_name} 未设置或使用默认值")
    
    return value

# 在模块导入时自动加载环境变量
load_environment_variables()
