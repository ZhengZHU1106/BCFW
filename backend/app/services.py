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
            
            # 记录检测日志 - 使用true_label因为模型还有问题
            detection_log = ThreatDetectionLog(
                threat_type=detection_result['true_label'],
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
            
            logger.info(f"🎯 攻击模拟完成: {detection_result['true_label']} "
                       f"(置信度: {detection_result['confidence']:.4f}, 预测: {detection_result['predicted_class']})")
            
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
        """创建自动提案 (使用MultiSig合约)"""
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
        
        # 使用MultiSig合约创建提案（系统自动创建，不需要角色验证）
        multisig_result = self.web3_manager.create_multisig_proposal(
            target_role="manager_0",  # 奖励目标（这里可以动态确定）
            amount_eth=INCENTIVE_CONFIG['proposal_reward'],
            data="0x",
            creator_role="system"  # 系统自动创建
        )
        
        if multisig_result["success"]:
            # 更新提案的合约相关信息
            proposal.contract_proposal_id = multisig_result["proposal_id"]
            proposal.contract_address = multisig_result["contract_address"]
            
            logger.info(f"📝 自动创建MultiSig提案: DB-ID-{proposal.id}, Contract-ID-{multisig_result['proposal_id']}")
        else:
            logger.error(f"❌ MultiSig提案创建失败: {multisig_result['error']}")
            # 继续使用传统模式
            proposal.contract_proposal_id = None
        
        return proposal
    
    def _generate_random_ip(self) -> str:
        """生成随机IP地址"""
        return f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"

class ProposalService:
    """提案管理服务"""
    
    def __init__(self):
        self.web3_manager = get_web3_manager()
    
    def create_manual_proposal(self, db: Session, detection_id: int, 
                             operator_action: str = "block", operator_role: str = None) -> Dict:
        """创建手动提案（Operator操作） - 现在使用角色验证"""
        try:
            # 角色验证将由合约层处理，这里只记录操作者
            if operator_role:
                # 可以添加简单的角色格式验证
                if not (operator_role.startswith("operator_") or operator_role.startswith("manager_")):
                    raise ValueError(f"无效的角色格式: {operator_role}")
            
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
            db.flush()  # 获取ID
            
            # 使用MultiSig合约创建提案（如果提供了角色）
            if operator_role:
                multisig_result = self.web3_manager.create_multisig_proposal(
                    target_role="manager_0",  # 奖励目标
                    amount_eth=INCENTIVE_CONFIG['proposal_reward'],
                    data="0x",
                    creator_role=operator_role
                )
                
                if multisig_result["success"]:
                    proposal.contract_proposal_id = multisig_result["proposal_id"]
                    proposal.contract_address = multisig_result["contract_address"]
                    logger.info(f"📝 手动创建MultiSig提案: DB-ID-{proposal.id}, Contract-ID-{multisig_result['proposal_id']}, Creator-{operator_role}")
                else:
                    logger.error(f"❌ MultiSig提案创建失败: {multisig_result['error']}")
            
            db.commit()
            
            # 更新检测日志
            detection_log.proposal_id = proposal.id
            detection_log.action_taken = "manual_proposal_created"
            db.commit()
            
            logger.info(f"📝 手动创建提案: ID-{proposal.id} by {operator_role or 'Operator'}")
            
            return {
                "proposal_id": proposal.id,
                "status": "created",
                "message": "提案创建成功，等待Manager签名",
                "creator_role": operator_role,
                "contract_proposal_id": proposal.contract_proposal_id
            }
            
        except Exception as e:
            logger.error(f"❌ 手动创建提案失败: {e}")
            db.rollback()
            raise
    
    def sign_proposal(self, db: Session, proposal_id: int, manager_role: str) -> Dict:
        """Manager签名提案 (使用MultiSig合约) - 现在使用角色验证"""
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
            
            # 使用MultiSig合约签名（如果有合约提案ID）
            multisig_result = None
            if proposal.contract_proposal_id:
                multisig_result = self.web3_manager.sign_multisig_proposal(
                    proposal.contract_proposal_id, 
                    manager_role
                )
                
                if multisig_result["success"]:
                    logger.info(f"✅ MultiSig合约签名成功: Contract-ID-{proposal.contract_proposal_id} by {manager_role}")
                else:
                    logger.error(f"❌ MultiSig合约签名失败: {multisig_result['error']}")
                    # 如果合约签名失败，可能是角色权限问题
                    if "not authorized" in multisig_result.get("error", "").lower():
                        raise ValueError(f"Manager {manager_role} 没有权限签名此提案")
            
            # 更新传统签名信息（向后兼容）
            signed_by.append(manager_role)
            proposal.signed_by = signed_by
            proposal.signatures_count = len(signed_by)
            
            # 检查是否达到签名要求
            if proposal.signatures_count >= proposal.signatures_required:
                # 提案通过，执行操作
                result = self._execute_approved_proposal(db, proposal, manager_role)
                proposal.status = "approved"
                proposal.approved_at = datetime.now()
                
                # 如果使用了MultiSig合约且执行成功
                if multisig_result and multisig_result.get("executed"):
                    result["multisig_executed"] = True
                    result["multisig_result"] = multisig_result.get("execution_result")
            else:
                result = {
                    "status": "signed",
                    "message": f"签名成功，还需要 {proposal.signatures_required - proposal.signatures_count} 个签名",
                    "multisig_signed": multisig_result is not None and multisig_result["success"]
                }
            
            db.commit()
            
            logger.info(f"✅ 提案签名成功: DB-ID-{proposal_id} by {manager_role}")
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
            
            # 准备返回结果
            result = {
                "status": "approved_and_executed",
                "execution_log_id": execution_log.id,
                "reward_paid": reward_result["success"],
                "reward_tx_hash": reward_result.get("tx_hash"),
                "message": "提案已批准并执行，奖励已发送",
                "auto_distributed": False,
                "distribution_amount": 0
            }
            
            # 自动触发基于贡献度的奖励分配
            try:
                # 使用当前实例直接调用（这里的self是ProposalService实例）
                # 需要获取RewardPoolService实例
                reward_pool_service = RewardPoolService()
                auto_distribution = reward_pool_service._auto_distribute_on_execution()
                
                if auto_distribution.get("success"):
                    distributions = auto_distribution.get("distributions", [])
                    if distributions:
                        logger.info(f"💰 自动分配奖励完成: 分配给 {len(distributions)} 个Manager")
                        # 在返回结果中包含自动分配信息
                        result["auto_distributed"] = True
                        result["distribution_amount"] = auto_distribution.get("total_distributed", 0)
                        result["distributions"] = distributions
                    else:
                        logger.info("💰 自动分配奖励: 暂无符合条件的Manager")
                else:
                    logger.warning(f"💰 自动分配奖励未触发: {auto_distribution.get('message')}")
                    
            except Exception as e:
                logger.error(f"❌ 自动分配奖励失败: {e}")
            
            return result
            
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
    
    def withdraw_proposal(self, db: Session, proposal_id: int, operator_role: str) -> Dict:
        """撤回提案（仅Operator可撤回自己创建的pending提案）"""
        try:
            # 查找提案
            proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
            if not proposal:
                raise ValueError(f"Proposal not found: {proposal_id}")
            
            # 检查提案状态
            if proposal.status != "pending":
                raise ValueError(f"Cannot withdraw proposal with status: {proposal.status}")
            
            # 验证操作者角色
            if not operator_role or not operator_role.startswith("operator_"):
                raise ValueError("Only operators can withdraw proposals")
            
            # 更新提案状态
            proposal.status = "withdrawn"
            proposal.withdrawn_at = datetime.now()
            proposal.withdrawn_by = operator_role
            
            db.commit()
            
            logger.info(f"📤 Proposal withdrawn: ID-{proposal_id} by {operator_role}")
            
            return {
                "status": "withdrawn",
                "message": "Proposal withdrawn successfully",
                "proposal_id": proposal_id,
                "withdrawn_by": operator_role
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to withdraw proposal: {e}")
            db.rollback()
            raise

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

class RewardPoolService:
    """奖金池管理服务"""
    
    def __init__(self):
        self.web3_manager = get_web3_manager()
    
    def deposit_to_reward_pool(self, from_role: str, amount_eth: float) -> Dict:
        """向奖金池充值"""
        try:
            result = self.web3_manager.deposit_to_reward_pool(from_role, amount_eth)
            
            if result["success"]:
                logger.info(f"💰 奖金池充值成功: {amount_eth} ETH from {from_role}")
                return {
                    "success": True,
                    "message": f"Successfully deposited {amount_eth} ETH to reward pool",
                    "depositor_role": from_role,
                    "amount": amount_eth,
                    "new_balance": result.get("new_balance", 0),
                    "tx_hash": result.get("tx_hash")
                }
            else:
                logger.error(f"❌ 奖金池充值失败: {result['error']}")
                return {
                    "success": False,
                    "error": result["error"],
                    "message": "Failed to deposit to reward pool"
                }
        
        except Exception as e:
            logger.error(f"❌ 奖金池充值异常: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Exception during reward pool deposit"
            }
    
    def get_reward_pool_info(self) -> Dict:
        """获取奖金池信息"""
        try:
            result = self.web3_manager.get_reward_pool_info()
            
            if result["success"]:
                pool_info = result["pool_info"]
                return {
                    "success": True,
                    "pool_info": {
                        "balance": pool_info["balance"],
                        "balance_wei": pool_info["balance_wei"],
                        "base_reward": pool_info["base_reward"],
                        "base_reward_wei": pool_info["base_reward_wei"],
                        "treasury_balance": pool_info.get("treasury_balance", 0),
                        "treasury_address": pool_info.get("treasury_address"),
                        "last_updated": pool_info.get("last_updated")
                    }
                }
            else:
                return {
                    "success": False,
                    "error": result["error"],
                    "pool_info": {
                        "balance": 0,
                        "base_reward": 0.01
                    }
                }
        
        except Exception as e:
            logger.error(f"❌ 获取奖金池信息失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "pool_info": {
                    "balance": 0,
                    "base_reward": 0.01
                }
            }
    
    def get_manager_contributions(self) -> Dict:
        """获取所有Manager贡献记录"""
        try:
            result = self.web3_manager.get_all_manager_contributions()
            
            if result["success"]:
                contributions = result["contributions"]
                
                # 格式化贡献数据
                formatted_contributions = {}
                for manager_role, contrib_data in contributions.items():
                    formatted_contributions[manager_role] = {
                        "address": contrib_data["address"],
                        "total_signatures": contrib_data["total_signatures"],
                        "avg_response_time": contrib_data["avg_response_time"],
                        "quality_score": contrib_data["quality_score"],
                        "last_signature_time": contrib_data["last_signature_time"],
                        "performance_grade": self._calculate_performance_grade(contrib_data)
                    }
                
                return {
                    "success": True,
                    "contributions": formatted_contributions
                }
            else:
                return {
                    "success": False,
                    "error": result["error"],
                    "contributions": {}
                }
        
        except Exception as e:
            logger.error(f"❌ 获取Manager贡献记录失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "contributions": {}
            }
    
    def distribute_contribution_rewards(self, admin_role: str = "manager_0") -> Dict:
        """分配基于贡献度的奖励"""
        try:
            result = self.web3_manager.distribute_contribution_rewards(admin_role)
            
            if result["success"]:
                distributions = result.get("distributions", [])
                total_distributed = result.get("total_distributed", 0)
                
                logger.info(f"🎁 贡献奖励分配完成: 总计 {total_distributed} ETH 分配给 {len(distributions)} 位Manager")
                
                return {
                    "success": True,
                    "message": f"Successfully distributed {total_distributed} ETH to {len(distributions)} managers",
                    "distributions": distributions,
                    "total_distributed": total_distributed,
                    "remaining_pool": result.get("remaining_pool", 0),
                    "distributed_at": result.get("distributed_at")
                }
            else:
                logger.error(f"❌ 贡献奖励分配失败: {result['error']}")
                return {
                    "success": False,
                    "error": result["error"],
                    "message": "Failed to distribute contribution rewards"
                }
        
        except Exception as e:
            logger.error(f"❌ 贡献奖励分配异常: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Exception during reward distribution"
            }
    
    def get_reward_pool_dashboard(self) -> Dict:
        """获取奖金池仪表板数据"""
        try:
            # 获取奖金池信息
            pool_result = self.get_reward_pool_info()
            
            # 获取Manager贡献信息
            contrib_result = self.get_manager_contributions()
            
            # 计算统计数据
            total_signatures = 0
            active_managers = 0
            
            if contrib_result["success"]:
                for manager_data in contrib_result["contributions"].values():
                    total_signatures += manager_data["total_signatures"]
                    if manager_data["total_signatures"] > 0:
                        active_managers += 1
            
            dashboard_data = {
                "pool_info": pool_result.get("pool_info", {}),
                "contributions": contrib_result.get("contributions", {}),
                "statistics": {
                    "total_signatures": total_signatures,
                    "active_managers": active_managers,
                    "total_managers": 3,
                    "pool_utilization": self._calculate_pool_utilization(pool_result.get("pool_info", {}))
                },
                "last_updated": datetime.now().isoformat()
            }
            
            return {
                "success": True,
                "dashboard": dashboard_data
            }
        
        except Exception as e:
            logger.error(f"❌ 获取奖金池仪表板失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "dashboard": {}
            }
    
    def _calculate_performance_grade(self, contrib_data: Dict) -> str:
        """计算Manager性能等级"""
        signatures = contrib_data.get("total_signatures", 0)
        quality_score = contrib_data.get("quality_score", 0)
        
        # 计算综合贡献度（0-100分）
        contribution_score = self._calculate_contribution_score(signatures, quality_score)
        
        if signatures == 0:
            return "No Activity"
        elif contribution_score >= 80:
            return "Excellent"
        elif contribution_score >= 60:
            return "Good"
        elif contribution_score >= 40:
            return "Average"
        else:
            return "Needs Improvement"
    
    def _calculate_contribution_score(self, total_signatures: int, quality_score: int) -> float:
        """计算贡献度评分（0-100分）"""
        # 签名次数得分（10次签名满分，占50%权重）
        signature_score = min(100, total_signatures * 10)
        
        # 综合贡献度：签名次数50% + 质量评分50%
        contribution_score = signature_score * 0.5 + quality_score * 0.5
        
        return contribution_score
    
    def _auto_distribute_on_execution(self) -> Dict:
        """提案执行完成时自动分配奖励"""
        try:
            # 获取所有Manager的贡献度
            contributions_result = self.get_manager_contributions()
            if not contributions_result["success"]:
                return {"success": False, "message": "无法获取Manager贡献信息"}
            
            contributions = contributions_result["contributions"]
            
            # 计算符合条件的Manager（贡献度 > 0）
            eligible_managers = {}
            total_contribution_score = 0
            
            for manager_role, contrib_data in contributions.items():
                signatures = contrib_data.get("total_signatures", 0)
                quality_score = contrib_data.get("quality_score", 0)
                
                if signatures > 0:  # 只有有签名记录的Manager参与分配
                    contribution_score = self._calculate_contribution_score(signatures, quality_score)
                    eligible_managers[manager_role] = contribution_score
                    total_contribution_score += contribution_score
            
            if total_contribution_score == 0:
                return {"success": True, "message": "暂无符合条件的Manager"}
            
            # 检查奖金池余额
            pool_result = self.get_reward_pool_info()
            if not pool_result["success"] or pool_result["pool_info"]["balance"] < 1.0:
                return {"success": False, "message": "奖金池余额不足（需要至少1 ETH）"}
            
            # 分配1 ETH奖励
            distribution_amount = 1.0
            distributions = []
            
            for manager_role, contribution_score in eligible_managers.items():
                reward_amount = (contribution_score / total_contribution_score) * distribution_amount
                
                if reward_amount > 0.001:  # 最小奖励阈值
                    reward_result = self.web3_manager.send_reward('treasury', manager_role, reward_amount)
                    
                    if reward_result["success"]:
                        distributions.append({
                            "manager_role": manager_role,
                            "reward_amount": reward_amount,
                            "contribution_score": contribution_score,
                            "tx_hash": reward_result["tx_hash"]
                        })
            
            # 更新奖金池余额（模拟）
            total_distributed = sum(d["reward_amount"] for d in distributions)
            if hasattr(self.web3_manager, 'multisig_contract') and self.web3_manager.multisig_contract:
                self.web3_manager.multisig_contract.reward_pool_balance -= total_distributed
                # 保存奖金池状态
                self.web3_manager.multisig_contract._save_reward_pool_state()
            
            logger.info(f"🎁 自动分配完成: {len(distributions)}位Manager获得奖励，总计{total_distributed} ETH")
            
            return {
                "success": True,
                "message": f"Successfully distributed {total_distributed} ETH to {len(distributions)} managers",
                "distributions": distributions,
                "total_distributed": total_distributed,
                "distributed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ 自动分配奖励失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _calculate_contribution_score(self, total_signatures: int, quality_score: int) -> float:
        """计算贡献度评分（0-100分）"""
        # 签名次数得分（10次签名满分，占50%权重）
        signature_score = min(100, total_signatures * 10)
        
        # 综合贡献度：签名次数50% + 质量评分50%
        contribution_score = signature_score * 0.5 + quality_score * 0.5
        
        return contribution_score
    
    def _calculate_pool_utilization(self, pool_info: Dict) -> float:
        """计算奖金池利用率"""
        balance = pool_info.get("balance", 0)
        treasury_balance = pool_info.get("treasury_balance", 0)
        
        if treasury_balance > 0:
            return min(100.0, (balance / treasury_balance) * 100)
        return 0.0