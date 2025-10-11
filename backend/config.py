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

# DevLeChain 私有链配置
DEVLECHAIN_CONFIG = {
    "rpc_url": "http://127.0.0.1:8545",
    "chain_id": 20000,
    "network_id": 20000,
    "keystore_dir": "/home/devlechain/ChainData/20000_20000_ethash_0/keystore",
    "password": "devlechain",
    "data_dir": "/home/devlechain/ChainData/20000_20000_ethash_0",

    # DevLeChain 预配置账户(从 genesis.json + 新创建的operator账户)
    "accounts": {
        "manager_0": "0x3BDEb75351468e39d60B32aF39df6f030C42E14f",
        "manager_1": "0x96BDDef5e941Cf35B7f63193b53047ad40e9C568",
        "manager_2": "0xa11B3Fdaad0E670fB5956456554FAB7Af850E701",
        "treasury": "0xaA09248D29717Ed9be4114909dc3F1A0b8c71F4F",
        "operator_0": "0x33273Cfda8d30889032c541c0Ccf1f50410008Af",
        "operator_1": "0x76A929caE1551BA35d3eEB44fA6ff6A84A5334f3",
        # 账户池 - 额外的operator账户（默认隐藏）
        "operator_2": "0x0e2985cab47a5fe4200bfa63daf25c5eec17e918",
        "operator_3": "0xd23974858ea0f7b33bb0e1288c6cc3cf6858a0b5",
        "operator_4": "0x4d531c0209e7fdbb3868a32635ed8afbcadc6cb6",
        "operator_5": "0x7facb7e5d56b29806601cf2f697a9f6df193b1bc",
    }
}

# 隐藏节点配置 - 默认隐藏的operator账户
HIDDEN_NODES = ["operator_2", "operator_3", "operator_4", "operator_5"]

# 向后兼容：使用DEVLECHAIN_CONFIG作为主配置
GANACHE_CONFIG = DEVLECHAIN_CONFIG  # 使用DevLeChain配置

# AI 模型配置
AI_MODEL_CONFIG = {
    # 使用正确的打包模型目录
    "model_package_dir": MODEL_PACKAGE_DIR / "model",
    "model_file": MODEL_PACKAGE_DIR / "model" / "model.pth",
    "scaler_file": MODEL_PACKAGE_DIR / "model" / "scaler.pkl", 
    "label_encoder_file": MODEL_PACKAGE_DIR / "model" / "label_encoder.pkl",
    "model_info_file": MODEL_PACKAGE_DIR / "model" / "model_info.json",
    "selected_features_file": MODEL_PACKAGE_DIR / "model" / "selected_features.json",
    "inference_data_file": DATA_DIR / "inference_data_7class.pt",
    
    # 使用预处理数据 - 现在有了正确的quantile阈值，效果完美(100%准确率)
    "use_original_data": False,
    "original_data_dir": BACKEND_ROOT.parent / "original_data",
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

# 网络可视化配置
NETWORK_CONFIG = {
    "node_types": {
        "manager": {"color": "#007bff", "size": 40, "role": "Manager"},
        "treasury": {"color": "#28a745", "size": 50, "role": "Treasury"}, 
        "operator": {"color": "#fd7e14", "size": 35, "role": "Operator"}
    },
    "layout_types": ["star", "grid", "circle", "random"],
    "default_layout": "star",
    "animation_duration": 1000,  # 毫秒
}