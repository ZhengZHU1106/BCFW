"""
区块链智能安防平台 - FastAPI 主应用
"""
import logging
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import ValidationError

from backend.database.connection import init_database, get_db
from backend.blockchain.web3_manager import init_web3_manager
from backend.ai_module.model_loader import init_threat_model
from backend.app.services import ThreatDetectionService, ProposalService, SystemInfoService, RewardPoolService

# 导入标准化模块
from backend.api.schemas import *
from backend.api.exceptions import *
from backend.api.responses import success_response, create_health_response

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    logger.info("🚀 启动区块链智能安防平台...")
    
    try:
        # 初始化数据库
        logger.info("📊 初始化数据库...")
        init_database()
        
        # 初始化Web3管理器
        logger.info("🔗 初始化Web3连接...")
        init_web3_manager()
        
        # 初始化AI模型
        logger.info("🤖 初始化AI模型...")
        init_threat_model()
        
        # 初始化奖金池
        logger.info("💰 初始化奖金池...")
        try:
            from backend.app.services import RewardPoolService
            reward_pool_service = RewardPoolService()
            
            # 检查奖金池当前余额
            pool_info = reward_pool_service.get_reward_pool_info()
            if pool_info["success"] and pool_info["pool_info"]["balance"] < 50.0:
                # 如果奖金池余额低于50 ETH，则充值到100 ETH
                needed_amount = 100.0 - pool_info["pool_info"]["balance"]
                deposit_result = reward_pool_service.deposit_to_reward_pool("treasury", needed_amount)
                if deposit_result["success"]:
                    logger.info(f"✅ 奖金池初始化成功: 充值 {needed_amount} ETH，当前余额 100 ETH")
                else:
                    logger.error(f"❌ 奖金池初始化失败: {deposit_result.get('error')}")
            else:
                logger.info(f"✅ 奖金池已有足够余额: {pool_info['pool_info']['balance']} ETH")
        except Exception as e:
            logger.error(f"❌ 奖金池初始化异常: {e}")
        
        logger.info("✅ 系统初始化完成！")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ 系统初始化失败: {e}")
        raise
    
    # 关闭时清理
    logger.info("🛑 关闭系统...")

app = FastAPI(
    title="区块链智能安防平台",
    description="基于AI威胁检测和区块链多重签名的安防平台演示原型",
    version="1.0.0",
    lifespan=lifespan
)

# 添加异常处理器
app.add_exception_handler(APIException, api_exception_handler)
app.add_exception_handler(ValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境允许所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化服务
threat_service = ThreatDetectionService()
proposal_service = ProposalService()
system_service = SystemInfoService()
reward_pool_service = RewardPoolService()

@app.get("/", response_model=dict, tags=["系统"])
async def root():
    """根路径，返回API状态信息"""
    return success_response(
        data={
            "version": "1.0.0",
            "docs": "/docs",
            "endpoints": {
                "simulate_attack": "/api/v1/attack/simulate",
                "system_status": "/api/v1/system/status",
                "proposals": "/api/v1/proposals",
                "network_topology": "/api/v1/network/topology",
                "health": "/health"
            }
        },
        message="区块链智能安防平台 API"
    )

@app.get("/health", response_model=HealthResponse, tags=["系统"])
async def health_check():
    """健康检查端点"""
    return create_health_response()

# API路由

# ================== 威胁检测相关API ==================

@app.post("/api/v1/attack/simulate", response_model=dict, tags=["威胁检测"])
async def simulate_attack(db: Session = Depends(get_db)):
    """模拟攻击检测
    
    执行AI威胁检测模拟，自动生成攻击场景并进行分析，
    根据置信度自动决定响应策略（自动响应、创建提案或人工决策）。
    """
    try:
        result = threat_service.simulate_attack(db)
        return success_response(
            data=result,
            message="攻击模拟执行成功"
        )
    except Exception as e:
        logger.error(f"攻击模拟失败: {e}")
        raise SystemException(f"攻击模拟执行失败: {str(e)}")

# ================== 系统状态相关API ==================

@app.get("/api/v1/system/status", response_model=dict, tags=["系统状态"])
async def get_system_status(db: Session = Depends(get_db)):
    """获取系统状态
    
    返回系统的完整运行状态，包括：
    - 网络连接状态和区块链信息
    - 所有账户余额和状态
    - AI模型配置和性能指标
    - 数据库统计信息
    """
    try:
        status = system_service.get_system_status(db)
        return success_response(
            data=status,
            message="系统状态获取成功"
        )
    except Exception as e:
        logger.error(f"获取系统状态失败: {e}")
        raise SystemException(f"获取系统状态失败: {str(e)}")

# ================== 提案管理相关API ==================

@app.get("/api/v1/proposals", response_model=dict, tags=["提案管理"])
async def get_proposals(
    status_filter: Optional[str] = Query(None, description="状态过滤器：pending/approved/rejected"),
    limit: int = Query(50, description="返回数量限制", ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取提案列表
    
    返回系统中的提案信息，支持按状态过滤。
    包含待处理提案和历史提案的完整信息。
    """
    try:
        pending = proposal_service.get_pending_proposals(db)
        history = proposal_service.get_proposal_history(db, limit=limit)
        
        # 统计信息
        stats = {
            "total": len(history),
            "pending": len(pending),
            "approved": len([p for p in history if p.get("status") == "approved"]),
            "rejected": len([p for p in history if p.get("status") == "rejected"])
        }
        
        return success_response(
            data={
                "pending": pending,
                "history": history,
                "stats": stats,
                "latest_pending_id": pending[0]["id"] if pending else None
            },
            message="提案列表获取成功"
        )
    except Exception as e:
        logger.error(f"获取提案列表失败: {e}")
        raise SystemException(f"获取提案列表失败: {str(e)}")


@app.post("/api/v1/proposals/{proposal_id}/sign", response_model=dict, tags=["提案管理"])
async def sign_proposal(
    proposal_id: int,
    manager_role: str = Query(..., description="管理员角色", regex=r"^manager_[0-2]$"),
    db: Session = Depends(get_db)
):
    """Manager签名提案
    
    允许授权的Manager对指定提案进行签名。
    当达到2/3签名阈值时，提案将自动执行并分发奖励。
    """
    try:
        # 验证manager_role
        valid_managers = ["manager_0", "manager_1", "manager_2"]
        validate_role(manager_role, valid_managers)
        
        result = proposal_service.sign_proposal(db, proposal_id, manager_role)
        return success_response(
            data=result,
            message="提案签名成功"
        )
    except ValueError as e:
        raise BusinessException(str(e))
    except Exception as e:
        logger.error(f"提案签名失败: {e}")
        raise SystemException(f"提案签名失败: {str(e)}")


@app.post("/api/v1/proposals/create", response_model=dict, tags=["提案管理"])
async def create_manual_proposal(
    request: CreateProposalRequest,
    db: Session = Depends(get_db)
):
    """创建手动提案（Operator操作）
    
    允许Operator基于检测记录手动创建安全响应提案。
    提案创建后将等待Manager签名批准。
    """
    try:
        result = proposal_service.create_manual_proposal(
            db, 
            request.detection_id, 
            request.action, 
            request.operator_role
        )
        return success_response(
            data=result,
            message="手动提案创建成功"
        )
    except ValueError as e:
        raise BusinessException(str(e))
    except Exception as e:
        logger.error(f"创建手动提案失败: {e}")
        raise SystemException(f"创建手动提案失败: {str(e)}")

# ================== 日志查询相关API ==================

@app.get("/api/v1/logs/detections", response_model=dict, tags=["日志查询"])
async def get_detection_logs(
    limit: int = Query(50, description="返回数量限制", ge=1, le=200),
    db: Session = Depends(get_db)
):
    """获取威胁检测日志
    
    返回AI威胁检测的历史记录，包括检测时间、威胁类型、
    置信度、响应级别和采取的行动等详细信息。
    """
    try:
        from backend.database.models import ThreatDetectionLog
        
        logs = db.query(ThreatDetectionLog).order_by(
            ThreatDetectionLog.detected_at.desc()
        ).limit(limit).all()
        
        return success_response(
            data=[log.to_dict() for log in logs],
            message="检测日志获取成功"
        )
    except Exception as e:
        logger.error(f"获取检测日志失败: {e}")
        raise SystemException(f"获取检测日志失败: {str(e)}")


@app.get("/api/v1/logs/executions", response_model=dict, tags=["日志查询"])
async def get_execution_logs(
    limit: int = Query(50, description="返回数量限制", ge=1, le=200),
    db: Session = Depends(get_db)
):
    """获取执行日志
    
    返回安全响应执行的历史记录，包括执行状态、
    目标IP、采取的动作和奖励分配等信息。
    """
    try:
        from backend.database.models import ExecutionLog
        
        logs = db.query(ExecutionLog).order_by(
            ExecutionLog.executed_at.desc()
        ).limit(limit).all()
        
        return success_response(
            data=[log.to_dict() for log in logs],
            message="执行日志获取成功"
        )
    except Exception as e:
        logger.error(f"获取执行日志失败: {e}")
        raise SystemException(f"获取执行日志失败: {str(e)}")

# ================== 账户管理相关API ==================

@app.post("/api/v1/accounts/fund", response_model=dict, tags=["账户管理"])
async def fund_account(request: FundAccountRequest):
    """从Treasury账户向新账户转账
    
    为指定的以太坊地址从Treasury账户转账，
    用于账户初始化和资金分配。
    """
    try:
        from backend.blockchain.web3_manager import get_web3_manager
        web3_manager = get_web3_manager()
        
        # 验证地址格式
        validate_ethereum_address(request.to_address)
        validate_positive_number(request.amount, "转账金额")
        
        # 检查Treasury余额
        treasury_info = web3_manager.get_account_info('treasury')
        if treasury_info['balance_eth'] < request.amount:
            raise BusinessException("Treasury账户余额不足")
        
        # 执行转账
        treasury_account = treasury_info['address']
        treasury_private_key = web3_manager.accounts['treasury']['private_key']
        
        # 构建交易
        nonce = web3_manager.w3.eth.get_transaction_count(treasury_account)
        transaction = {
            'nonce': nonce,
            'to': request.to_address,
            'value': web3_manager.w3.to_wei(request.amount, 'ether'),
            'gas': 21000,
            'gasPrice': web3_manager.w3.to_wei('1', 'gwei')
        }
        
        # 签名并发送交易
        signed_txn = web3_manager.w3.eth.account.sign_transaction(
            transaction, 
            private_key=treasury_private_key
        )
        tx_hash = web3_manager.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        
        # 等待交易确认
        receipt = web3_manager.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        # 获取新余额
        new_balance = web3_manager.w3.eth.get_balance(request.to_address)
        
        return success_response(
            data={
                "transaction_hash": tx_hash.hex(),
                "from_address": treasury_account,
                "to_address": request.to_address,
                "amount": request.amount,
                "new_balance": float(web3_manager.w3.from_wei(new_balance, 'ether'))
            },
            message=f"成功向 {request.to_address} 转账 {request.amount} ETH"
        )
    except Exception as e:
        logger.error(f"账户资金转账失败: {e}")
        raise SystemException(f"账户资金转账失败: {str(e)}")

# ================== 测试相关API ==================

@app.post("/api/v1/test/reward", response_model=dict, tags=["测试功能"])
async def test_reward_sending(request: TestRewardRequest):
    """测试奖励发送功能
    
    用于测试区块链奖励发送机制，验证账户间的ETH转账功能。
    主要用于开发和调试阶段。
    """
    try:
        web3_manager = system_service.web3_manager
        
        # 验证角色
        all_roles = ["treasury", "manager_0", "manager_1", "manager_2"] + [f"operator_{i}" for i in range(6)]
        validate_role(request.from_role, all_roles)
        validate_role(request.to_role, all_roles)
        
        # 检查账户余额
        from_balance = web3_manager.get_account_info(request.from_role)["balance_eth"]
        to_balance_before = web3_manager.get_account_info(request.to_role)["balance_eth"]
        
        if from_balance < request.amount_eth:
            raise BusinessException(f"{request.from_role}账户余额不足")
        
        # 发送测试奖励
        result = web3_manager.send_reward(request.from_role, request.to_role, request.amount_eth)
        
        # 检查发送后余额
        to_balance_after = web3_manager.get_account_info(request.to_role)["balance_eth"]
        
        return success_response(
            data={
                "reward_result": result,
                "balance_changes": {
                    "from_role": request.from_role,
                    "to_role": request.to_role,
                    "amount": request.amount_eth,
                    "to_balance_before": to_balance_before,
                    "to_balance_after": to_balance_after,
                    "balance_increase": to_balance_after - to_balance_before
                }
            },
            message="奖励发送测试完成"
        )
    except Exception as e:
        logger.error(f"奖励发送测试失败: {e}")
        raise SystemException(f"奖励发送测试失败: {str(e)}")

# ================== 奖励池管理相关API ==================

@app.get("/api/v1/reward-pool/info", response_model=dict, tags=["奖励池管理"])
async def get_reward_pool_info():
    """获取奖金池信息
    
    返回奖励池的详细信息，包括余额、基础奖励额度、
    Treasury余额等关键数据。
    """
    try:
        result = reward_pool_service.get_reward_pool_info()
        if result["success"]:
            return success_response(
                data=result.get("pool_info", {}),
                message="奖金池信息获取成功"
            )
        else:
            raise SystemException(result.get("error", "获取奖金池信息失败"))
    except Exception as e:
        logger.error(f"获取奖金池信息失败: {e}")
        raise SystemException(f"获取奖金池信息失败: {str(e)}")


@app.get("/api/v1/reward-pool/contributions", response_model=dict, tags=["奖励池管理"])
async def get_manager_contributions():
    """获取Manager贡献记录
    
    返回所有Manager的详细贡献信息，包括签名次数、
    响应时间、质量评分和性能等级。
    """
    try:
        result = reward_pool_service.get_manager_contributions()
        if result["success"]:
            return success_response(
                data=result.get("contributions", {}),
                message="Manager贡献记录获取成功"
            )
        else:
            raise SystemException(result.get("error", "获取Manager贡献记录失败"))
    except Exception as e:
        logger.error(f"获取Manager贡献记录失败: {e}")
        raise SystemException(f"获取Manager贡献记录失败: {str(e)}")


@app.post("/api/v1/reward-pool/deposit", response_model=dict, tags=["奖励池管理"])
async def deposit_to_reward_pool(request: DepositRequest):
    """向奖金池充值
    
    允许从指定角色账户向奖励池充值ETH，
    用于维持奖励池的资金充足。
    """
    try:
        # 验证充值角色
        valid_roles = ["treasury", "manager_0", "manager_1", "manager_2"]
        validate_role(request.from_role, valid_roles)
        validate_positive_number(request.amount_eth, "充值金额")
        
        result = reward_pool_service.deposit_to_reward_pool(request.from_role, request.amount_eth)
        
        if result["success"]:
            return success_response(
                data={
                    "depositor_role": result.get("depositor_role"),
                    "amount": result.get("amount"),
                    "new_balance": result.get("new_balance"),
                    "tx_hash": result.get("tx_hash")
                },
                message=result.get("message", "奖金池充值成功")
            )
        else:
            raise BusinessException(result.get("error", "奖金池充值失败"))
    except Exception as e:
        logger.error(f"奖金池充值失败: {e}")
        raise SystemException(f"奖金池充值失败: {str(e)}")


@app.post("/api/v1/test/auto-distribute", response_model=dict, tags=["测试功能"])
async def test_auto_distribute():
    """测试自动分配机制
    
    手动触发一次奖励自动分配流程，
    用于测试基于贡献度的奖励分配算法。
    """
    try:
        result = reward_pool_service._auto_distribute_on_execution()
        return success_response(
            data=result,
            message="自动分配测试完成"
        )
    except Exception as e:
        logger.error(f"自动分配测试失败: {e}")
        raise SystemException(f"自动分配测试失败: {str(e)}")

# ================== 网络拓扑相关API (简化版) ==================

@app.get("/api/v1/network/topology", response_model=dict, tags=["网络拓扑"])
async def get_network_topology():
    """获取网络拓扑信息
    
    返回简化的网络拓扑结构，主要展示系统中的
    关键网络节点和连接关系。
    """
    try:
        # 简化的网络拓扑信息
        topology = {
            "nodes": [
                {"id": "blockchain", "name": "Ganache Blockchain", "type": "blockchain", "status": "active"},
                {"id": "ai_engine", "name": "AI Detection Engine", "type": "ai_service", "status": "active"},
                {"id": "api_server", "name": "API Server", "type": "backend", "status": "active"},
                {"id": "frontend", "name": "Web Frontend", "type": "frontend", "status": "active"}
            ],
            "connections": [
                {"from": "frontend", "to": "api_server", "type": "http"},
                {"from": "api_server", "to": "blockchain", "type": "web3"},
                {"from": "api_server", "to": "ai_engine", "type": "internal"}
            ],
            "stats": {
                "total_nodes": 4,
                "active_connections": 3,
                "network_status": "healthy"
            }
        }
        
        return success_response(
            data=topology,
            message="网络拓扑信息获取成功"
        )
    except Exception as e:
        logger.error(f"获取网络拓扑失败: {e}")
        raise SystemException(f"获取网络拓扑失败: {str(e)}")



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
