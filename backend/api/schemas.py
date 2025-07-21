"""
API 标准化请求和响应模型
"""
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime


# ================== 基础响应模型 ==================

class APIResponse(BaseModel):
    """标准API响应基类"""
    success: bool = Field(..., description="操作是否成功")
    message: str = Field(..., description="响应消息")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")


class APISuccessResponse(APIResponse):
    """成功响应模型"""
    success: bool = Field(True, description="操作成功")
    data: Any = Field(..., description="响应数据")


class APIErrorResponse(APIResponse):
    """错误响应模型"""
    success: bool = Field(False, description="操作失败")
    error_code: str = Field(..., description="错误代码")
    details: Optional[Dict[str, Any]] = Field(None, description="错误详情")


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(..., description="服务状态")
    message: str = Field(..., description="状态消息")
    timestamp: datetime = Field(default_factory=datetime.now, description="检查时间")


# ================== 攻击模拟相关模型 ==================

class ThreatInfo(BaseModel):
    """威胁信息模型"""
    predicted_class: str = Field(..., description="预测的威胁类型")
    confidence: float = Field(..., ge=0, le=1, description="置信度（0-1）")
    true_label: str = Field(..., description="真实标签")
    response_level: str = Field(..., description="响应级别")


class NetworkInfo(BaseModel):
    """网络信息模型"""
    source_ip: str = Field(..., description="源IP地址")
    target_ip: str = Field(..., description="目标IP地址")


class ResponseAction(BaseModel):
    """响应动作模型"""
    action_taken: str = Field(..., description="采取的动作")
    description: str = Field(..., description="动作描述")
    proposal_id: Optional[int] = Field(None, description="关联提案ID")
    execution_log_id: Optional[int] = Field(None, description="执行日志ID")


class AttackSimulationResult(BaseModel):
    """攻击模拟结果模型"""
    detection_id: int = Field(..., description="检测ID")
    threat_info: ThreatInfo = Field(..., description="威胁信息")
    network_info: NetworkInfo = Field(..., description="网络信息")
    response_action: ResponseAction = Field(..., description="响应动作")
    timestamp: str = Field(..., description="检测时间")


# ================== 系统状态相关模型 ==================

class NetworkStatus(BaseModel):
    """网络状态模型"""
    chain_id: int = Field(..., description="链ID")
    block_number: int = Field(..., description="区块高度")
    gas_price: int = Field(..., description="Gas价格")
    is_connected: bool = Field(..., description="是否连接")
    rpc_url: str = Field(..., description="RPC URL")


class AccountInfo(BaseModel):
    """账户信息模型"""
    role: str = Field(..., description="账户角色")
    address: str = Field(..., description="账户地址")
    balance_wei: int = Field(..., description="余额（Wei）")
    balance_eth: float = Field(..., description="余额（ETH）")
    nonce: int = Field(..., description="nonce值")


class AIModelInfo(BaseModel):
    """AI模型信息模型"""
    model_info: Dict[str, Any] = Field(..., description="模型详细信息")
    feature_count: int = Field(..., description="特征数量")
    threat_classes: List[str] = Field(..., description="威胁类别列表")
    thresholds: Dict[str, float] = Field(..., description="置信度阈值")
    inference_samples: int = Field(..., description="推理样本数")


class DatabaseStats(BaseModel):
    """数据库统计模型"""
    total_detections: int = Field(..., description="总检测数")
    total_proposals: int = Field(..., description="总提案数")
    pending_proposals: int = Field(..., description="待处理提案数")
    total_executions: int = Field(..., description="总执行数")


class SystemStatus(BaseModel):
    """系统状态模型"""
    network: NetworkStatus = Field(..., description="网络状态")
    accounts: List[AccountInfo] = Field(..., description="账户列表")
    ai_model: AIModelInfo = Field(..., description="AI模型信息")
    database: DatabaseStats = Field(..., description="数据库统计")
    thresholds: Dict[str, float] = Field(..., description="系统阈值")
    system_time: str = Field(..., description="系统时间")


# ================== 提案相关模型 ==================

class CreateProposalRequest(BaseModel):
    """创建提案请求模型"""
    detection_id: int = Field(..., description="检测ID", gt=0)
    action: str = Field("block", description="建议动作")
    operator_role: Optional[str] = Field(None, description="操作员角色")


class SignProposalRequest(BaseModel):
    """签名提案请求模型"""
    manager_role: str = Field(..., description="管理员角色", pattern=r"^manager_[0-2]$")


class ProposalInfo(BaseModel):
    """提案信息模型"""
    id: int = Field(..., description="提案ID")
    threat_type: str = Field(..., description="威胁类型")
    confidence: float = Field(..., description="置信度")
    proposal_type: str = Field(..., description="提案类型")
    status: str = Field(..., description="提案状态")
    target_ip: str = Field(..., description="目标IP")
    action_type: str = Field(..., description="动作类型")
    signatures_required: int = Field(..., description="需要签名数")
    signatures_count: int = Field(..., description="已签名数")
    signed_by: List[str] = Field(..., description="签名者列表")
    created_at: str = Field(..., description="创建时间")
    approved_at: Optional[str] = Field(None, description="批准时间")
    executed_at: Optional[str] = Field(None, description="执行时间")


class ProposalStats(BaseModel):
    """提案统计模型"""
    total: int = Field(..., description="总提案数")
    pending: int = Field(..., description="待处理数")
    approved: int = Field(..., description="已批准数")
    rejected: int = Field(..., description="已拒绝数")


class ProposalListResponse(BaseModel):
    """提案列表响应模型"""
    pending: List[ProposalInfo] = Field(..., description="待处理提案")
    stats: ProposalStats = Field(..., description="提案统计")


class SignProposalResult(BaseModel):
    """提案签名结果模型"""
    status: str = Field(..., description="签名状态")
    message: str = Field(..., description="状态消息")
    execution_log_id: Optional[int] = Field(None, description="执行日志ID")
    reward_paid: Optional[bool] = Field(None, description="是否支付奖励")
    reward_tx_hash: Optional[str] = Field(None, description="奖励交易哈希")
    auto_distributed: Optional[bool] = Field(None, description="是否自动分配")
    distribution_amount: Optional[float] = Field(None, description="分配金额")


# ================== 奖励池相关模型 ==================

class RewardPoolInfo(BaseModel):
    """奖励池信息模型"""
    balance: float = Field(..., description="奖励池余额（ETH）")
    balance_wei: int = Field(..., description="奖励池余额（Wei）")
    base_reward: float = Field(..., description="基础奖励（ETH）")
    base_reward_wei: int = Field(..., description="基础奖励（Wei）")
    treasury_balance: float = Field(..., description="财务余额（ETH）")
    treasury_address: str = Field(..., description="财务地址")
    last_updated: str = Field(..., description="最后更新时间")


class ManagerContribution(BaseModel):
    """管理员贡献模型"""
    address: str = Field(..., description="管理员地址")
    total_signatures: int = Field(..., description="总签名次数")
    avg_response_time: float = Field(..., description="平均响应时间")
    quality_score: int = Field(..., description="质量评分")
    last_signature_time: str = Field(..., description="最后签名时间")
    performance_grade: str = Field(..., description="性能等级")


class DepositRequest(BaseModel):
    """充值请求模型"""
    from_role: str = Field(..., description="充值来源角色")
    amount_eth: float = Field(..., description="充值金额（ETH）", gt=0)


class TestRewardRequest(BaseModel):
    """测试奖励请求模型"""
    from_role: str = Field(..., description="发送方角色")
    to_role: str = Field(..., description="接收方角色")
    amount_eth: float = Field(..., description="奖励金额（ETH）", gt=0)


class FundAccountRequest(BaseModel):
    """账户充值请求模型"""
    to_address: str = Field(..., description="目标地址", pattern=r"^0x[a-fA-F0-9]{40}$")
    amount: float = Field(1.0, description="充值金额（ETH）", gt=0)


# ================== 日志相关模型 ==================

class DetectionLogInfo(BaseModel):
    """检测日志信息模型"""
    id: int = Field(..., description="日志ID")
    threat_type: str = Field(..., description="威胁类型")
    confidence: float = Field(..., description="置信度")
    true_label: str = Field(..., description="真实标签")
    response_level: str = Field(..., description="响应级别")
    source_ip: str = Field(..., description="源IP")
    target_ip: str = Field(..., description="目标IP")
    action_taken: Optional[str] = Field(None, description="采取的动作")
    detected_at: str = Field(..., description="检测时间")


class ExecutionLogInfo(BaseModel):
    """执行日志信息模型"""
    id: int = Field(..., description="日志ID")
    action_type: str = Field(..., description="动作类型")
    target_ip: str = Field(..., description="目标IP")
    threat_type: str = Field(..., description="威胁类型")
    confidence: float = Field(..., description="置信度")
    execution_status: str = Field(..., description="执行状态")
    execution_details: str = Field(..., description="执行详情")
    reward_tx_hash: Optional[str] = Field(None, description="奖励交易哈希")
    executed_at: str = Field(..., description="执行时间")


# ================== 网络拓扑相关模型 ==================

class NetworkNode(BaseModel):
    """网络节点模型"""
    id: str = Field(..., description="节点ID")
    name: str = Field(..., description="节点名称")
    type: str = Field(..., description="节点类型")
    status: str = Field(..., description="节点状态")
    ip_address: str = Field(..., description="IP地址")
    connections: List[str] = Field(..., description="连接的节点ID列表")


class CreateNetworkNodeRequest(BaseModel):
    """创建网络节点请求模型"""
    name: str = Field(..., description="节点名称", min_length=1, max_length=50)
    type: str = Field(..., description="节点类型")
    ip_address: str = Field(..., description="IP地址")
    connections: List[str] = Field([], description="连接的节点ID列表")


class AttackFlowRequest(BaseModel):
    """攻击流请求模型"""
    source_node_id: str = Field(..., description="源节点ID")
    target_node_id: str = Field(..., description="目标节点ID")
    attack_type: str = Field(..., description="攻击类型")