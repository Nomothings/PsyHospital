"""
日志配置模块
"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler


def setup_logging(log_dir: Path, level: str = "INFO") -> None:
    """配置日志系统

    Args:
        log_dir: 日志目录
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "app.log"

    # 日志格式
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 应用命名日志器（避免污染全局根日志器）
    app_logger = logging.getLogger("mental_hospital")
    app_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # 清除已有处理器
    app_logger.handlers.clear()
    app_logger.propagate = False

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    app_logger.addHandler(console_handler)

    # 文件处理器（轮转，最大 10MB，保留 5 个备份）
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    app_logger.addHandler(file_handler)

    app_logger.info(f"日志系统已初始化，日志文件: {log_file}")
