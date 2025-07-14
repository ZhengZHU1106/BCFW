"""
Web3连接和账户管理模块
"""

from web3 import Web3
from eth_account import Account
from typing import Dict, List, Optional
import logging
from ..config import GANACHE_CONFIG, INCENTIVE_CONFIG

logger = logging.getLogger(__name__)

class Web3Manager:
    """Web3连接和账户管理器"""
    
    def __init__(self):
        self.w3: Optional[Web3] = None
        self.accounts: Dict[str, str] = {}  # role -> address
        self.private_keys: Dict[str, str] = {}  # role -> private_key
        self._initialize_connection()
        self._setup_accounts()
    
    def _initialize_connection(self):
        """初始化Web3连接"""
        try:
            self.w3 = Web3(Web3.HTTPProvider(GANACHE_CONFIG['rpc_url']))
            
            if not self.w3.is_connected():
                raise ConnectionError(f"无法连接到Ganache: {GANACHE_CONFIG['rpc_url']}")
            
            logger.info(f"✅ Web3连接成功: {GANACHE_CONFIG['rpc_url']}")
            logger.info(f"🔗 网络ID: {self.w3.eth.chain_id}")
            logger.info(f"📦 当前区块: {self.w3.eth.block_number}")
            
        except Exception as e:
            logger.error(f"❌ Web3连接失败: {e}")
            raise
    
    def _setup_accounts(self):
        """设置确定性账户"""
        try:
            # 启用HD钱包功能
            Account.enable_unaudited_hdwallet_features()
            
            mnemonic = GANACHE_CONFIG['mnemonic']
            account_mapping = GANACHE_CONFIG['accounts']
            
            # 为每个角色生成确定性账户
            for role, index in account_mapping.items():
                account = Account.from_mnemonic(
                    mnemonic, 
                    account_path=f"m/44'/60'/0'/0/{index}"
                )
                
                self.accounts[role] = account.address
                self.private_keys[role] = account.key.hex()
                
                # 验证余额
                balance = self.w3.eth.get_balance(account.address)
                balance_eth = self.w3.from_wei(balance, 'ether')
                
                logger.info(f"👛 {role}: {account.address} (余额: {balance_eth} ETH)")
            
            logger.info("✅ 账户设置完成")
            
        except Exception as e:
            logger.error(f"❌ 账户设置失败: {e}")
            raise
    
    def get_account_info(self, role: str) -> Dict:
        """获取账户信息"""
        if role not in self.accounts:
            raise ValueError(f"未知角色: {role}")
        
        address = self.accounts[role]
        balance = self.w3.eth.get_balance(address)
        
        return {
            "role": role,
            "address": address,
            "balance_wei": balance,
            "balance_eth": float(self.w3.from_wei(balance, 'ether')),
            "nonce": self.w3.eth.get_transaction_count(address)
        }
    
    def get_all_accounts_info(self) -> List[Dict]:
        """获取所有账户信息"""
        accounts_info = []
        for role in self.accounts.keys():
            accounts_info.append(self.get_account_info(role))
        return accounts_info
    
    def get_network_info(self) -> Dict:
        """获取网络信息"""
        return {
            "chain_id": self.w3.eth.chain_id,
            "block_number": self.w3.eth.block_number,
            "gas_price": self.w3.eth.gas_price,
            "is_connected": self.w3.is_connected(),
            "rpc_url": GANACHE_CONFIG['rpc_url']
        }
    
    def send_reward(self, from_role: str, to_role: str, amount_eth: float = None) -> Dict:
        """发送奖励ETH"""
        if amount_eth is None:
            amount_eth = INCENTIVE_CONFIG['proposal_reward']
        
        try:
            from_address = self.accounts[from_role]
            to_address = self.accounts[to_role]
            from_private_key = self.private_keys[from_role]
            
            # 构建交易
            amount_wei = self.w3.to_wei(amount_eth, 'ether')
            nonce = self.w3.eth.get_transaction_count(from_address)
            
            transaction = {
                'to': to_address,
                'value': amount_wei,
                'gas': 21000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': nonce,
                'chainId': self.w3.eth.chain_id
            }
            
            # 签名并发送交易
            signed_txn = self.w3.eth.account.sign_transaction(transaction, from_private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # 等待交易确认
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            logger.info(f"💰 奖励发送成功: {amount_eth} ETH from {from_role} to {to_role}")
            logger.info(f"📝 交易哈希: {tx_hash.hex()}")
            
            return {
                "success": True,
                "tx_hash": tx_hash.hex(),
                "from_role": from_role,
                "to_role": to_role,
                "amount_eth": amount_eth,
                "gas_used": receipt.gasUsed,
                "block_number": receipt.blockNumber
            }
            
        except Exception as e:
            logger.error(f"❌ 奖励发送失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "from_role": from_role,
                "to_role": to_role,
                "amount_eth": amount_eth
            }
    
    def estimate_gas(self, transaction: Dict) -> int:
        """估算Gas费用"""
        return self.w3.eth.estimate_gas(transaction)
    
    def is_connected(self) -> bool:
        """检查连接状态"""
        return self.w3 is not None and self.w3.is_connected()

# 全局Web3管理器实例
web3_manager = None

def get_web3_manager() -> Web3Manager:
    """获取Web3管理器单例"""
    global web3_manager
    if web3_manager is None:
        web3_manager = Web3Manager()
    return web3_manager

def init_web3_manager():
    """初始化Web3管理器"""
    global web3_manager
    web3_manager = Web3Manager()
    return web3_manager