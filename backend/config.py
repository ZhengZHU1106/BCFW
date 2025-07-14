"""
配置文件 - 系统配置和常量
"""
import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
BACKEND_ROOT = Path(__file__).parent

# 资产目录路径
ASSETS_DIR = BACKEND_ROOT / "assets"
MODEL_PACKAGE_DIR = ASSETS_DIR / "model_package"
DATA_DIR = ASSETS_DIR / "data"

# 区块链配置
GANACHE_CONFIG = {
    "mnemonic": "bulk tonight audit hover toddler orange boost twenty biology flower govern soldier",
    "rpc_url": "http://127.0.0.1:8545",
    "block_time": 5,
    "accounts": {
        "manager_0": 0,  # Manager 账户索引
        "manager_1": 1,
        "manager_2": 2,
        "treasury": 3,   # 系统金库账户索引
    }
}

# AI 模型配置
AI_MODEL_CONFIG = {
    "model_file": MODEL_PACKAGE_DIR / "model.pth",
    "scaler_file": MODEL_PACKAGE_DIR / "scaler.pkl",
    "feature_selector_file": MODEL_PACKAGE_DIR / "feature_selector.pkl",
    "label_encoder_file": MODEL_PACKAGE_DIR / "label_encoder.pkl",
    "model_info_file": MODEL_PACKAGE_DIR / "model_info.json",
    "selected_features_file": MODEL_PACKAGE_DIR / "selected_features.json",
    "inference_data_file": DATA_DIR / "inference_data.pt",
}

# 威胁检测置信度阈值
THREAT_THRESHOLDS = {
    "high_confidence": 0.90,      # 自动响应
    "medium_high": 0.80,          # 自动发起提案
    "medium_low": 0.70,           # 手动决策告警
    "low_confidence": 0.0,        # 静默记录
}

# 激励系统配置
INCENTIVE_CONFIG = {
    "proposal_reward": 0.01,  # ETH，给最终签名者的奖励
}

# 数据库配置
DATABASE_CONFIG = {
    "url": f"sqlite:///{BACKEND_ROOT}/security_platform.db",
    "echo": False,  # 生产环境设为 False
}