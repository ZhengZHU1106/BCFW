# 区块链智能安防平台 (Blockchain Security Platform)

演示原型项目，结合AI威胁检测与区块链多重签名决策机制。

## 项目助记词 (Project Mnemonic)

```
bulk tonight audit hover toddler orange boost twenty biology flower govern soldier
```

## 快速启动 (Quick Start)

### 方式一：自动化CLI方式 (推荐开发使用)

```bash
# 1. 安装依赖
npm install

# 2. 一键启动开发环境
./start-dev.sh
# 或者分步启动
npm run start-chain    # 启动区块链
npm run backend        # 启动后端服务
```

### 方式二：Ganache 桌面端方式

```bash
# 显示桌面端配置信息
npm run start-chain-desktop
```

打开 Ganache 桌面端，创建新工作区，配置：
- **助记词**: `bulk tonight audit hover toddler orange boost twenty biology flower govern soldier`
- **RPC 服务器**: `http://127.0.0.1:8545`
- **区块时间**: 5秒（自动挖矿）

### 账户分配
- **账户 0-2**: Manager 业务账户（多重签名决策者）
- **账户 3**: 系统金库账户（激励支付）

### 测试连接
```bash
npm run test-connection  # 测试Ganache连接
npm run test            # 快速验证
```

## 项目结构

```
BCFW/
├── backend/              # FastAPI 后端应用
│   ├── assets/           # AI模型和数据文件
│   ├── config.py         # 系统配置
│   └── main.py          # 应用入口
├── frontend/            # Vue前端框架（待开发）
├── test/                # 测试文件
├── docs/                # 项目文档
├── scripts/             # 训练脚本
├── start-dev.sh         # 开发环境启动脚本
└── package.json         # 项目配置和npm脚本
```

## 命令参考

```bash
# 测试和验证
npm run test              # 快速验证设置
npm run test-full         # 完整测试
npm run test-connection   # 测试Ganache连接

# 启动服务
npm run start-chain       # 启动Ganache CLI
npm run backend          # 启动后端服务
./start-dev.sh           # 一键启动开发环境

# 配置信息
npm run ganache-info     # 查看Ganache配置
npm run start-chain-desktop  # 桌面端配置说明
```

## 开发状态

**第一阶段：环境与核心配置** ✅ 已完成
- ✅ 项目结构设计和文件整理
- ✅ 基础配置文件创建
- ✅ AI模型文件部署
- ✅ 测试框架建立
- ✅ 验证脚本通过

**第二阶段：后端开发** 🔄 准备开始
- 🔄 Web3 连接到 Ganache
- 🔄 AI 模型加载模块
- 🔄 数据库设计和API实现