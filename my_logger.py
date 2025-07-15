import os
import sys
import time
import logging
from logging.handlers import RotatingFileHandler

def get_caller_info():
    """
    获取调用者的文件路径和行号，跳过日志文件本身的帧
    """
    frame = sys._getframe()
    # 跳过当前帧和logging模块的帧
    while frame:
        filename = frame.f_globals.get('__file__', None)
        if filename and 'my_logger.py' not in filename and 'utils.py' not in filename:
            return f"{os.path.basename(filename)}:{frame.f_lineno}"
        frame = frame.f_back
    return "unknown:0"

class SizeRotatingHandler(RotatingFileHandler):
    """
    自定义RotatingFileHandler，限制文件数量和大小
    """
    def __init__(self, filename, max_bytes=16*1024*1024, backup_count=5):
        super().__init__(filename, maxBytes=max_bytes, backupCount=backup_count,encoding='utf-8')
        self.max_bytes = max_bytes
        self.backup_count = backup_count

    def doRollover(self):
        """
        覆盖最旧的日志文件
        """
        if self.backup_count > 0:
            for i in range(self.backup_count - 1, 0, -1):
                sfn = f"{self.baseFilename}.{i}"
                dfn = f"{self.baseFilename}.{i+1}"
                if os.path.exists(sfn):
                    if os.path.exists(dfn):
                        os.remove(dfn)
                    os.rename(sfn, dfn)
            dfn = f"{self.baseFilename}.1"
            if os.path.exists(dfn):
                os.remove(dfn)
            self.rotate(self.baseFilename, dfn)

# 确保logs目录存在
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

# 创建logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 以秒级时间戳命名日志文件
timestamp = time.strftime("%Y%m%d")
log_filename = os.path.join(log_dir, f"{timestamp}.log")

# 添加文件handler
handler = SizeRotatingHandler(log_filename, max_bytes=16*1024*1024, backup_count=5)
formatter = logging.Formatter('[%(asctime)s.%(msecs)03d] %(filename)s:%(lineno)d - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
handler.setFormatter(formatter)
logger.addHandler(handler)

# 控制台handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

def log(message, level=logging.INFO):
    """
    记录日志，包含调用者信息
    :param message: 日志消息
    :param level: 日志级别，默认为INFO
    """
    caller_info = get_caller_info()
    logger.log(level, f"{caller_info} - {message}")

# 暴露logger对象以便直接调用不同级别的方法
__all__ = ['logger', 'log']