"""
Web3连接和账户管理模块
"""

from web3 import Web3
from eth_account import Account
from typing import Dict, List, Optional
import logging
import json
import os
from ..config import GANACHE_CONFIG, INCENTIVE_CONFIG

logger = logging.getLogger(__name__)

class Web3Manager:
    """Web3连接和账户管理器"""
    
    def __init__(self):
        self.w3: Optional[Web3] = None
        self.accounts: Dict[str, str] = {}  # role -> address
        self.private_keys: Dict[str, str] = {}  # role -> private_key
        self.multisig_contract = None
        self._initialize_connection()
        self._setup_accounts()
        self._initialize_multisig_contract()
    
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
        """从DevLeChain keystore加载账户"""
        try:
            keystore_dir = GANACHE_CONFIG.get('keystore_dir')
            password = GANACHE_CONFIG.get('password')
            accounts_config = GANACHE_CONFIG['accounts']

            # 检查是否是新的DevLeChain配置(地址而非索引)
            first_account_value = list(accounts_config.values())[0]
            is_address_config = isinstance(first_account_value, str) and first_account_value.startswith('0x')

            if is_address_config and keystore_dir and password:
                # DevLeChain模式：从keystore加载
                logger.info("🔑 从DevLeChain keystore加载账户...")
                self._load_from_keystore(keystore_dir, password, accounts_config)
            else:
                # Ganache模式：使用助记词(向后兼容)
                logger.info("🔑 使用助记词派生账户(Ganache模式)...")
                self._load_from_mnemonic()

            logger.info("✅ 账户设置完成")

        except Exception as e:
            logger.error(f"❌ 账户设置失败: {e}")
            raise

    def _load_from_keystore(self, keystore_dir: str, password: str, accounts_config: Dict):
        """从keystore文件加载账户"""
        import os
        import glob

        for role, address in accounts_config.items():
            try:
                # 查找对应的keystore文件(不区分大小写)
                pattern = os.path.join(keystore_dir, f"*--{address[2:].lower()}")
                keyfiles = glob.glob(pattern)

                if not keyfiles:
                    logger.warning(f"⚠️  未找到{role}的keystore文件: {address}")
                    continue

                keyfile_path = keyfiles[0]

                # 读取并解密keystore
                with open(keyfile_path, 'r') as f:
                    encrypted_key = json.load(f)

                private_key = Account.decrypt(encrypted_key, password)
                account = Account.from_key(private_key)

                # 验证地址匹配
                if account.address.lower() != address.lower():
                    logger.error(f"❌ 地址不匹配: {role} - 期望{address}, 实际{account.address}")
                    continue

                self.accounts[role] = account.address
                self.private_keys[role] = private_key.hex()

                # 验证余额
                balance = self.w3.eth.get_balance(account.address)
                balance_eth = self.w3.from_wei(balance, 'ether')

                logger.info(f"👛 {role}: {account.address} (余额: {balance_eth} ETH)")

            except Exception as e:
                logger.error(f"❌ 加载{role}账户失败: {e}")
                raise

    def _load_from_mnemonic(self):
        """使用助记词派生账户(Ganache模式-向后兼容)"""
        Account.enable_unaudited_hdwallet_features()

        mnemonic = GANACHE_CONFIG.get('mnemonic', '')
        account_mapping = GANACHE_CONFIG['accounts']

        for role, index in account_mapping.items():
            account = Account.from_mnemonic(
                mnemonic,
                account_path=f"m/44'/60'/0'/0/{index}"
            )

            self.accounts[role] = account.address
            self.private_keys[role] = account.key.hex()

            balance = self.w3.eth.get_balance(account.address)
            balance_eth = self.w3.from_wei(balance, 'ether')

            logger.info(f"👛 {role}: {account.address} (余额: {balance_eth} ETH)")
    
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
    
    def get_account_addresses(self) -> Dict[str, str]:
        """获取所有账户地址映射"""
        return self.accounts.copy()
    
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
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            
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
    
    def _initialize_multisig_contract(self):
        """初始化多签名合约集成"""
        try:
            # 导入多签名合约集成模块
            from .multisig_contract import MultiSigContract
            self.multisig_contract = MultiSigContract(self)

            # 加载合约配置（注意：MultiSigContract已经在内部加载了deployed_contract.json）
            config_path = os.path.join(os.path.dirname(__file__), '../assets/deployed_contract.json')
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    self.multisig_config = json.load(f)
                logger.info(f"✅ MultiSig合约集成成功: {self.multisig_config['address']}")
            else:
                logger.warning(f"⚠️ MultiSig合约配置文件不存在: {config_path}")
                self.multisig_config = None

        except Exception as e:
            logger.error(f"❌ MultiSig合约初始化失败: {e}")
            self.multisig_contract = None
            self.multisig_config = None
    
    # ================================
    # MultiSig Contract Methods
    # ================================
    
    def create_multisig_proposal(self, target_role: str, amount_eth: float, data: str = "0x", creator_role: str = None) -> Dict:
        """创建多签名提案 - 现在支持角色验证"""
        if not self.multisig_contract:
            return {
                "success": False,
                "error": "MultiSig contract not initialized"
            }
        
        try:
            target_address = self.accounts.get(target_role)
            if not target_address:
                raise ValueError(f"Unknown target role: {target_role}")
            
            return self.multisig_contract.create_proposal(target_address, amount_eth, data, creator_role)
            
        except Exception as e:
            logger.error(f"❌ Failed to create multisig proposal: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def sign_multisig_proposal(self, proposal_id: int, signer_role: str) -> Dict:
        """签名多签名提案"""
        if not self.multisig_contract:
            return {
                "success": False,
                "error": "MultiSig contract not initialized"
            }
        
        try:
            return self.multisig_contract.sign_proposal(proposal_id, signer_role)
            
        except Exception as e:
            logger.error(f"❌ Failed to sign multisig proposal: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_multisig_proposal(self, proposal_id: int) -> Dict:
        """获取多签名提案详情"""
        if not self.multisig_contract:
            return {
                "success": False,
                "error": "MultiSig contract not initialized"
            }
        
        try:
            proposal = self.multisig_contract.get_proposal(proposal_id)
            if proposal:
                return {
                    "success": True,
                    "proposal": proposal
                }
            else:
                return {
                    "success": False,
                    "error": f"Proposal {proposal_id} not found"
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to get multisig proposal: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_multisig_info(self) -> Dict:
        """获取多签名合约信息"""
        if not self.multisig_contract:
            return {
                "success": False,
                "error": "MultiSig contract not initialized"
            }
        
        try:
            contract_info = self.multisig_contract.get_contract_info()
            return {
                "success": True,
                "contract_info": contract_info
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get multisig info: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def has_signed_multisig_proposal(self, proposal_id: int, signer_role: str) -> bool:
        """检查是否已签名多签名提案"""
        if not self.multisig_contract:
            return False
        
        try:
            return self.multisig_contract.has_signed(proposal_id, signer_role)
        except Exception as e:
            logger.error(f"❌ Failed to check multisig signature: {e}")
            return False
    
    # ================================
    # Reward Pool Methods
    # ================================
    
    def deposit_to_reward_pool(self, from_role: str, amount_eth: float) -> Dict:
        """向奖金池充值ETH"""
        if not self.multisig_contract:
            return {
                "success": False,
                "error": "MultiSig contract not initialized"
            }
        
        try:
            return self.multisig_contract.deposit_to_reward_pool(from_role, amount_eth)
            
        except Exception as e:
            logger.error(f"❌ Failed to deposit to reward pool: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_reward_pool_info(self) -> Dict:
        """获取奖金池信息"""
        if not self.multisig_contract:
            return {
                "success": False,
                "error": "MultiSig contract not initialized"
            }
        
        try:
            pool_info = self.multisig_contract.get_reward_pool_info()
            return {
                "success": True,
                "pool_info": pool_info
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get reward pool info: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_manager_contribution(self, manager_role: str) -> Dict:
        """获取Manager贡献记录"""
        if not self.multisig_contract:
            return {
                "success": False,
                "error": "MultiSig contract not initialized"
            }
        
        try:
            manager_address = self.accounts.get(manager_role)
            if not manager_address:
                raise ValueError(f"Unknown manager role: {manager_role}")
            
            contribution = self.multisig_contract.get_contribution(manager_address)
            return {
                "success": True,
                "contribution": contribution
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get manager contribution: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_all_manager_contributions(self) -> Dict:
        """获取所有Manager的贡献记录"""
        if not self.multisig_contract:
            return {
                "success": False,
                "error": "MultiSig contract not initialized"
            }
        
        try:
            contributions = {}
            
            # 获取所有Manager角色的贡献
            manager_roles = ["manager_0", "manager_1", "manager_2"]
            for role in manager_roles:
                if role in self.accounts:
                    manager_address = self.accounts[role]
                    contribution = self.multisig_contract.get_contribution(manager_address)
                    contributions[role] = {
                        "address": manager_address,
                        **contribution
                    }
            
            return {
                "success": True,
                "contributions": contributions
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get all manager contributions: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def distribute_contribution_rewards(self, admin_role: str = "manager_0") -> Dict:
        """分配基于贡献度的奖励"""
        if not self.multisig_contract:
            return {
                "success": False,
                "error": "MultiSig contract not initialized"
            }
        
        try:
            return self.multisig_contract.distribute_contribution_rewards(admin_role)
            
        except Exception as e:
            logger.error(f"❌ Failed to distribute contribution rewards: {e}")
            return {
                "success": False,
                "error": str(e)
            }

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