"""
数据库模型定义
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
from typing import Dict, Any

Base = declarative_base()

class Proposal(Base):
    """提案模型"""
    __tablename__ = 'proposals'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 威胁检测信息
    threat_type = Column(String(100), nullable=False, comment='威胁类型')
    confidence = Column(Float, nullable=False, comment='置信度')
    true_label = Column(String(100), comment='真实标签（用于验证）')
    
    # 提案信息
    proposal_type = Column(String(50), nullable=False, comment='提案类型：auto/manual')
    status = Column(String(50), default='pending', comment='状态：pending/approved/rejected')
    target_ip = Column(String(45), comment='目标IP地址')
    action_type = Column(String(50), default='block', comment='动作类型：block/unblock')
    
    # 签名信息
    signatures_required = Column(Integer, default=2, comment='需要的签名数')
    signatures_count = Column(Integer, default=0, comment='当前签名数')
    signed_by = Column(JSON, default=list, comment='签名者列表')
    
    # 激励信息
    reward_paid = Column(Boolean, default=False, comment='是否已支付奖励')
    reward_recipient = Column(String(100), comment='奖励接收者')
    reward_tx_hash = Column(String(66), comment='奖励交易哈希')
    
    # MultiSig合约集成字段
    contract_proposal_id = Column(Integer, nullable=True, comment='合约中的提案ID')
    contract_address = Column(String(42), nullable=True, comment='MultiSig合约地址')
    
    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment='创建时间')
    approved_at = Column(DateTime, comment='批准时间')
    executed_at = Column(DateTime, comment='执行时间')
    
    # 扩展数据
    detection_data = Column(JSON, comment='完整检测数据')
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'threat_type': self.threat_type,
            'confidence': self.confidence,
            'true_label': self.true_label,
            'proposal_type': self.proposal_type,
            'status': self.status,
            'target_ip': self.target_ip,
            'action_type': self.action_type,
            'signatures_required': self.signatures_required,
            'signatures_count': self.signatures_count,
            'signed_by': self.signed_by,
            'reward_paid': self.reward_paid,
            'reward_recipient': self.reward_recipient,
            'reward_tx_hash': self.reward_tx_hash,
            'contract_proposal_id': self.contract_proposal_id,
            'contract_address': self.contract_address,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'executed_at': self.executed_at.isoformat() if self.executed_at else None,
            'detection_data': self.detection_data
        }

class ExecutionLog(Base):
    """执行日志模型"""
    __tablename__ = 'execution_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 关联信息
    proposal_id = Column(Integer, comment='关联的提案ID')
    
    # 执行信息
    action_type = Column(String(50), nullable=False, comment='执行动作：block/unblock/auto_block')
    target_ip = Column(String(45), comment='目标IP')
    threat_type = Column(String(100), comment='威胁类型')
    confidence = Column(Float, comment='置信度')
    
    # 执行结果
    execution_status = Column(String(50), default='success', comment='执行状态：success/failed')
    execution_details = Column(Text, comment='执行详情')
    
    # 区块链信息
    manager_account = Column(String(42), comment='执行Manager账户')
    reward_tx_hash = Column(String(66), comment='奖励交易哈希')
    
    # 时间戳
    executed_at = Column(DateTime, default=func.now(), comment='执行时间')
    
    # 扩展数据
    execution_data = Column(JSON, comment='完整执行数据')
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'proposal_id': self.proposal_id,
            'action_type': self.action_type,
            'target_ip': self.target_ip,
            'threat_type': self.threat_type,
            'confidence': self.confidence,
            'execution_status': self.execution_status,
            'execution_details': self.execution_details,
            'manager_account': self.manager_account,
            'reward_tx_hash': self.reward_tx_hash,
            'executed_at': self.executed_at.isoformat() if self.executed_at else None,
            'execution_data': self.execution_data
        }

class ThreatDetectionLog(Base):
    """威胁检测日志模型"""
    __tablename__ = 'threat_detection_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 检测信息
    threat_type = Column(String(100), nullable=False, comment='威胁类型')
    confidence = Column(Float, nullable=False, comment='置信度')
    true_label = Column(String(100), comment='真实标签')
    response_level = Column(String(50), nullable=False, comment='响应级别')
    
    # 处理信息
    source_ip = Column(String(45), comment='源IP地址')
    target_ip = Column(String(45), comment='目标IP地址')
    action_taken = Column(String(100), comment='采取的行动')
    
    # 关联信息
    proposal_id = Column(Integer, comment='关联的提案ID（如果创建了提案）')
    execution_log_id = Column(Integer, comment='关联的执行日志ID（如果直接执行）')
    
    # 时间戳
    detected_at = Column(DateTime, default=func.now(), comment='检测时间')
    
    # 完整数据
    detection_data = Column(JSON, comment='完整检测数据')
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'threat_type': self.threat_type,
            'confidence': self.confidence,
            'true_label': self.true_label,
            'response_level': self.response_level,
            'source_ip': self.source_ip,
            'target_ip': self.target_ip,
            'action_taken': self.action_taken,
            'proposal_id': self.proposal_id,
            'execution_log_id': self.execution_log_id,
            'detected_at': self.detected_at.isoformat() if self.detected_at else None,
            'detection_data': self.detection_data
        }

class RewardPool(Base):
    """奖金池模型"""
    __tablename__ = 'reward_pools'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 奖金池信息
    balance = Column(Float, default=0.0, comment='奖金池余额(ETH)')
    balance_wei = Column(String(100), default='0', comment='奖金池余额(Wei)')
    base_reward = Column(Float, default=0.01, comment='基础奖励(ETH)')
    
    # 管理信息
    treasury_address = Column(String(42), comment='国库地址')
    contract_address = Column(String(42), comment='合约地址')
    
    # 统计信息
    total_deposits = Column(Float, default=0.0, comment='总充值额度(ETH)')
    total_rewards = Column(Float, default=0.0, comment='总奖励发放(ETH)')
    active_managers = Column(Integer, default=0, comment='活跃Manager数量')
    
    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment='创建时间')
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment='更新时间')
    
    # 扩展数据
    pool_config = Column(JSON, comment='奖金池配置')
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'balance': self.balance,
            'balance_wei': self.balance_wei,
            'base_reward': self.base_reward,
            'treasury_address': self.treasury_address,
            'contract_address': self.contract_address,
            'total_deposits': self.total_deposits,
            'total_rewards': self.total_rewards,
            'active_managers': self.active_managers,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'pool_config': self.pool_config
        }

class RewardPoolTransaction(Base):
    """奖金池交易记录模型"""
    __tablename__ = 'reward_pool_transactions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 交易信息
    transaction_type = Column(String(50), nullable=False, comment='交易类型：deposit/reward/distribute')
    amount = Column(Float, nullable=False, comment='交易金额(ETH)')
    amount_wei = Column(String(100), comment='交易金额(Wei)')
    
    # 账户信息
    from_role = Column(String(50), comment='发送方角色')
    from_address = Column(String(42), comment='发送方地址')
    to_role = Column(String(50), comment='接收方角色')
    to_address = Column(String(42), comment='接收方地址')
    
    # 区块链信息
    tx_hash = Column(String(66), comment='交易哈希')
    block_number = Column(Integer, comment='区块号')
    gas_used = Column(Integer, comment='Gas消耗')
    
    # 关联信息
    proposal_id = Column(Integer, comment='关联的提案ID')
    pool_id = Column(Integer, comment='关联的奖金池ID')
    
    # 状态信息
    status = Column(String(50), default='pending', comment='交易状态：pending/confirmed/failed')
    error_message = Column(Text, comment='错误信息')
    
    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment='创建时间')
    confirmed_at = Column(DateTime, comment='确认时间')
    
    # 扩展数据
    transaction_data = Column(JSON, comment='完整交易数据')
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'transaction_type': self.transaction_type,
            'amount': self.amount,
            'amount_wei': self.amount_wei,
            'from_role': self.from_role,
            'from_address': self.from_address,
            'to_role': self.to_role,
            'to_address': self.to_address,
            'tx_hash': self.tx_hash,
            'block_number': self.block_number,
            'gas_used': self.gas_used,
            'proposal_id': self.proposal_id,
            'pool_id': self.pool_id,
            'status': self.status,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'confirmed_at': self.confirmed_at.isoformat() if self.confirmed_at else None,
            'transaction_data': self.transaction_data
        }

class ContributionRecord(Base):
    """Manager贡献记录模型"""
    __tablename__ = 'contribution_records'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Manager信息
    manager_role = Column(String(50), nullable=False, comment='Manager角色')
    manager_address = Column(String(42), nullable=False, comment='Manager地址')
    
    # 贡献统计
    total_signatures = Column(Integer, default=0, comment='总签名次数')
    total_response_time = Column(Float, default=0.0, comment='总响应时间(秒)')
    avg_response_time = Column(Float, default=0.0, comment='平均响应时间(秒)')
    quality_score = Column(Integer, default=0, comment='质量评分(0-100)')
    
    # 奖励信息
    total_rewards_earned = Column(Float, default=0.0, comment='累计获得奖励(ETH)')
    last_reward_amount = Column(Float, comment='最后一次奖励金额(ETH)')
    reward_count = Column(Integer, default=0, comment='获得奖励次数')
    
    # 活动信息
    last_signature_time = Column(DateTime, comment='最后签名时间')
    last_reward_time = Column(DateTime, comment='最后获得奖励时间')
    active_since = Column(DateTime, default=func.now(), comment='活跃开始时间')
    
    # 性能等级
    performance_grade = Column(String(20), default='No Activity', comment='性能等级')
    
    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment='创建时间')
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment='更新时间')
    
    # 扩展数据
    contribution_data = Column(JSON, comment='详细贡献数据')
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'manager_role': self.manager_role,
            'manager_address': self.manager_address,
            'total_signatures': self.total_signatures,
            'total_response_time': self.total_response_time,
            'avg_response_time': self.avg_response_time,
            'quality_score': self.quality_score,
            'total_rewards_earned': self.total_rewards_earned,
            'last_reward_amount': self.last_reward_amount,
            'reward_count': self.reward_count,
            'last_signature_time': self.last_signature_time.isoformat() if self.last_signature_time else None,
            'last_reward_time': self.last_reward_time.isoformat() if self.last_reward_time else None,
            'active_since': self.active_since.isoformat() if self.active_since else None,
            'performance_grade': self.performance_grade,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'contribution_data': self.contribution_data
        }