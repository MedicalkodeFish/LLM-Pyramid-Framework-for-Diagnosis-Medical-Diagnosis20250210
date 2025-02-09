import os
import logging
from model_config import backBone

def setup_logger(case_num):
    """为每个病例设置独立的日志记录器
    Set up an independent logger for each case
    """
    # 创建该病例的日志目录
    # Create log directory for this case
    log_dir = os.path.join(f"\\logs\\{backBone}")
    os.makedirs(log_dir, exist_ok=True)

    # 创建该病例的日志文件
    # Create log file for this case
    log_file = os.path.join(log_dir, f"case_{case_num}.log")

    # 创建新的日志处理器
    # Create new log handlers
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    console_handler = logging.StreamHandler()

    # 设置日志格式
    # Set log format
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # 获取根日志记录器并重新配置
    # Get root logger and reconfigure
    logger = logging.getLogger()

    # 清除现有的处理器
    # Clear existing handlers
    logger.handlers.clear()

    # 添加新的处理器
    # Add new handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.setLevel(logging.INFO)

    return logger
