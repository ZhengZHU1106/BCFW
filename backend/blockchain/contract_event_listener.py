"""
智能合约事件监听器
实现合约事件的实时监听和数据库同步
"""

import asyncio
import logging
from typing import Dict, List, Optional, Callable
from web3 import Web3
from web3.contract import Contract
from sqlalchemy.orm import Session
from datetime import datetime
import json

from backend.database.connection import get_db
from backend.database.models import Proposal, ThreatDetectionLog, ExecutionLog

logger = logging.getLogger(__name__)

class ContractEventListener:
    """智能合约事件监听器"""
    
    def __init__(self, smart_contract_manager):
        self.contract_manager = smart_contract_manager
        self.w3 = smart_contract_manager.w3
        self.contract = smart_contract_manager.contract
        self.is_listening = False
        self.event_filters = {}
        self.latest_block = 0
        
    async def start_listening(self):
        """开始监听合约事件"""
        if self.is_listening:
            logger.warning("事件监听器已经在运行")
            return
        
        self.is_listening = True
        self.latest_block = self.w3.eth.block_number
        
        logger.info(f"🎧 开始监听智能合约事件，起始区块: {self.latest_block}")
        
        # 创建事件过滤器
        self._create_event_filters()
        
        # 启动事件监听循环
        await self._event_listening_loop()
    
    def stop_listening(self):
        """停止监听合约事件"""
        self.is_listening = False
        logger.info("🛑 停止监听智能合约事件")
    
    def _create_event_filters(self):
        """创建事件过滤器"""
        try:
            # ProposalCreated事件过滤器
            self.event_filters['ProposalCreated'] = self.contract.events.ProposalCreated.create_filter(
                fromBlock=self.latest_block
            )
            
            # ProposalSigned事件过滤器  
            self.event_filters['ProposalSigned'] = self.contract.events.ProposalSigned.create_filter(
                fromBlock=self.latest_block
            )
            
            # ProposalExecuted事件过滤器
            self.event_filters['ProposalExecuted'] = self.contract.events.ProposalExecuted.create_filter(
                fromBlock=self.latest_block
            )
            
            logger.info("✅ 智能合约事件过滤器创建成功")
            
        except Exception as e:
            logger.error(f"❌ 创建事件过滤器失败: {e}")
            raise
    
    async def _event_listening_loop(self):
        """事件监听主循环"""
        while self.is_listening:
            try:
                # 检查新事件
                await self._check_new_events()
                
                # 短暂休眠
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"❌ 事件监听循环错误: {e}")
                await asyncio.sleep(5)  # 错误时延长休眠时间
    
    async def _check_new_events(self):
        """检查新事件"""
        try:
            # 检查ProposalCreated事件
            for event in self.event_filters['ProposalCreated'].get_new_entries():
                await self._handle_proposal_created(event)
            
            # 检查ProposalSigned事件
            for event in self.event_filters['ProposalSigned'].get_new_entries():
                await self._handle_proposal_signed(event)
            
            # 检查ProposalExecuted事件
            for event in self.event_filters['ProposalExecuted'].get_new_entries():
                await self._handle_proposal_executed(event)
                
        except Exception as e:
            logger.error(f"❌ 检查新事件失败: {e}")
    
    async def _handle_proposal_created(self, event):
        """处理ProposalCreated事件"""
        try:
            args = event['args']
            proposal_id = args['proposalId']
            creator = args['creator']
            target = args['target']
            amount = args['amount']
            
            logger.info(f"📝 检测到新提案创建事件: ID-{proposal_id}, 创建者-{creator}")
            
            # 同步到数据库
            with next(get_db()) as db:
                await self._sync_proposal_to_db(db, proposal_id, 'created')
            
        except Exception as e:
            logger.error(f"❌ 处理ProposalCreated事件失败: {e}")
    
    async def _handle_proposal_signed(self, event):
        """处理ProposalSigned事件"""
        try:
            args = event['args']
            proposal_id = args['proposalId']
            signer = args['signer']
            
            logger.info(f"✅ 检测到提案签名事件: ID-{proposal_id}, 签名者-{signer}")
            
            # 同步到数据库
            with next(get_db()) as db:
                await self._sync_proposal_to_db(db, proposal_id, 'signed', signer)
            
        except Exception as e:
            logger.error(f"❌ 处理ProposalSigned事件失败: {e}")
    
    async def _handle_proposal_executed(self, event):
        """处理ProposalExecuted事件"""
        try:
            args = event['args']
            proposal_id = args['proposalId']
            executor = args['executor']
            target = args['target']
            amount = args['amount']
            
            logger.info(f"🎉 检测到提案执行事件: ID-{proposal_id}, 执行者-{executor}")
            
            # 同步到数据库
            with next(get_db()) as db:
                await self._sync_proposal_to_db(db, proposal_id, 'executed', executor)
                await self._create_execution_log(db, proposal_id, executor, target, amount)
            
        except Exception as e:
            logger.error(f"❌ 处理ProposalExecuted事件失败: {e}")
    
    async def _sync_proposal_to_db(self, db: Session, contract_proposal_id: int, 
                                  action: str, actor: str = None):
        """同步提案状态到数据库"""
        try:
            # 查找对应的数据库提案
            proposal = db.query(Proposal).filter(
                Proposal.contract_proposal_id == contract_proposal_id
            ).first()
            
            if not proposal:
                logger.warning(f"⚠️ 未找到合约提案ID {contract_proposal_id} 对应的数据库记录")
                return
            
            # 从合约获取最新状态
            contract_proposal = self.contract_manager.get_proposal(contract_proposal_id)
            if not contract_proposal:
                logger.error(f"❌ 无法从合约获取提案 {contract_proposal_id} 的信息")
                return
            
            # 更新数据库状态
            if action == 'created':
                proposal.status = 'pending'
                proposal.contract_address = self.contract_manager.contract_address
                
            elif action == 'signed':
                # 更新签名信息
                signed_by = proposal.signed_by or []
                
                # 将地址转换为角色名（需要映射逻辑）
                signer_role = self._address_to_role(actor)
                if signer_role and signer_role not in signed_by:
                    signed_by.append(signer_role)
                    proposal.signed_by = signed_by
                    proposal.signatures_count = len(signed_by)
                
            elif action == 'executed':
                proposal.status = 'executed'
                proposal.approved_at = datetime.now()
                
                # 记录执行者
                executor_role = self._address_to_role(actor)
                if executor_role:
                    proposal.final_signer = executor_role
            
            db.commit()
            logger.info(f"✅ 数据库提案同步成功: DB-ID-{proposal.id}, Contract-ID-{contract_proposal_id}, Action-{action}")
            
        except Exception as e:
            logger.error(f"❌ 同步提案到数据库失败: {e}")
            db.rollback()
    
    async def _create_execution_log(self, db: Session, contract_proposal_id: int,
                                   executor: str, target: str, amount: int):
        """创建执行日志"""
        try:
            # 查找对应的提案
            proposal = db.query(Proposal).filter(
                Proposal.contract_proposal_id == contract_proposal_id
            ).first()
            
            if not proposal:
                logger.warning(f"⚠️ 创建执行日志时未找到提案: Contract-ID-{contract_proposal_id}")
                return
            
            # 创建执行日志
            execution_log = ExecutionLog(
                proposal_id=proposal.id,
                action_type="blockchain_reward",
                target_ip=proposal.target_ip or "N/A",
                success=True,
                response_data={
                    "contract_proposal_id": contract_proposal_id,
                    "executor": executor,
                    "target": target,
                    "amount_wei": amount,
                    "amount_eth": self.w3.from_wei(amount, 'ether'),
                    "action": "智能合约自动执行奖励发放"
                }
            )
            
            db.add(execution_log)
            db.commit()
            
            logger.info(f"✅ 执行日志创建成功: Contract-ID-{contract_proposal_id}")
            
        except Exception as e:
            logger.error(f"❌ 创建执行日志失败: {e}")
            db.rollback()
    
    def _address_to_role(self, address: str) -> Optional[str]:
        """将以太坊地址转换为角色名"""
        try:
            # 遍历web3_manager的账户映射
            for role, addr in self.contract_manager.web3_manager.accounts.items():
                if addr.lower() == address.lower():
                    return role
            
            logger.warning(f"⚠️ 未找到地址 {address} 对应的角色")
            return None
            
        except Exception as e:
            logger.error(f"❌ 地址到角色转换失败: {e}")
            return None

class ContractSyncService:
    """合约状态同步服务"""
    
    def __init__(self, smart_contract_manager):
        self.contract_manager = smart_contract_manager
        self.event_listener = ContractEventListener(smart_contract_manager)
    
    async def start_sync_service(self):
        """启动同步服务"""
        logger.info("🚀 启动智能合约同步服务")
        
        # 首次同步历史数据
        await self._sync_historical_data()
        
        # 启动实时事件监听
        await self.event_listener.start_listening()
    
    def stop_sync_service(self):
        """停止同步服务"""
        self.event_listener.stop_listening()
        logger.info("🛑 智能合约同步服务已停止")
    
    async def _sync_historical_data(self):
        """同步历史数据"""
        try:
            logger.info("📚 开始同步历史合约数据...")
            
            # 获取所有合约提案
            contract_proposals = self.contract_manager.get_all_proposals()
            
            with next(get_db()) as db:
                for contract_proposal in contract_proposals:
                    await self._ensure_proposal_in_db(db, contract_proposal)
            
            logger.info(f"✅ 历史数据同步完成，共处理 {len(contract_proposals)} 个提案")
            
        except Exception as e:
            logger.error(f"❌ 历史数据同步失败: {e}")
    
    async def _ensure_proposal_in_db(self, db: Session, contract_proposal: Dict):
        """确保合约提案在数据库中存在"""
        try:
            contract_id = contract_proposal['id']
            
            # 检查是否已存在
            existing = db.query(Proposal).filter(
                Proposal.contract_proposal_id == contract_id
            ).first()
            
            if existing:
                # 更新状态
                if contract_proposal['executed'] and existing.status != 'executed':
                    existing.status = 'executed'
                    existing.approved_at = datetime.fromtimestamp(contract_proposal['created_at'])
                    db.commit()
                    logger.info(f"✅ 更新提案状态: DB-ID-{existing.id}, Contract-ID-{contract_id}")
            else:
                logger.info(f"⚠️ 发现孤立的合约提案: Contract-ID-{contract_id}")
                # 可以选择创建占位符记录或记录警告
                
        except Exception as e:
            logger.error(f"❌ 处理合约提案失败: {e}")

# 全局同步服务实例
_sync_service = None

def get_contract_sync_service():
    """获取合约同步服务实例"""
    global _sync_service
    if _sync_service is None:
        from backend.blockchain.smart_contract_manager import get_smart_contract_manager
        contract_manager = get_smart_contract_manager()
        _sync_service = ContractSyncService(contract_manager)
    return _sync_service