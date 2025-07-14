"""
业务逻辑服务层
"""

import random
from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
import logging

from ..database.models import Proposal, ExecutionLog, ThreatDetectionLog
from ..blockchain.web3_manager import get_web3_manager
from ..ai_module.model_loader import get_threat_model
from ..config import THREAT_THRESHOLDS, INCENTIVE_CONFIG

logger = logging.getLogger(__name__)

class ThreatDetectionService:
    """威胁检测服务"""
    
    def __init__(self):
        self.threat_model = get_threat_model()
        self.web3_manager = get_web3_manager()
    
    def simulate_attack(self, db: Session) -> Dict:
        """模拟攻击检测"""
        try:
            # 执行AI检测
            detection_result = self.threat_model.simulate_attack_detection()
            
            # 生成模拟IP地址
            source_ip = self._generate_random_ip()
            target_ip = self._generate_random_ip()
            
            # 记录检测日志
            detection_log = ThreatDetectionLog(
                threat_type=detection_result['predicted_class'],
                confidence=detection_result['confidence'],
                true_label=detection_result['true_label'],
                response_level=detection_result['response_level'],
                source_ip=source_ip,
                target_ip=target_ip,
                detection_data=detection_result
            )
            
            # 根据响应级别处理
            response_action = self._handle_detection_response(
                db, detection_result, detection_log, target_ip
            )
            
            # 更新检测日志的处理信息
            detection_log.action_taken = response_action['action_taken']
            detection_log.proposal_id = response_action.get('proposal_id')
            detection_log.execution_log_id = response_action.get('execution_log_id')
            
            db.add(detection_log)
            db.commit()
            
            result = {
                "detection_id": detection_log.id,
                "threat_info": {
                    "predicted_class": detection_result['predicted_class'],
                    "confidence": detection_result['confidence'],
                    "true_label": detection_result['true_label'],
                    "response_level": detection_result['response_level']
                },
                "network_info": {
                    "source_ip": source_ip,
                    "target_ip": target_ip
                },
                "response_action": response_action,
                "timestamp": detection_log.detected_at.isoformat()
            }
            
            logger.info(f"🎯 攻击模拟完成: {detection_result['predicted_class']} "
                       f"(置信度: {detection_result['confidence']:.4f})")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 攻击模拟失败: {e}")
            db.rollback()
            raise
    
    def _handle_detection_response(self, db: Session, detection_result: Dict, 
                                 detection_log: ThreatDetectionLog, target_ip: str) -> Dict:
        """处理检测响应"""
        response_level = detection_result['response_level']
        
        if response_level == "automatic_response":
            # 高置信度：自动响应
            execution_log = self._execute_automatic_response(
                db, detection_result, target_ip
            )
            return {
                "action_taken": "automatic_block",
                "execution_log_id": execution_log.id,
                "description": "高置信度威胁，自动执行封锁"
            }
            
        elif response_level == "auto_create_proposal":
            # 中高置信度：自动创建提案
            proposal = self._create_auto_proposal(db, detection_result, target_ip)
            return {
                "action_taken": "auto_proposal_created",
                "proposal_id": proposal.id,
                "description": "中高置信度威胁，已自动创建提案等待Manager审批"
            }
            
        elif response_level == "manual_decision_alert":
            # 中低置信度：人工决策告警
            return {
                "action_taken": "manual_alert",
                "description": "中低置信度威胁，已生成告警等待Operator手动决策"
            }
            
        else:
            # 低置信度：静默记录
            return {
                "action_taken": "silent_logging",
                "description": "低置信度事件，已静默记录"
            }
    
    def _execute_automatic_response(self, db: Session, detection_result: Dict, 
                                  target_ip: str) -> ExecutionLog:
        """执行自动响应"""
        execution_log = ExecutionLog(
            action_type="auto_block",
            target_ip=target_ip,
            threat_type=detection_result['predicted_class'],
            confidence=detection_result['confidence'],
            execution_status="success",
            execution_details=f"自动封锁IP {target_ip}，威胁类型: {detection_result['predicted_class']}",
            execution_data=detection_result
        )
        
        db.add(execution_log)
        db.flush()  # 获取ID
        
        logger.info(f"🚫 自动执行封锁: {target_ip}")
        return execution_log
    
    def _create_auto_proposal(self, db: Session, detection_result: Dict, 
                            target_ip: str) -> Proposal:
        """创建自动提案"""
        proposal = Proposal(
            threat_type=detection_result['predicted_class'],
            confidence=detection_result['confidence'],
            true_label=detection_result['true_label'],
            proposal_type="auto",
            target_ip=target_ip,
            action_type="block",
            detection_data=detection_result
        )
        
        db.add(proposal)
        db.flush()  # 获取ID
        
        logger.info(f"📝 自动创建提案: ID-{proposal.id}, 威胁-{detection_result['predicted_class']}")
        return proposal
    
    def _generate_random_ip(self) -> str:
        """生成随机IP地址"""
        return f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"

class ProposalService:
    """提案管理服务"""
    
    def __init__(self):
        self.web3_manager = get_web3_manager()
    
    def create_manual_proposal(self, db: Session, detection_id: int, 
                             operator_action: str = "block") -> Dict:
        """创建手动提案（Operator操作）"""
        try:
            # 查找检测记录
            detection_log = db.query(ThreatDetectionLog).filter(
                ThreatDetectionLog.id == detection_id
            ).first()
            
            if not detection_log:
                raise ValueError(f"检测记录不存在: {detection_id}")
            
            # 创建提案
            proposal = Proposal(
                threat_type=detection_log.threat_type,
                confidence=detection_log.confidence,
                true_label=detection_log.true_label,
                proposal_type="manual",
                target_ip=detection_log.target_ip,
                action_type=operator_action,
                detection_data=detection_log.detection_data
            )
            
            db.add(proposal)
            db.commit()
            
            # 更新检测日志
            detection_log.proposal_id = proposal.id
            detection_log.action_taken = "manual_proposal_created"
            db.commit()
            
            logger.info(f"📝 手动创建提案: ID-{proposal.id} by Operator")
            
            return {
                "proposal_id": proposal.id,
                "status": "created",
                "message": "提案创建成功，等待Manager签名"
            }
            
        except Exception as e:
            logger.error(f"❌ 手动创建提案失败: {e}")
            db.rollback()
            raise
    
    def sign_proposal(self, db: Session, proposal_id: int, manager_role: str) -> Dict:
        """Manager签名提案"""
        try:
            # 查找提案
            proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
            if not proposal:
                raise ValueError(f"提案不存在: {proposal_id}")
            
            if proposal.status != "pending":
                raise ValueError(f"提案状态不允许签名: {proposal.status}")
            
            # 检查是否已经签名
            signed_by = proposal.signed_by or []
            if manager_role in signed_by:
                raise ValueError(f"Manager {manager_role} 已经签名过此提案")
            
            # 添加签名
            signed_by.append(manager_role)
            proposal.signed_by = signed_by
            proposal.signatures_count = len(signed_by)
            
            # 检查是否达到签名要求
            if proposal.signatures_count >= proposal.signatures_required:
                # 提案通过，执行操作
                result = self._execute_approved_proposal(db, proposal, manager_role)
                proposal.status = "approved"
                proposal.approved_at = datetime.now()
            else:
                result = {
                    "status": "signed",
                    "message": f"签名成功，还需要 {proposal.signatures_required - proposal.signatures_count} 个签名"
                }
            
            db.commit()
            
            logger.info(f"✅ 提案签名成功: ID-{proposal_id} by {manager_role}")
            return result
            
        except Exception as e:
            logger.error(f"❌ 提案签名失败: {e}")
            db.rollback()
            raise
    
    def _execute_approved_proposal(self, db: Session, proposal: Proposal, 
                                 final_signer: str) -> Dict:
        """执行已批准的提案"""
        try:
            # 创建执行日志
            execution_log = ExecutionLog(
                proposal_id=proposal.id,
                action_type=proposal.action_type,
                target_ip=proposal.target_ip,
                threat_type=proposal.threat_type,
                confidence=proposal.confidence,
                execution_status="success",
                execution_details=f"提案批准后执行{proposal.action_type}操作",
                manager_account=self.web3_manager.accounts.get(final_signer, "unknown"),
                execution_data=proposal.detection_data
            )
            
            db.add(execution_log)
            db.flush()
            
            # 发送奖励给最终签名者
            reward_result = self.web3_manager.send_reward("treasury", final_signer)
            
            if reward_result["success"]:
                # 更新提案的奖励信息
                proposal.reward_paid = True
                proposal.reward_recipient = final_signer
                proposal.reward_tx_hash = reward_result["tx_hash"]
                
                # 更新执行日志
                execution_log.reward_tx_hash = reward_result["tx_hash"]
                
                logger.info(f"💰 奖励发送成功: {final_signer} 获得 {INCENTIVE_CONFIG['proposal_reward']} ETH")
            else:
                logger.error(f"❌ 奖励发送失败: {reward_result['error']}")
            
            proposal.executed_at = datetime.now()
            
            return {
                "status": "approved_and_executed",
                "execution_log_id": execution_log.id,
                "reward_paid": reward_result["success"],
                "reward_tx_hash": reward_result.get("tx_hash"),
                "message": "提案已批准并执行，奖励已发送"
            }
            
        except Exception as e:
            logger.error(f"❌ 执行提案失败: {e}")
            raise
    
    def get_pending_proposals(self, db: Session) -> List[Dict]:
        """获取待处理提案"""
        proposals = db.query(Proposal).filter(Proposal.status == "pending").order_by(Proposal.created_at.desc()).all()
        return [proposal.to_dict() for proposal in proposals]
    
    def get_proposal_history(self, db: Session, limit: int = 50) -> List[Dict]:
        """获取提案历史"""
        proposals = db.query(Proposal).order_by(Proposal.created_at.desc()).limit(limit).all()
        return [proposal.to_dict() for proposal in proposals]

class SystemInfoService:
    """系统信息服务"""
    
    def __init__(self):
        self.web3_manager = get_web3_manager()
        self.threat_model = get_threat_model()
    
    def get_system_status(self, db: Session) -> Dict:
        """获取系统状态"""
        # 网络信息
        network_info = self.web3_manager.get_network_info()
        
        # 账户信息
        accounts_info = self.web3_manager.get_all_accounts_info()
        
        # 模型信息
        model_info = self.threat_model.get_model_info()
        
        # 数据库统计
        db_stats = self._get_database_stats(db)
        
        return {
            "network": network_info,
            "accounts": accounts_info,
            "ai_model": model_info,
            "database": db_stats,
            "thresholds": THREAT_THRESHOLDS,
            "system_time": datetime.now().isoformat()
        }
    
    def _get_database_stats(self, db: Session) -> Dict:
        """获取数据库统计信息"""
        return {
            "total_detections": db.query(ThreatDetectionLog).count(),
            "total_proposals": db.query(Proposal).count(),
            "pending_proposals": db.query(Proposal).filter(Proposal.status == "pending").count(),
            "total_executions": db.query(ExecutionLog).count()
        }