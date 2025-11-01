"""系统级配置 - PoA Demo 专用"""

from __future__ import annotations

import copy
import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, Optional


logger = logging.getLogger(__name__)

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
BACKEND_ROOT = Path(__file__).parent

# 资产目录路径
ASSETS_DIR = BACKEND_ROOT / "assets"
MODEL_PACKAGE_DIR = ASSETS_DIR / "model_package"
DATA_DIR = ASSETS_DIR / "data"

# ===== PoA 区块链配置（唯一激活模式） =====

BLOCKCHAIN_CONFIG: Dict[str, Any] = {
    "name": "Proof of Authority (Demo)",
    "mode": "poa",
    "chain_id": 20001,
    "network_id": 20001,
    "rpc_url": "http://127.0.0.1:8545",
    "data_dir": str(PROJECT_ROOT / ".poa_chain"),
    "keystore_dir": "/home/devlechain/ChainData/20000_20000_ethash_0/keystore",
    "expected_block_time": "1s",
    "description": "Fixed-period Clique chain optimised for real-time demo flows",
    "contract_config_path": str(ASSETS_DIR / "deployed_contract.json"),
    "password": "devlechain",
    "accounts": {
        "manager_0": "0x3BDEb75351468e39d60B32aF39df6f030C42E14f",
        "manager_1": "0x96BDDef5e941Cf35B7f63193b53047ad40e9C568",
        "manager_2": "0xa11B3Fdaad0E670fB5956456554FAB7Af850E701",
        "treasury": "0xaA09248D29717Ed9be4114909dc3F1A0b8c71F4F",
        "operator_0": "0x33273Cfda8d30889032c541c0Ccf1f50410008Af",
        "operator_1": "0x76A929caE1551BA35d3eEB44fA6ff6A84A5334f3",
        # 隐藏节点池
        "operator_2": "0x0e2985cab47a5fe4200bfa63daf25c5eec17e918",
        "operator_3": "0xd23974858ea0f7b33bb0e1288c6cc3cf6858a0b5",
        "operator_4": "0x4d531c0209e7fdbb3868a32635ed8afbcadc6cb6",
        "operator_5": "0x7facb7e5d56b29806601cf2f697a9f6df193b1bc",
    },
}


@lru_cache(maxsize=1)
def get_blockchain_config() -> Dict[str, Any]:
    """获取 PoA 区块链配置副本"""

    return copy.deepcopy(BLOCKCHAIN_CONFIG)


def _contract_config_path() -> Path:
    return Path(BLOCKCHAIN_CONFIG["contract_config_path"]).resolve()


@lru_cache(maxsize=1)
def get_deployed_contract() -> Dict[str, Any]:
    """加载部署好的多签合约配置"""

    path = _contract_config_path()
    if not path.exists():
        raise FileNotFoundError(
            f"Contract config not found at {path}. "
            "Run scripts/bootstrap_poa_demo.py to deploy the PoA contract."
        )

    with path.open("r", encoding="utf-8") as file:
        contract_info = json.load(file)

    contract_address = contract_info.get("address")
    if not contract_address or contract_address.startswith("REPLACE"):
        raise ValueError(
            f"Invalid contract address in {path}: {contract_address}. "
            "Re-run the bootstrap script to refresh contract metadata."
        )

    contract_info.setdefault("mode", BLOCKCHAIN_CONFIG["mode"])
    contract_info.setdefault("chain_id", BLOCKCHAIN_CONFIG["chain_id"])
    return contract_info


@lru_cache(maxsize=1)
def get_devlechain_config() -> Dict[str, Any]:
    """返回完整的区块链 + 账户配置"""

    config = get_blockchain_config()
    config["accounts"] = copy.deepcopy(BLOCKCHAIN_CONFIG["accounts"])
    try:
        config["deployed_contract"] = get_deployed_contract()
    except FileNotFoundError as exc:
        logger.warning("PoA contract not deployed yet: %s", exc)
        config["deployed_contract"] = None
    except ValueError as exc:
        logger.warning("PoA contract configuration invalid: %s", exc)
        config["deployed_contract"] = None

    return config


def refresh_blockchain_config_cache() -> None:
    """清空缓存（主要用于测试/脚本）"""

    get_blockchain_config.cache_clear()
    get_deployed_contract.cache_clear()
    get_devlechain_config.cache_clear()


class _ConfigProxy:
    """向后兼容的只读配置代理"""

    def _data(self) -> Dict[str, Any]:
        return get_devlechain_config()

    def __getitem__(self, key: str) -> Any:  # type: ignore[override]
        return self._data()[key]

    def __contains__(self, item: object) -> bool:
        return item in self._data()

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        return self._data().get(key, default)

    def keys(self) -> Iterable[str]:
        return self._data().keys()

    def values(self) -> Iterable[Any]:
        return self._data().values()

    def items(self) -> Iterable[Any]:
        return self._data().items()

    def __iter__(self) -> Iterator[str]:
        return iter(self._data())

    def __len__(self) -> int:
        return len(self._data())

    def __repr__(self) -> str:
        return f"ConfigProxy({self._data()!r})"

    def __setitem__(self, key: str, value: Any) -> None:  # pragma: no cover
        raise TypeError("ConfigProxy is read-only")


# Legacy aliases retained for backwards compatibility
DEVLECHAIN_CONFIG = _ConfigProxy()
GANACHE_CONFIG = DEVLECHAIN_CONFIG  # historical alias used in older scripts

# 隐藏节点配置 - 默认隐藏的operator账户
HIDDEN_NODES = ["operator_2", "operator_3", "operator_4", "operator_5"]

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
