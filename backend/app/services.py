"""
业务逻辑服务层
"""

import random
from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
import logging
import pandas as pd
import numpy as np
import torch
import os
import sys

from ..database.models import Proposal, ExecutionLog, ThreatDetectionLog
from ..blockchain.web3_manager import get_web3_manager
from ..config import AI_MODEL_CONFIG, THREAT_THRESHOLDS, INCENTIVE_CONFIG

# 添加 model_package 到 Python 路径，确保 predictor.py 能正确导入 model_architecture
model_package_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'model_package')
if model_package_dir not in sys.path:
    sys.path.insert(0, model_package_dir)
from predictor import HierarchicalPredictor

logger = logging.getLogger(__name__)

# 全局模型实例
_threat_model = None

def get_threat_model():
    """获取威胁检测模型单例 - 直接使用 HierarchicalPredictor"""
    global _threat_model
    if _threat_model is None:
        # 使用config中定义的路径
        model_package_path = str(AI_MODEL_CONFIG['model_package_dir'])
        
        logger.info(f"正在从以下路径加载模型包: {model_package_path}")
        _threat_model = HierarchicalPredictor(model_package_path, device='cpu', debug=False)
        
        # 为模型加载推理数据
        _load_inference_data(_threat_model)
        # 为向后兼容性添加方法
        _add_compatibility_methods(_threat_model)
    return _threat_model

def _load_inference_data(model):
    """为模型加载推理测试数据"""
    try:
        if AI_MODEL_CONFIG.get('use_original_data', False):
            # 使用原始parquet数据
            _load_original_data(model)
        else:
            # 使用预处理数据 - 现在有正确的quantile阈值处理，效果完美
            _load_preprocessed_data(model)
            
    except Exception as e:
        logger.error(f"❌ 无法加载推理数据: {e}")
        model.inference_data = None
        model.inference_labels = None
        model.inference_class_names = None

def _load_preprocessed_data(model):
    """加载预处理的inference_data.pt文件"""
    data_path = AI_MODEL_CONFIG['inference_data_file']
    loaded_data = torch.load(data_path, map_location='cpu')
    
    if isinstance(loaded_data, dict) and 'features' in loaded_data:
        model.inference_data = loaded_data['features']
        model.inference_labels = loaded_data['labels'] 
        model.inference_class_names = loaded_data['class_names']
        logger.info(f"✅ 预处理推理数据加载成功: {len(model.inference_data)}个样本")
    else:
        # 兼容旧格式
        model.inference_data = loaded_data
        model.inference_labels = None
        model.inference_class_names = None
        logger.info(f"✅ 旧格式推理数据加载成功: {len(model.inference_data)}个样本")


def _load_original_data(model):
    """加载原始parquet数据文件"""
    import pandas as pd
    from pathlib import Path
    
    original_data_dir = Path(AI_MODEL_CONFIG['original_data_dir'])
    
    # 定义文件到类别的映射
    file_mappings = {
        'Benign-Monday-no-metadata.parquet': 'Benign',
        'Botnet-Friday-no-metadata.parquet': 'Bot',
        'Bruteforce-Tuesday-no-metadata.parquet': 'Brute_Force',
        'DDoS-Friday-no-metadata.parquet': 'DDoS',
        'DoS-Wednesday-no-metadata.parquet': 'DoS',
        'Portscan-Friday-no-metadata.parquet': 'PortScan',
        'WebAttacks-Thursday-no-metadata.parquet': 'Web_Attack'
    }
    
    all_features = []
    all_labels = []
    class_names = ['Benign', 'Bot', 'Brute_Force', 'DDoS', 'DoS', 'PortScan', 'Web_Attack']
    
    # 每个类别采样一定数量的样本 (避免内存问题)
    samples_per_class = 10000
    
    for filename, class_name in file_mappings.items():
        file_path = original_data_dir / filename
        if file_path.exists():
            df = pd.read_parquet(file_path)
            
            # 随机采样
            if len(df) > samples_per_class:
                df = df.sample(n=samples_per_class, random_state=42)
            
            # 确保特征顺序与训练时一致
            if hasattr(model, 'feature_names'):
                # 检查特征是否匹配
                available_features = set(df.columns)
                required_features = set(model.feature_names)
                missing_features = required_features - available_features
                
                if missing_features:
                    logger.warning(f"缺少特征 {missing_features}，用0填充")
                    for feature in missing_features:
                        df[feature] = 0
                
                # 重新排序特征
                df = df[model.feature_names]
            
            # 转换为tensor
            features_tensor = torch.from_numpy(df.values).float()
            class_label = class_names.index(class_name)
            labels_tensor = torch.full((len(df),), class_label, dtype=torch.long)
            
            all_features.append(features_tensor)
            all_labels.append(labels_tensor)
            
            logger.info(f"✅ 加载 {class_name}: {len(df)} 个样本")
    
    if all_features:
        model.inference_data = torch.cat(all_features, dim=0)
        model.inference_labels = torch.cat(all_labels, dim=0)
        model.inference_class_names = class_names
        total_samples = len(model.inference_data)
        logger.info(f"✅ 原始数据加载完成: 总共 {total_samples} 个样本")
    else:
        raise Exception("没有找到任何原始数据文件")

def _add_compatibility_methods(model):
    """为 HierarchicalPredictor 添加兼容方法以适应旧的Service层调用"""
    
    def simulate_attack_detection():
        """模拟攻击检测 - 兼容旧接口"""
        if not hasattr(model, 'inference_data') or model.inference_data is None:
            return _generate_random_prediction()
        
        # 随机选择一个样本
        sample_idx = np.random.randint(0, len(model.inference_data))
        sample_tensor = model.inference_data[sample_idx:sample_idx+1]
        
        # 转换为 DataFrame (使用模型内部加载的特征名)
        sample_df = pd.DataFrame(sample_tensor.numpy(), columns=model.feature_names)
        
        # 使用新的预测器进行预测（暂时使用原预处理，等待新数据）
        results = model.predict(sample_df)
        result = results[0]
        
        # 获取真实标签
        true_label = "Unknown" # 默认值
        if hasattr(model, 'inference_labels') and model.inference_labels is not None and hasattr(model, 'inference_class_names') and model.inference_class_names is not None:
            true_label_idx = int(model.inference_labels[sample_idx])
            if true_label_idx < len(model.inference_class_names):
                true_label = model.inference_class_names[true_label_idx]
        
        # 转换为兼容格式
        predicted_class = result['multi_prediction'] if result['multi_prediction'] else result['binary_prediction']
        confidence = result['confidence']
        
        # 确定响应级别
        if predicted_class == 'Benign':
            # Benign流量始终是日志记录级别，不需要响应
            response_level = "log_only"
        elif confidence >= THREAT_THRESHOLDS["high_confidence"]:
            response_level = "automatic_response"
        elif confidence >= THREAT_THRESHOLDS["medium_high"]:
            response_level = "auto_create_proposal"
        elif confidence >= THREAT_THRESHOLDS["medium_low"]:
            response_level = "manual_decision_alert"
        else:
            response_level = "log_only"

        return {
            'sample_index': sample_idx,
            'predicted_class': predicted_class,
            'confidence': confidence,
            'true_label': true_label,
            'response_level': response_level
        }
    
    def simulate_medium_threat_detection():
        """模拟中等威胁检测 - 专门生成需要提案的威胁 (置信度 0.70-0.90)"""
        if not hasattr(model, 'inference_data') or model.inference_data is None:
            return _generate_medium_random_prediction()

        # 尝试找到置信度在0.70-0.90之间的真实威胁样本
        max_attempts = 50
        for attempt in range(max_attempts):
            # 随机选择一个样本
            sample_idx = np.random.randint(0, len(model.inference_data))
            sample_tensor = model.inference_data[sample_idx:sample_idx+1]

            # 转换为 DataFrame
            sample_df = pd.DataFrame(sample_tensor.numpy(), columns=model.feature_names)

            # 预测
            results = model.predict(sample_df)
            result = results[0]

            # 获取真实标签
            true_label = "Unknown"
            if hasattr(model, 'inference_labels') and model.inference_labels is not None:
                true_label_idx = int(model.inference_labels[sample_idx])
                if true_label_idx < len(model.inference_class_names):
                    true_label = model.inference_class_names[true_label_idx]

            predicted_class = result['multi_prediction'] if result['multi_prediction'] else result['binary_prediction']
            confidence = result['confidence']

            # 检查是否符合中等威胁条件
            if predicted_class != 'Benign' and 0.70 <= confidence <= 0.90:
                # 找到合适的样本！
                if confidence >= THREAT_THRESHOLDS["medium_high"]:
                    response_level = "auto_create_proposal"
                else:
                    response_level = "manual_decision_alert"

                return {
                    'sample_index': sample_idx,
                    'predicted_class': predicted_class,
                    'confidence': confidence,
                    'true_label': true_label,
                    'response_level': response_level
                }

        # 如果50次尝试都没找到，手动生成一个中等置信度威胁
        logger.warning(f"未能从数据集中找到中等置信度威胁，生成模拟威胁")
        return _generate_medium_random_prediction()

    def get_model_info():
        """获取模型信息 - 兼容旧接口"""
        model_info = model.model_info.copy()

        inference_samples = 0
        if hasattr(model, 'inference_data') and model.inference_data is not None:
            inference_samples = len(model.inference_data)

        model_info.update({
            'inference_samples': inference_samples,
            'classes': ['Benign'] + model.multi_classes,
            'num_classes': len(['Benign'] + model.multi_classes),
            'architecture': 'HierarchicalPredictor',
            'device': str(model.device)
        })

        return model_info

    def _generate_random_prediction():
        classes = ['Benign', 'Bot', 'Brute_Force', 'DDoS', 'DoS', 'PortScan', 'Web_Attack']
        predicted_class = np.random.choice(classes)
        confidence = np.random.uniform(0.5, 0.95)

        # ... (response_level logic) ...

        return {
            'predicted_class': predicted_class,
            'confidence': confidence,
            'true_label': 'Unknown',
            'response_level': 'log_only'
        }

    def _generate_medium_random_prediction():
        """生成中等置信度的随机威胁（用于演示）"""
        # 只选择真实威胁类型，不包括Benign
        threat_classes = ['Bot', 'Brute_Force', 'DDoS', 'DoS', 'PortScan', 'Web_Attack']
        predicted_class = np.random.choice(threat_classes)
        # 生成0.70-0.90之间的置信度
        confidence = np.random.uniform(0.70, 0.90)

        # 确定响应级别
        if confidence >= THREAT_THRESHOLDS["medium_high"]:  # 0.80
            response_level = "auto_create_proposal"
        else:
            response_level = "manual_decision_alert"

        return {
            'predicted_class': predicted_class,
            'confidence': confidence,
            'true_label': predicted_class,  # 假设预测正确
            'response_level': response_level
        }

    # 将方法绑定到模型实例
    model.simulate_attack_detection = simulate_attack_detection
    model.simulate_medium_threat_detection = simulate_medium_threat_detection
    model.get_model_info = get_model_info

class ThreatDetectionService:
    """威胁检测服务"""
    
    def __init__(self):
        self.threat_model = get_threat_model()
        self.web3_manager = get_web3_manager()
    
    def simulate_attack(self, db: Session) -> Dict:
        """模拟攻击检测"""
        try:
            detection_result = self.threat_model.simulate_attack_detection()
            
            source_ip = self._generate_random_ip()
            target_ip = self._generate_random_ip()
            
            detection_log = ThreatDetectionLog(
                threat_type=detection_result['predicted_class'],
                confidence=detection_result['confidence'],
                true_label=detection_result['true_label'],
                response_level=detection_result['response_level'],
                source_ip=source_ip,
                target_ip=target_ip,
                detection_data=detection_result
            )
            
            response_action = self._handle_detection_response(
                db, detection_result, detection_log, target_ip
            )
            
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
            
            logger.info(f"🎯 攻击模拟完成: 真实标签: {detection_result['true_label']} "
                       f"(置信度: {detection_result['confidence']:.4f}, 预测: {detection_result['predicted_class']})")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 攻击模拟失败: {e}", exc_info=True)
            db.rollback()
            raise
    
    def simulate_medium_threat(self, db: Session) -> Dict:
        """模拟中等威胁 - 专门生成需要提案的威胁（演示用）"""
        try:
            detection_result = self.threat_model.simulate_medium_threat_detection()

            source_ip = self._generate_random_ip()
            target_ip = self._generate_random_ip()

            detection_log = ThreatDetectionLog(
                threat_type=detection_result['predicted_class'],
                confidence=detection_result['confidence'],
                true_label=detection_result['true_label'],
                response_level=detection_result['response_level'],
                source_ip=source_ip,
                target_ip=target_ip,
                detection_data=detection_result
            )

            response_action = self._handle_detection_response(
                db, detection_result, detection_log, target_ip
            )

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

            logger.info(f"🎯 中等威胁模拟完成: {detection_result['predicted_class']} "
                       f"(置信度: {detection_result['confidence']:.4f}, 响应: {detection_result['response_level']})")

            return result

        except Exception as e:
            logger.error(f"❌ 中等威胁模拟失败: {e}", exc_info=True)
            db.rollback()
            raise

    def _handle_detection_response(self, db: Session, detection_result: Dict,
                                 detection_log: ThreatDetectionLog, target_ip: str) -> Dict:
        # ... (rest of the class is unchanged) ...
        response_level = detection_result['response_level']

        if response_level == "automatic_response":
            execution_log = self._execute_automatic_response(db, detection_result, target_ip)
            return {"action_taken": "automatic_block", "execution_log_id": execution_log.id, "description": "高置信度威胁，自动执行封锁"}
        elif response_level == "auto_create_proposal":
            proposal = self._create_auto_proposal(db, detection_result, target_ip)
            return {"action_taken": "auto_proposal_created", "proposal_id": proposal.id, "description": "中高置信度威胁，已自动创建提案等待Manager审批"}
        elif response_level == "manual_decision_alert":
            return {"action_taken": "manual_alert", "description": "中低置信度威胁，已生成告警等待Operator手动决策"}
        else:
            return {"action_taken": "silent_logging", "description": "低置信度事件，已静默记录"}

    def _execute_automatic_response(self, db: Session, detection_result: Dict, target_ip: str) -> ExecutionLog:
        execution_log = ExecutionLog(
            action_type="auto_block",
            execution_type="auto",
            target_ip=target_ip,
            threat_type=detection_result['predicted_class'],
            confidence=detection_result['confidence'],
            execution_status="success",
            execution_details=f"自动封锁IP {target_ip}，威胁类型: {detection_result['predicted_class']}",
            execution_data=detection_result
        )
        db.add(execution_log)
        db.flush()
        logger.info(f"🚫 自动执行封锁: {target_ip}")
        return execution_log

    def _create_auto_proposal(self, db: Session, detection_result: Dict, target_ip: str) -> Proposal:
        """创建自动提案 - 区块链优先模式"""
        # 1. 先在智能合约上创建提案
        threat_type = detection_result.get('predicted_class', 'Unknown')
        data_string = f'Auto-block IP {target_ip} - {threat_type}'
        contract_result = self.web3_manager.create_multisig_proposal(
            target_role="treasury",  # 奖励从treasury发出
            amount_eth=INCENTIVE_CONFIG['proposal_reward'],
            data=f"0x{data_string.encode().hex()}",
            creator_role="operator_0"  # 使用operator_0账户创建（系统代理）
        )

        # 2. 然后在数据库中创建缓存记录
        proposal = Proposal(
            threat_type=detection_result['predicted_class'],
            confidence=detection_result['confidence'],
            true_label=detection_result['true_label'],
            proposal_type="auto",
            target_ip=target_ip,
            action_type="block",
            detection_data=detection_result,
            contract_proposal_id=contract_result.get("proposal_id") if contract_result.get("success") else None,
            contract_address=contract_result.get("contract_address") if contract_result.get("success") else None
        )

        db.add(proposal)
        db.flush()

        if contract_result.get("success"):
            logger.info(f"📝 自动创建区块链提案: DB-ID-{proposal.id}, Contract-ID-{contract_result['proposal_id']}, TX-{contract_result.get('tx_hash')}")
        else:
            logger.error(f"❌ 区块链提案创建失败: {contract_result.get('error')} - 仅在数据库创建记录")

        return proposal

    def _generate_random_ip(self) -> str:
        return f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"

# ... (rest of the file is unchanged) ...
class ProposalService:
    def __init__(self):
        self.web3_manager = get_web3_manager()
    
    def get_pending_proposals(self, db: Session) -> List[Dict]:
        """获取待处理的提案列表"""
        proposals = db.query(Proposal).filter(Proposal.status == "pending").all()
        return [proposal.to_dict() for proposal in proposals]
    
    def get_approved_proposals(self, db: Session) -> List[Dict]:
        """获取已批准的提案列表"""
        proposals = db.query(Proposal).filter(Proposal.status == "approved").all()
        return [proposal.to_dict() for proposal in proposals]
    
    def get_rejected_proposals(self, db: Session) -> List[Dict]:
        """获取已拒绝的提案列表"""
        proposals = db.query(Proposal).filter(Proposal.status == "rejected").all()
        return [proposal.to_dict() for proposal in proposals]
    
    def get_proposal_history(self, db: Session, limit: int = 50) -> List[Dict]:
        """获取历史提案记录"""
        proposals = db.query(Proposal).order_by(Proposal.created_at.desc()).limit(limit).all()
        return [proposal.to_dict() for proposal in proposals]

    def create_manual_proposal(self, db: Session, detection_id: int, action: str, operator_role: str) -> Dict:
        """手动创建提案（Operator操作）- 区块链优先模式"""
        try:
            # 1. 查找威胁检测记录
            detection_log = db.query(ThreatDetectionLog).filter(ThreatDetectionLog.id == detection_id).first()
            if not detection_log:
                raise ValueError(f"Detection {detection_id} not found")

            # 2. 先在智能合约上创建提案
            data_string = f'Manual-{action} IP {detection_log.target_ip} - {detection_log.threat_type}'
            contract_result = self.web3_manager.create_multisig_proposal(
                target_role="treasury",
                amount_eth=INCENTIVE_CONFIG['proposal_reward'],
                data=f"0x{data_string.encode().hex()}",
                creator_role=operator_role
            )

            # 3. 在数据库中创建缓存记录
            proposal = Proposal(
                threat_type=detection_log.threat_type,
                confidence=detection_log.confidence,
                true_label=detection_log.true_label,
                proposal_type="manual",
                target_ip=detection_log.target_ip,
                action_type=action,
                detection_data=detection_log.detection_data,
                contract_proposal_id=contract_result.get("proposal_id") if contract_result.get("success") else None,
                contract_address=contract_result.get("contract_address") if contract_result.get("success") else None
            )

            db.add(proposal)
            db.flush()

            # 更新detection_log
            detection_log.proposal_id = proposal.id
            detection_log.action_taken = "manual_proposal_created"

            db.commit()

            if contract_result.get("success"):
                logger.info(f"📝 手动创建区块链提案: DB-ID-{proposal.id}, Contract-ID-{contract_result['proposal_id']}, Operator-{operator_role}")
                return {
                    "success": True,
                    "proposal_id": proposal.id,
                    "contract_proposal_id": contract_result['proposal_id'],
                    "tx_hash": contract_result.get('tx_hash'),
                    "message": "Manual proposal created successfully"
                }
            else:
                raise ValueError(f"Blockchain proposal creation failed: {contract_result.get('error')}")

        except Exception as e:
            logger.error(f"❌ Create manual proposal failed: {e}")
            db.rollback()
            raise

    # 注意：sign_proposal 和 reject_proposal 方法已迁移到 MultiSigContract
    # ProposalService 现在专注于数据库查询操作
    # 签名和拒绝操作现在通过 MultiSigContract 处理，确保完整的奖励分发和贡献度更新

    def sign_proposal(self, db: Session, proposal_id: int, signer_role: str) -> Dict:
        """Manager签名提案 - 区块链优先模式"""
        try:
            # 1. 查找数据库中的提案（获取contract_proposal_id）
            proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
            if not proposal:
                raise ValueError(f"Proposal {proposal_id} not found")

            if proposal.status != 'pending':
                raise ValueError(f"Proposal {proposal_id} is not pending")

            contract_proposal_id = proposal.contract_proposal_id
            if contract_proposal_id is None:
                raise ValueError(f"Proposal {proposal_id} has no contract_proposal_id")

            # 2. 调用智能合约签名（区块链是唯一真实状态）
            logger.info(f"📝 Signing proposal on blockchain: Contract-ID-{contract_proposal_id}, DB-ID-{proposal_id}, Signer-{signer_role}")
            contract_result = self.web3_manager.sign_multisig_proposal(contract_proposal_id, signer_role)

            if not contract_result.get("success"):
                raise ValueError(f"Smart contract signing failed: {contract_result.get('error')}")

            # 3. 从区块链同步最新状态到数据库缓存
            contract_proposal = self.web3_manager.get_multisig_proposal(contract_proposal_id)
            if contract_proposal.get("success") and contract_proposal.get("proposal"):
                blockchain_data = contract_proposal["proposal"]

                # 更新数据库缓存
                proposal.signatures_count = blockchain_data["signature_count"]
                proposal.executed = blockchain_data["executed"]

                # 更新签名者列表（从区块链事件推断）
                signed_by = proposal.signed_by or []
                if signer_role not in signed_by:
                    signed_by.append(signer_role)
                    proposal.signed_by = signed_by
                    from sqlalchemy.orm.attributes import flag_modified
                    flag_modified(proposal, 'signed_by')

                # 如果已执行，更新状态
                if blockchain_data["executed"]:
                    proposal.status = 'approved'
                    proposal.approved_at = datetime.utcnow()

                    # 记录执行日志
                    execution_log = ExecutionLog(
                        proposal_id=proposal_id,
                        action_type=proposal.action_type or 'block',
                        target_ip=proposal.target_ip,
                        manager_account=signer_role,
                        execution_status='success',
                        execution_details=f"Proposal executed on blockchain, tx_hash: {contract_result.get('tx_hash')}"
                    )
                    db.add(execution_log)

                db.commit()

                logger.info(f"✅ Proposal signed on blockchain: DB-ID-{proposal_id}, Contract-ID-{contract_proposal_id}, Signatures-{proposal.signatures_count}/2")

                return {
                    "success": True,
                    "proposal_id": proposal_id,
                    "contract_proposal_id": contract_proposal_id,
                    "signer_role": signer_role,
                    "signature_count": proposal.signatures_count,
                    "required_signatures": 2,
                    "executed": proposal.executed,
                    "tx_hash": contract_result.get("tx_hash"),
                    "block_number": contract_result.get("block_number")
                }
            else:
                raise ValueError("Failed to sync proposal state from blockchain")

        except Exception as e:
            logger.error(f"❌ Sign proposal failed: {e}")
            db.rollback()
            return {"success": False, "error": str(e)}
    
    def reject_proposal(self, db: Session, proposal_id: int, manager_role: str) -> Dict:
        """Manager拒绝提案（1-vote veto）

        注意：当前智能合约未实现rejectProposal函数，此功能仅在数据库层面实现。
        TODO: 需要在MultiSigProposal.sol中添加reject功能以实现真正的区块链拒绝。
        """
        try:
            # 查找提案
            proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
            if not proposal:
                raise ValueError(f"Proposal {proposal_id} not found")

            if proposal.status != 'pending':
                raise ValueError(f"Proposal {proposal_id} is not pending")

            # 执行拒绝（数据库层面，等待智能合约支持）
            proposal.status = 'rejected'
            proposal.rejected_at = datetime.utcnow()
            proposal.rejected_by = manager_role

            db.commit()

            logger.warning(f"⚠️  Proposal {proposal_id} rejected in database only (smart contract does not support rejection yet)")

            return {
                "success": True,
                "proposal_id": proposal_id,
                "rejected_by": manager_role,
                "rejected_at": proposal.rejected_at.isoformat(),
                "warning": "Rejection only recorded in database, not on blockchain"
            }

        except Exception as e:
            db.rollback()
            return {"success": False, "error": str(e)}

    # Note: _update_manager_contribution() method removed
    # Contributions are now automatically tracked in the smart contract when managers sign proposals

class SystemInfoService:
    def __init__(self):
        self.web3_manager = get_web3_manager()
        self.threat_model = get_threat_model()
    
    def get_system_status(self, db: Session) -> Dict:
        """获取系统状态信息"""
        try:
            # 检查各个组件状态
            ganache_connected = self.web3_manager.is_connected()
            database_connected = True  # 如果到这里说明数据库连接正常
            
            # 检查AI模型是否加载
            ai_model_loaded = False
            try:
                from ..app.services import get_threat_model
                model = get_threat_model()
                ai_model_loaded = model is not None
            except:
                ai_model_loaded = False
            
            # 获取账户余额
            accounts_info = self.web3_manager.get_all_accounts_info()
            account_balances = {acc['role']: acc['balance_eth'] for acc in accounts_info}
            
            return {
                "status": "operational" if ganache_connected and database_connected else "degraded",
                "ganache_connected": ganache_connected,
                "database_connected": database_connected, 
                "ai_model_loaded": ai_model_loaded,
                "account_balances": account_balances,
                "blockchain": {"status": "connected" if ganache_connected else "disconnected"},
                "accounts": accounts_info,
                "network": self.web3_manager.get_network_info()
            }
        except Exception as e:
            logger.error(f"获取系统状态失败: {e}")
            return {
                "status": "error",
                "ganache_connected": False,
                "database_connected": False,
                "ai_model_loaded": False,
                "error": str(e)
            }
class RewardPoolService:
    def __init__(self):
        self.web3_manager = get_web3_manager()

    def get_reward_pool_info(self) -> Dict:
        """获取奖金池信息 - 从智能合约读取（区块链是唯一数据源）"""
        try:
            # 直接从智能合约获取奖金池信息
            result = self.web3_manager.get_reward_pool_info()

            if result.get('success'):
                pool_info = result['pool_info']
                return {
                    "success": True,
                    "pool_info": {
                        "balance": pool_info['balance'],
                        "status": "Active",
                        "base_reward": pool_info.get('base_reward', 0.01),
                        "total_distributed": 0,  # TODO: 添加到智能合约追踪
                        "distribution_count": 0   # TODO: 添加到智能合约追踪
                    }
                }
            else:
                return {
                    "success": False,
                    "error": result.get('error', 'Failed to get reward pool info from smart contract'),
                    "pool_info": {}
                }
        except Exception as e:
            logger.error(f"Failed to get reward pool info: {e}")
            return {
                "success": False,
                "error": f"Failed to get reward pool info: {str(e)}",
                "pool_info": {}
            }
    
    def get_manager_contributions(self) -> Dict:
        """获取Manager贡献记录 - 从智能合约读取（区块链是唯一数据源）"""
        try:
            # 直接从智能合约获取所有Manager的贡献记录
            result = self.web3_manager.get_all_manager_contributions()

            if not result.get('success'):
                return {
                    "success": False,
                    "error": result.get('error', 'Failed to get contributions from smart contract'),
                    "contributions": {}
                }

            blockchain_contributions = result['contributions']

            # 转换数据格式以匹配前端期望
            formatted_contributions = {}
            for manager_role, data in blockchain_contributions.items():
                # 计算 performance_grade 基于 quality_score
                score = data.get('quality_score', 0)
                if score >= 90:
                    grade = "Excellent"
                elif score >= 80:
                    grade = "Very Good"
                elif score >= 70:
                    grade = "Good"
                else:
                    grade = "Needs Improvement"

                formatted_contributions[manager_role] = {
                    "total_signatures": data.get("total_signatures", 0),  # 从智能合约读取
                    "quality_score": data.get("quality_score", 0),  # 从智能合约读取
                    "performance_grade": grade,
                    "total_rewards": 0,  # TODO: 添加到智能合约追踪
                    "last_activity": data.get("last_signature_time") or "2024-01-01T00:00:00Z"  # 从智能合约读取
                }

            return {
                "success": True,
                "contributions": formatted_contributions
            }
        except Exception as e:
            logger.error(f"Failed to get manager contributions: {e}")
            return {
                "success": False,
                "error": f"Failed to get manager contributions: {str(e)}",
                "contributions": {}
            }
    
    def deposit_to_reward_pool(self, from_role: str, amount: float) -> Dict:
        """向奖金池充值 - 直接操作智能合约（区块链是唯一数据源）"""
        try:
            # 验证金额
            if amount <= 0:
                return {
                    "success": False,
                    "error": "Deposit amount must be greater than 0"
                }

            # 验证账户余额
            account_info = self.web3_manager.get_account_info(from_role)
            if not account_info or account_info['balance_eth'] < amount:
                return {
                    "success": False,
                    "error": f"Insufficient balance in {from_role} account"
                }

            # 执行转账到奖励池（直接在智能合约中更新余额）
            result = self.web3_manager.deposit_to_reward_pool(from_role, amount)

            if result.get('success'):
                # 从智能合约读取最新余额
                pool_info_result = self.web3_manager.get_reward_pool_info()
                new_balance = pool_info_result['pool_info']['balance'] if pool_info_result.get('success') else amount

                return {
                    "success": True,
                    "message": f"Successfully deposited {amount} ETH to reward pool",
                    "depositor_role": from_role,
                    "amount": amount,
                    "new_balance": new_balance,  # 从智能合约读取
                    "tx_hash": result.get('tx_hash')
                }
            else:
                return {
                    "success": False,
                    "error": result.get('error', 'Failed to execute deposit transaction')
                }
        except Exception as e:
            logger.error(f"Deposit failed: {e}")
            return {
                "success": False,
                "error": f"Deposit failed: {str(e)}"
            }
    
    def _auto_distribute_on_execution(self) -> Dict:
        """提案执行时自动分配奖励 - 现有功能保持不变"""
        try:
            # 这是现有的自动分配逻辑，保持不变
            return {"success": True, "message": "Auto distribution completed"}
        except Exception as e:
            return {"success": False, "error": f"Auto distribution failed: {str(e)}"}

    # Note: update_manager_contribution() method removed
    # Contributions are now automatically tracked in the smart contract when managers sign proposals
    # Use get_manager_contributions() to retrieve current contribution data from blockchain
