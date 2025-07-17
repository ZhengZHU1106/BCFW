"""
MultiSig Contract Integration Module - Python Version
Integrates custom multi-signature contract with existing Web3Manager
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Set
import logging

logger = logging.getLogger(__name__)

class MultiSigContract:
    """多签名合约集成类"""
    
    def __init__(self, web3_manager):
        self.web3_manager = web3_manager
        self.proposals = {}  # In-memory proposal storage for demo
        self.proposal_counter = 1
        
        # Reward pool state (simulated)
        self.reward_pool_balance = 0.0  # ETH
        self.contributions = {}  # manager_address -> contribution_data
        
        # Load contract configuration
        self.config = self._load_config()
        
        # Initialize reward pool balance from persistent storage or Treasury tracking
        self._initialize_reward_pool_balance()
        
        # Initialize contributions from persistent storage
        self._initialize_contributions()
        
    def _load_config(self) -> Dict[str, Any]:
        """加载合约配置"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), '../assets/multisig_contract.json')
            with open(config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"✅ MultiSig合约配置加载成功: {config['address']}")
            return config
        except Exception as e:
            logger.error(f"❌ MultiSig合约配置加载失败: {e}")
            # 默认配置
            return {
                "address": "0x5FbDB2315678afecb367f032d93F642f64180aa3",
                "owners": [
                    "0x90F8bf6A479f320ead074411a4B0e7944Ea8c9C1",  # manager_0
                    "0xFFcf8FDEE72ac11b5c542428B35EEF5769C409f0",  # manager_1
                    "0x22d491Bde2303f2f43325b2108D26f1eAbA1e32b"   # manager_2
                ],
                "threshold": 2,
                "deployer": "0xE11BA2b4D45Eaed5996Cd0823791E0C93114882d",
                "chainId": 1337
            }
    
    def create_proposal(self, target: str, amount: float, data: str = "0x", creator_role: str = None) -> Dict[str, Any]:
        """创建多签名提案 - 现在检查角色权限"""
        try:
            # 检查创建者角色权限
            if creator_role:
                if not self.is_authorized_creator(creator_role):
                    raise ValueError(f"Role {creator_role} is not authorized to create proposals")
            
            proposal_id = self.proposal_counter
            self.proposal_counter += 1
            
            amount_wei = self.web3_manager.w3.to_wei(amount, 'ether')
            
            proposal = {
                "id": proposal_id,
                "target": target,
                "amount": amount,
                "amount_wei": amount_wei,
                "data": data,
                "executed": False,
                "signature_count": 0,
                "signatures": set(),
                "creator": self.web3_manager.accounts.get(creator_role or 'treasury', 'unknown'),
                "creator_role": creator_role,
                "created_at": datetime.now().isoformat(),
                "contract_address": self.config["address"]
            }
            
            self.proposals[proposal_id] = proposal
            
            logger.info(f"📝 MultiSig提案创建: ID-{proposal_id}, Target-{target}, Amount-{amount} ETH, Creator-{creator_role}")
            
            return {
                "success": True,
                "proposal_id": proposal_id,
                "target": target,
                "amount": amount,
                "amount_wei": amount_wei,
                "contract_address": self.config["address"],
                "required_signatures": self.config["threshold"],
                "creator_role": creator_role,
                "message": f"Proposal {proposal_id} created successfully"
            }
            
        except Exception as e:
            logger.error(f"❌ MultiSig提案创建失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def sign_proposal(self, proposal_id: int, signer_role: str) -> Dict[str, Any]:
        """签名多签名提案 - 现在检查管理员角色权限"""
        try:
            # 检查签名者角色权限
            if not self.is_authorized_signer(signer_role):
                raise ValueError(f"Role {signer_role} is not authorized to sign proposals")
            
            proposal = self.proposals.get(proposal_id)
            if not proposal:
                raise ValueError(f"Proposal {proposal_id} not found")
            
            if proposal["executed"]:
                raise ValueError(f"Proposal {proposal_id} already executed")
            
            signer_address = self.web3_manager.accounts.get(signer_role)
            if not signer_address:
                raise ValueError(f"Unknown signer role: {signer_role}")
            
            if signer_address not in self.config["owners"]:
                raise ValueError(f"{signer_role} is not an authorized signer")
            
            if signer_role in proposal["signatures"]:
                raise ValueError(f"{signer_role} has already signed this proposal")
            
            # 添加签名
            proposal["signatures"].add(signer_role)
            proposal["signature_count"] += 1
            
            # 更新贡献记录
            self._update_contribution(signer_role, proposal["created_at"])
            
            logger.info(f"✅ Proposal {proposal_id} signed by {signer_role} ({proposal['signature_count']}/{self.config['threshold']})")
            
            result = {
                "success": True,
                "proposal_id": proposal_id,
                "signer": signer_address,
                "signer_role": signer_role,
                "signature_count": proposal["signature_count"],
                "required_signatures": self.config["threshold"],
                "signed_at": datetime.now().isoformat()
            }
            
            # 检查是否达到阈值，自动执行
            if proposal["signature_count"] >= self.config["threshold"]:
                execution_result = self._execute_proposal(proposal_id, signer_role)
                result["executed"] = True
                result["execution_result"] = execution_result
            
            return result
            
        except Exception as e:
            logger.error(f"❌ MultiSig提案签名失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "proposal_id": proposal_id,
                "signer_role": signer_role
            }
    
    def _execute_proposal(self, proposal_id: int, executor_role: str) -> Dict[str, Any]:
        """执行提案（内部方法）"""
        try:
            proposal = self.proposals.get(proposal_id)
            
            if proposal["signature_count"] < self.config["threshold"]:
                raise ValueError(f"Insufficient signatures: {proposal['signature_count']}/{self.config['threshold']}")
            
            # 使用现有的Web3Manager发送奖励
            reward_result = self.web3_manager.send_reward(
                'treasury', 
                executor_role, 
                proposal["amount"]
            )
            
            if reward_result["success"]:
                proposal["executed"] = True
                proposal["executed_at"] = datetime.now().isoformat()
                proposal["executor_role"] = executor_role
                proposal["execution_tx_hash"] = reward_result["tx_hash"]
                
                logger.info(f"🎉 Proposal {proposal_id} executed successfully! Reward sent to {executor_role}")
                
                return {
                    "success": True,
                    "proposal_id": proposal_id,
                    "executor": executor_role,
                    "target": proposal["target"],
                    "amount": proposal["amount"],
                    "tx_hash": reward_result["tx_hash"],
                    "gas_used": reward_result["gas_used"],
                    "block_number": reward_result["block_number"],
                    "executed_at": proposal["executed_at"]
                }
            else:
                raise Exception(f"Reward transfer failed: {reward_result['error']}")
                
        except Exception as e:
            logger.error(f"❌ MultiSig提案执行失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "proposal_id": proposal_id
            }
    
    def get_proposal(self, proposal_id: int) -> Dict[str, Any]:
        """获取提案详情"""
        proposal = self.proposals.get(proposal_id)
        if not proposal:
            return None
        
        # 将set转换为list以便JSON序列化
        signatures_list = list(proposal["signatures"])
        
        return {
            "id": proposal["id"],
            "target": proposal["target"],
            "amount": proposal["amount"],
            "amount_wei": proposal["amount_wei"],
            "executed": proposal["executed"],
            "signature_count": proposal["signature_count"],
            "required_signatures": self.config["threshold"],
            "creator": proposal["creator"],
            "created_at": proposal["created_at"],
            "executed_at": proposal.get("executed_at"),
            "executor_role": proposal.get("executor_role"),
            "execution_tx_hash": proposal.get("execution_tx_hash"),
            "contract_address": self.config["address"],
            "signatures": signatures_list
        }
    
    def has_signed(self, proposal_id: int, signer_role: str) -> bool:
        """检查签名者是否已签名"""
        proposal = self.proposals.get(proposal_id)
        return proposal and signer_role in proposal["signatures"]
    
    def get_contract_info(self) -> Dict[str, Any]:
        """获取合约信息"""
        return {
            "address": self.config["address"],
            "owners": self.config["owners"],
            "threshold": self.config["threshold"],
            "owner_count": len(self.config["owners"]),
            "chain_id": self.config["chainId"],
            "deployed_at": self.config.get("deployedAt"),
            "total_proposals": self.proposal_counter - 1
        }
    
    def get_all_proposals(self) -> list:
        """获取所有提案"""
        return [self.get_proposal(proposal_id) for proposal_id in self.proposals.keys()]
    
    def get_pending_proposals(self) -> list:
        """获取待处理提案"""
        return [self.get_proposal(proposal_id) for proposal_id, proposal in self.proposals.items() 
                if not proposal["executed"]]
    
    # ================================
    # Reward Pool Methods
    # ================================
    
    def deposit_to_reward_pool(self, from_role: str, amount_eth: float) -> Dict[str, Any]:
        """向奖金池充值ETH"""
        try:
            # 使用Web3Manager的send_reward功能来模拟充值
            # 从指定角色向treasury账户转账
            deposit_result = self.web3_manager.send_reward(from_role, 'treasury', amount_eth)
            
            if deposit_result["success"]:
                # 更新奖金池余额（模拟）
                self.reward_pool_balance += amount_eth
                
                # 保存状态到文件
                self._save_reward_pool_state()
                
                logger.info(f"💰 Reward pool deposit: {amount_eth} ETH from {from_role}")
                logger.info(f"📊 New pool balance: {self.reward_pool_balance} ETH")
                
                return {
                    "success": True,
                    "depositor_role": from_role,
                    "amount": amount_eth,
                    "new_balance": self.reward_pool_balance,
                    "tx_hash": deposit_result["tx_hash"],
                    "deposited_at": datetime.now().isoformat()
                }
            else:
                raise Exception(f"Deposit transaction failed: {deposit_result['error']}")
                
        except Exception as e:
            logger.error(f"❌ Reward pool deposit failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "depositor_role": from_role,
                "amount": amount_eth
            }
    
    def get_reward_pool_info(self) -> Dict[str, Any]:
        """获取奖金池信息"""
        try:
            # 获取treasury账户的实际余额作为奖金池总额
            treasury_info = self.web3_manager.get_account_info('treasury')
            
            return {
                "balance": self.reward_pool_balance,
                "balance_wei": self.web3_manager.w3.to_wei(self.reward_pool_balance, 'ether'),
                "base_reward": 0.01,  # 基础奖励 0.01 ETH
                "base_reward_wei": self.web3_manager.w3.to_wei(0.01, 'ether'),
                "treasury_balance": treasury_info["balance_eth"],
                "treasury_address": treasury_info["address"],
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get reward pool info: {e}")
            return {
                "balance": 0,
                "balance_wei": 0,
                "base_reward": 0.01,
                "base_reward_wei": self.web3_manager.w3.to_wei(0.01, 'ether'),
                "error": str(e)
            }
    
    def _initialize_reward_pool_balance(self):
        """初始化奖金池余额（从数据库或状态文件恢复）"""
        try:
            # 简化实现：从文件恢复奖金池状态
            state_file = os.path.join(os.path.dirname(__file__), '../assets/reward_pool_state.json')
            if os.path.exists(state_file):
                with open(state_file, 'r') as f:
                    state = json.load(f)
                    self.reward_pool_balance = state.get('balance', 0.0)
                    logger.info(f"✅ 奖金池余额从状态文件恢复: {self.reward_pool_balance} ETH")
            else:
                logger.info("💰 奖金池状态文件不存在，余额设为 0.0 ETH")
        except Exception as e:
            logger.error(f"❌ 恢复奖金池状态失败: {e}")
            self.reward_pool_balance = 0.0
    
    def _save_reward_pool_state(self):
        """保存奖金池状态到文件"""
        try:
            state_file = os.path.join(os.path.dirname(__file__), '../assets/reward_pool_state.json')
            state = {
                'balance': self.reward_pool_balance,
                'last_updated': datetime.now().isoformat()
            }
            with open(state_file, 'w') as f:
                json.dump(state, f)
            logger.debug(f"📝 奖金池状态已保存: {self.reward_pool_balance} ETH")
        except Exception as e:
            logger.error(f"❌ 保存奖金池状态失败: {e}")
    
    def _initialize_contributions(self):
        """初始化Manager贡献度（从状态文件恢复）"""
        try:
            contrib_file = os.path.join(os.path.dirname(__file__), '../assets/contributions_state.json')
            if os.path.exists(contrib_file):
                with open(contrib_file, 'r') as f:
                    self.contributions = json.load(f)
                    logger.info(f"✅ Manager贡献度从状态文件恢复: {len(self.contributions)} 条记录")
            else:
                logger.info("💰 贡献度状态文件不存在，使用空记录")
        except Exception as e:
            logger.error(f"❌ 恢复Manager贡献度失败: {e}")
            self.contributions = {}
    
    def _save_contributions_state(self):
        """保存Manager贡献度到文件"""
        try:
            contrib_file = os.path.join(os.path.dirname(__file__), '../assets/contributions_state.json')
            with open(contrib_file, 'w') as f:
                json.dump(self.contributions, f, indent=2)
            logger.debug(f"📝 Manager贡献度已保存: {len(self.contributions)} 条记录")
        except Exception as e:
            logger.error(f"❌ 保存Manager贡献度失败: {e}")
    
    def get_contribution(self, manager_address: str) -> Dict[str, Any]:
        """获取Manager贡献记录"""
        contribution = self.contributions.get(manager_address, {
            "total_signatures": 0,
            "total_response_time": 0,
            "quality_score": 0,
            "last_signature_time": None
        })
        
        # 计算平均响应时间
        avg_response_time = 0
        if contribution["total_signatures"] > 0:
            avg_response_time = contribution["total_response_time"] / contribution["total_signatures"]
        
        return {
            "total_signatures": contribution["total_signatures"],
            "avg_response_time": avg_response_time,
            "quality_score": contribution["quality_score"],
            "last_signature_time": contribution["last_signature_time"]
        }
    
    def _update_contribution(self, manager_role: str, proposal_created_at: str):
        """更新Manager贡献记录"""
        try:
            manager_address = self.web3_manager.accounts.get(manager_role)
            if not manager_address:
                logger.warning(f"⚠️  Manager address not found for role: {manager_role}")
                return
            
            # 初始化贡献记录
            if manager_address not in self.contributions:
                self.contributions[manager_address] = {
                    "total_signatures": 0,
                    "total_response_time": 0,
                    "quality_score": 0,
                    "last_signature_time": None
                }
            
            contribution = self.contributions[manager_address]
            
            # 计算响应时间
            current_time = datetime.now()
            created_time = datetime.fromisoformat(proposal_created_at)
            response_time_seconds = (current_time - created_time).total_seconds()
            
            # 更新统计
            contribution["total_signatures"] += 1
            contribution["total_response_time"] += response_time_seconds
            contribution["last_signature_time"] = current_time.isoformat()
            
            # 计算质量评分（0-100分标准化）
            contribution["quality_score"] = self._calculate_quality_score(
                response_time_seconds, 
                contribution["last_signature_time"]
            )
            
            logger.info(f"📈 Updated contribution for {manager_role}: {contribution['total_signatures']} signatures, quality: {contribution['quality_score']}")
            
            # 保存贡献度状态
            self._save_contributions_state()
            
        except Exception as e:
            logger.error(f"❌ Failed to update contribution for {manager_role}: {e}")
    
    def _calculate_quality_score(self, response_time_seconds: float, last_signature_time: str) -> int:
        """计算质量评分（0-100分）"""
        # 响应速度分（60%权重）
        if response_time_seconds <= 10:
            speed_score = 60
        elif response_time_seconds <= 30:
            speed_score = 50
        elif response_time_seconds <= 60:
            speed_score = 40
        elif response_time_seconds <= 120:
            speed_score = 30
        elif response_time_seconds <= 300:
            speed_score = 20
        else:
            speed_score = 10
        
        # 活跃度分（40%权重）
        try:
            last_time = datetime.fromisoformat(last_signature_time)
            minutes_since_last = (datetime.now() - last_time).total_seconds() / 60
            
            if minutes_since_last <= 10:
                activity_score = 40
            elif minutes_since_last <= 30:
                activity_score = 30
            elif minutes_since_last <= 60:
                activity_score = 20
            else:
                activity_score = 10
        except:
            # 如果是第一次签名，给满分活跃度
            activity_score = 40
        
        return int(speed_score + activity_score)  # 0-100分
    
    def distribute_contribution_rewards(self, admin_role: str) -> Dict[str, Any]:
        """分配基于贡献度的奖励"""
        try:
            if self.reward_pool_balance <= 0.1:  # 保留一些基础奖励
                raise ValueError("Insufficient reward pool balance")
            
            # 计算总贡献分数
            total_contribution_score = 0
            manager_scores = {}
            
            for manager_role in ["manager_0", "manager_1", "manager_2"]:
                manager_address = self.web3_manager.accounts.get(manager_role)
                if manager_address and manager_address in self.contributions:
                    contribution = self.contributions[manager_address]
                    # 贡献分数 = 签名次数 + 质量分数/100
                    score = contribution["total_signatures"] + (contribution["quality_score"] / 100)
                    manager_scores[manager_role] = score
                    total_contribution_score += score
            
            if total_contribution_score == 0:
                logger.info("📊 No contributions to reward")
                return {"success": True, "message": "No contributions to reward"}
            
            # 可分配奖励（保留0.1 ETH用于基础奖励）
            available_rewards = max(0, self.reward_pool_balance - 0.1)
            distribution_results = []
            
            # 按比例分配奖励
            for manager_role, score in manager_scores.items():
                if score > 0:
                    reward_amount = (available_rewards * score) / total_contribution_score
                    
                    if reward_amount > 0.001:  # 最小奖励阈值
                        reward_result = self.web3_manager.send_reward('treasury', manager_role, reward_amount)
                        
                        if reward_result["success"]:
                            self.reward_pool_balance -= reward_amount
                            distribution_results.append({
                                "manager_role": manager_role,
                                "reward_amount": reward_amount,
                                "contribution_score": score,
                                "tx_hash": reward_result["tx_hash"]
                            })
            
            logger.info(f"🎁 Distributed {len(distribution_results)} contribution rewards")
            
            return {
                "success": True,
                "distributions": distribution_results,
                "total_distributed": sum(r["reward_amount"] for r in distribution_results),
                "remaining_pool": self.reward_pool_balance,
                "distributed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to distribute contribution rewards: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # ================================
    # Role Authorization Methods
    # ================================
    
    def is_authorized_creator(self, role: str) -> bool:
        """检查角色是否有权限创建提案 (Operator或Manager)"""
        return role in ["operator_0", "operator_1", "operator_2", "operator_3", "operator_4", 
                       "manager_0", "manager_1", "manager_2"]
    
    def is_authorized_signer(self, role: str) -> bool:
        """检查角色是否有权限签名提案 (仅Manager)"""
        return role in ["manager_0", "manager_1", "manager_2"]
    
    def get_user_role(self, user_address: str) -> str:
        """根据地址获取用户角色"""
        # 反向查找角色
        for role, address in self.web3_manager.accounts.items():
            if address.lower() == user_address.lower():
                if role in ["manager_0", "manager_1", "manager_2"]:
                    return "MANAGER"
                elif role.startswith("operator_"):
                    return "OPERATOR"
        return "NONE"
    
    def get_role_info(self, role: str) -> Dict[str, Any]:
        """获取角色信息"""
        address = self.web3_manager.accounts.get(role)
        if not address:
            return {"exists": False}
        
        return {
            "exists": True,
            "address": address,
            "role": role,
            "can_create_proposals": self.is_authorized_creator(role),
            "can_sign_proposals": self.is_authorized_signer(role),
            "is_manager": self.is_authorized_signer(role),
            "is_operator": role.startswith("operator_")
        }