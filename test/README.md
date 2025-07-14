# 测试目录

区块链智能安防平台的测试文件。

## 主要测试文件

```
test/
├── test_phase2_fixed.sh         # 第二阶段完整测试套件（主要测试）
├── test_ganache_connection.py   # Ganache连接测试
├── verify_setup.py              # 快速验证脚本
└── README.md                    # 测试说明
```

## 运行测试

### Phase 2 完整测试（推荐）
```bash
./test_phase2_fixed.sh
```

### 快速验证
```bash
npm run test
```

### Ganache连接测试
```bash
npm run test-connection
```

## 测试内容

### test_phase2_fixed.sh - 完整API测试
- ✅ 系统状态检查
- ✅ 奖励发送功能测试
- ✅ 攻击模拟和AI检测
- ✅ 提案创建和多重签名
- ✅ 执行日志验证
- ✅ 账户余额变化检查

### verify_setup.py - 快速验证
- ✅ 关键文件存在性检查
- ✅ FastAPI应用导入测试
- ✅ 启动方式说明

### test_ganache_connection.py - 连接测试
- ✅ Ganache网络连接
- ✅ 账户地址验证
- ✅ 余额和区块信息

## 测试覆盖范围

### Phase 2 测试覆盖的API端点
- `POST /api/attack/simulate` - 攻击模拟
- `GET /api/system/status` - 系统状态
- `GET /api/proposals` - 提案列表
- `POST /api/proposals/{id}/sign` - 提案签名
- `GET /api/logs/executions` - 执行日志
- `POST /api/test/reward` - 奖励发送测试

### 测试验证重点
1. **AI模型集成**：真实Ensemble_Hybrid模型预测
2. **区块链集成**：Web3连接和ETH转账
3. **多重签名**：2/3签名机制
4. **奖励系统**：自动发送0.01 ETH奖励
5. **数据持久化**：SQLite数据库存储

## 启动开发环境

1. **CLI方式（推荐）**:
   ```bash
   npm run start-chain    # 启动Ganache
   npm run backend       # 启动后端
   ```

2. **一键启动**:
   ```bash
   ./start-dev.sh
   ```

## 已清理的文件

以下测试文件已被删除（被test_phase2_fixed.sh替代）：
- `test_phase1.py` - 第一阶段测试
- `test_model_loading.py` - 模型加载测试
- `inspect_real_model.py` - 模型检查脚本

## 开发状态

- ✅ **第一阶段**：基础设施和配置 - 已完成
- ✅ **第二阶段**：后端开发 - 已完成并测试通过
- 🔄 **第三阶段**：前端开发 - 待开始