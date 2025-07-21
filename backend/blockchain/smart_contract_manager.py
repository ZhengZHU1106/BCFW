"""
智能合约管理器 - 真正的区块链交互
替代 multisig_contract.js 的JavaScript模拟
"""

import json
import logging
from typing import Dict, List, Optional, Any
from web3 import Web3
from web3.contract import Contract
from datetime import datetime

logger = logging.getLogger(__name__)

class SmartContractManager:
    """真正的智能合约管理器"""
    
    def __init__(self, web3_manager):
        self.web3_manager = web3_manager
        self.w3 = web3_manager.w3
        self.contract: Optional[Contract] = None
        self.contract_address = None
        self.contract_abi = None
        self._load_contract_config()
    
    def _load_contract_config(self):
        """加载合约配置和ABI"""
        try:
            # 加载合约地址配置
            with open('backend/assets/multisig_contract.json', 'r') as f:
                config = json.load(f)
                self.contract_address = config['address']
            
            # 加载合约ABI
            with open('backend/assets/multisig_interface.json', 'r') as f:
                interface = json.load(f)
                self.contract_abi = interface['abi']
            
            # 创建合约实例
            self.contract = self.w3.eth.contract(
                address=self.contract_address,
                abi=self.contract_abi
            )
            
            logger.info(f"✅ 智能合约加载成功: {self.contract_address}")
            
        except Exception as e:
            logger.error(f"❌ 智能合约加载失败: {e}")
            raise
    
    def create_proposal(self, target_address: str, amount_eth: float, operator_role: str) -> Dict:
        """在智能合约中创建提案"""
        try:
            # 转换金额为wei
            amount_wei = self.w3.to_wei(amount_eth, 'ether')
            
            # 获取操作员账户
            operator_account = self.web3_manager.accounts[operator_role]
            operator_private_key = self.web3_manager.private_keys[operator_role]
            
            # 构建交易
            function_call = self.contract.functions.createProposal(
                target_address,
                amount_wei,
                b''  # 空的data字段
            )
            
            # 估算gas
            gas_estimate = function_call.estimate_gas({'from': operator_account})
            
            # 构建交易
            transaction = function_call.build_transaction({
                'from': operator_account,
                'gas': gas_estimate,
                'gasPrice': self.w3.to_wei('1', 'gwei'),
                'nonce': self.w3.eth.get_transaction_count(operator_account)
            })
            
            # 签名并发送交易
            signed_txn = self.w3.eth.account.sign_transaction(
                transaction, 
                private_key=operator_private_key
            )
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            
            # 等待交易确认
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            # 解析事件获取提案ID
            proposal_id = None
            for log in receipt.logs:
                try:
                    decoded_log = self.contract.events.ProposalCreated().process_log(log)
                    proposal_id = decoded_log['args']['proposalId']
                    break
                except:
                    continue
            
            if proposal_id is None:
                raise ValueError("无法从交易日志中获取提案ID")
            
            logger.info(f"✅ 智能合约提案创建成功: ID-{proposal_id}, 交易哈希: {tx_hash.hex()}")
            
            return {
                'success': True,
                'proposal_id': proposal_id,
                'tx_hash': tx_hash.hex(),
                'block_number': receipt['blockNumber'],
                'gas_used': receipt['gasUsed'],
                'target': target_address,
                'amount': amount_eth,
                'creator': operator_account,
                'created_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ 智能合约提案创建失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def sign_proposal(self, proposal_id: int, manager_role: str) -> Dict:
        """在智能合约中签名提案"""
        try:
            # 获取管理员账户
            manager_account = self.web3_manager.accounts[manager_role]
            manager_private_key = self.web3_manager.private_keys[manager_role]
            
            # 获取提案信息，检查是否存在
            try:
                proposal_data = self.contract.functions.proposals(proposal_id).call()
                if proposal_data[0] == 0:  # proposal id为0表示不存在
                    return {
                        'success': False,
                        'error': f'提案 {proposal_id} 不存在'
                    }
            except Exception as e:
                return {
                    'success': False,
                    'error': f'获取提案信息失败: {str(e)}'
                }
            
            # 构建交易
            function_call = self.contract.functions.signProposal(proposal_id)
            
            # 估算gas
            gas_estimate = function_call.estimate_gas({'from': manager_account})
            
            # 构建交易
            transaction = function_call.build_transaction({
                'from': manager_account,
                'gas': gas_estimate,
                'gasPrice': self.w3.to_wei('1', 'gwei'),
                'nonce': self.w3.eth.get_transaction_count(manager_account)
            })
            
            # 签名并发送交易
            signed_txn = self.w3.eth.account.sign_transaction(
                transaction, 
                private_key=manager_private_key
            )
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            
            # 等待交易确认
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            # 检查是否自动执行
            executed = False
            execution_tx_hash = None
            
            for log in receipt.logs:
                try:
                    # 检查ProposalExecuted事件
                    decoded_log = self.contract.events.ProposalExecuted().process_log(log)
                    if decoded_log['args']['proposalId'] == proposal_id:
                        executed = True
                        execution_tx_hash = tx_hash.hex()
                        break
                except:
                    continue
            
            logger.info(f"✅ 智能合约提案签名成功: ID-{proposal_id}, 管理员: {manager_role}")
            if executed:
                logger.info(f"🎉 提案自动执行成功: ID-{proposal_id}")
            
            return {
                'success': True,
                'proposal_id': proposal_id,
                'signer': manager_account,
                'signer_role': manager_role,
                'tx_hash': tx_hash.hex(),
                'block_number': receipt['blockNumber'],
                'gas_used': receipt['gasUsed'],
                'executed': executed,
                'execution_tx_hash': execution_tx_hash,
                'signed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ 智能合约提案签名失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'proposal_id': proposal_id,
                'signer_role': manager_role
            }
    
    def get_proposal(self, proposal_id: int) -> Optional[Dict]:
        """从智能合约获取提案详情"""
        try:
            proposal_data = self.contract.functions.proposals(proposal_id).call()
            
            # 解析提案数据
            return {
                'id': proposal_data[0],
                'target': proposal_data[1],
                'amount': self.w3.from_wei(proposal_data[2], 'ether'),
                'data': proposal_data[3].hex(),
                'executed': proposal_data[4],
                'signature_count': proposal_data[5],
                'creator': proposal_data[6],
                'created_at': proposal_data[7],
                'contract_address': self.contract_address
            }
            
        except Exception as e:
            logger.error(f"❌ 获取智能合约提案失败: {e}")
            return None
    
    def get_all_proposals(self) -> List[Dict]:
        """获取所有提案（通过事件日志）"""
        try:
            # 获取所有ProposalCreated事件
            proposal_filter = self.contract.events.ProposalCreated.create_filter(
                fromBlock=0,
                toBlock='latest'
            )
            
            proposals = []
            for event in proposal_filter.get_all_entries():
                proposal_id = event['args']['proposalId']
                proposal_data = self.get_proposal(proposal_id)
                if proposal_data:
                    proposals.append(proposal_data)
            
            return proposals
            
        except Exception as e:
            logger.error(f"❌ 获取所有智能合约提案失败: {e}")
            return []
    
    def get_contract_info(self) -> Dict:
        """获取合约信息"""
        try:
            proposal_count = self.contract.functions.proposalCount().call()
            threshold = self.contract.functions.threshold().call()
            
            return {
                'address': self.contract_address,
                'proposal_count': proposal_count,
                'threshold': threshold,
                'balance': self.w3.from_wei(self.w3.eth.get_balance(self.contract_address), 'ether')
            }
            
        except Exception as e:
            logger.error(f"❌ 获取合约信息失败: {e}")
            return {}

# 全局智能合约管理器实例
_contract_manager = None

def get_smart_contract_manager():
    """获取智能合约管理器实例"""
    global _contract_manager
    if _contract_manager is None:
        from backend.blockchain.web3_manager import get_web3_manager
        web3_manager = get_web3_manager()
        _contract_manager = SmartContractManager(web3_manager)
    return _contract_manager