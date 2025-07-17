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
        
        # Load contract configuration
        self.config = self._load_config()
        
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
    
    def create_proposal(self, target: str, amount: float, data: str = "0x") -> Dict[str, Any]:
        """创建多签名提案"""
        try:
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
                "creator": self.web3_manager.accounts.get('treasury', 'unknown'),
                "created_at": datetime.now().isoformat(),
                "contract_address": self.config["address"]
            }
            
            self.proposals[proposal_id] = proposal
            
            logger.info(f"📝 MultiSig提案创建: ID-{proposal_id}, Target-{target}, Amount-{amount} ETH")
            
            return {
                "success": True,
                "proposal_id": proposal_id,
                "target": target,
                "amount": amount,
                "amount_wei": amount_wei,
                "contract_address": self.config["address"],
                "required_signatures": self.config["threshold"],
                "message": f"Proposal {proposal_id} created successfully"
            }
            
        except Exception as e:
            logger.error(f"❌ MultiSig提案创建失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def sign_proposal(self, proposal_id: int, signer_role: str) -> Dict[str, Any]:
        """签名多签名提案"""
        try:
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