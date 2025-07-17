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