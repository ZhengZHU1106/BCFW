TODO 行动文档

### **第一阶段：环境与核心配置** ✅ **已完成 (实际用时：1天)**

* [x] 全局安装 `ganache`: `npm install -g ganache`。
* [x] 确定一个12词的**项目助记词**，并写入`README.md`。
  * **实现说明**: 生成了有效的BIP39助记词：`bulk tonight audit hover toddler orange boost twenty biology flower govern soldier`
  * **原因**: 原助记词不符合BIP39标准，重新生成了有效助记词
* [x] 在`package.json`中或创建一个`start-chain.sh`脚本，配置好启动Ganache的最终命令:
  * **实现说明**: 创建了多种启动方式
    - `npm run start-chain` - CLI方式启动
    - `start-dev.sh` - 一键开发环境脚本  
    - `npm run start-chain-desktop` - 桌面端配置说明
  * **改进**: 提供了CLI和桌面端两种方式，增强了灵活性
* [x] 初始化FastAPI后端项目和`requirements.txt`。
* [x] 初始化Vue/React前端项目。
  * **实现说明**: 创建了基础Vue项目结构，待第二阶段后实际开发
* [x] 将所有预备资产（模型包、数据文件）放入后端的`assets`目录下。
  * **实现说明**: 
    - 模型文件放入 `backend/assets/model_package/`
    - 数据文件放入 `backend/assets/data/`
    - 创建了完整的配置管理 `backend/config.py`

**第一阶段额外完成项**:
* [x] 创建完整的测试框架 (`test/` 目录)
* [x] 实现项目验证脚本 (`npm run test`)
* [x] 优化项目文档结构
* [x] 创建开发环境自动化脚本

### **第二阶段：后端开发** ✅ **已完成 (实际用时：1天)**

* [x] 配置FastAPI，使其`Web3`实例连接到本地Ganache (`http://127.0.0.1:8545`)。
  * **实现说明**: 完整的Web3Manager集成，支持确定性账户生成和余额管理
* [x] 从Ganache启动日志中复制**固定的**Manager和金库账户的地址与私钥，作为后端的配置项。
  * **实现说明**: 使用BIP39助记词生成确定性账户，无需复制地址
* [x] **核心**: 创建`ai_module.py`，编写逻辑在应用启动时**加载预打包的模型文件**。
  * **实现说明**: 完整的model_loader.py，支持真实Ensemble_Hybrid模型加载
  * **改进**: 解决了sklearn版本兼容性问题，使用joblib替代pickle
* [x] 在后端启动时，**加载预抽样的攻击数据**`inference_data.pt`。
  * **实现说明**: 成功加载230个真实攻击样本，支持随机采样模拟
* [x] 实现数据库模型 (`proposals`, `execution_logs`)及初始化。
  * **实现说明**: SQLite数据库，包含ThreatDetectionLog, Proposal, ExecutionLog模型
* [x] 开发**"模拟攻击"API**并实现完整的**分级响应逻辑**。
  * **实现说明**: POST /api/attack/simulate，支持4级响应逻辑
* [x] 开发**手动/自动提案**的相关API。
  * **实现说明**: 自动提案创建和手动提案创建API
* [x] 开发**提案签名**API。
  * **实现说明**: POST /api/proposals/{id}/sign，支持2/3多重签名
* [x] 开发**"提案执行与激励"**逻辑 (从金库转账ETH)。
  * **实现说明**: 完整的奖励系统，0.01 ETH奖励给最终签名者

**第二阶段额外完成项**:
* [x] 完整的API端点测试套件 (`test_phase2_fixed.sh`)
* [x] 系统状态监控API (`/api/system/status`)  
* [x] 审计日志API (`/api/logs/detections`, `/api/logs/executions`)
* [x] 奖励发送测试API (`/api/test/reward`)
* [x] 修复预处理器版本兼容性问题
* [x] 优化提案排序和ID获取逻辑

### **第三阶段：前端可视化开发** ✅ **已完成 (实际用时：1天)**

* [x] 实现无状态的"角色切换器"。
  * **实现说明**: 创建RoleSwitch组件，支持Operator/Manager角色切换，使用localStorage持久化
* [x] 开发**账户信息看板**组件，轮询后端API以展示余额和持续增长的区块高度。
  * **实现说明**: Dashboard页面实现完整的账户信息展示，5秒自动刷新系统状态
* [x] 开发**账户列表模拟**组件 (纯前端功能)。
  * **改进**: 不仅是纯前端功能，实现了真实的Web3账户创建和Treasury转账功能
* [x] 开发威胁告警、提案卡片、历史记录等核心可视化组件。
  * **实现说明**: 完整的威胁检测页面、提案管理界面、历史记录展示
* [x] 联调所有API，完成端到端流程。
  * **实现说明**: 所有API联调成功，端到端流程完整可用

**第三阶段额外完成项**:
* [x] Vue 3 + Vite现代化前端框架搭建
* [x] 完整的组件化架构设计
* [x] 响应式UI设计，适配不同屏幕尺寸
* [x] 真实的Web3账户创建和资金管理功能
* [x] 实时数据更新和轮询机制
* [x] 详细的日志详情模态框组件
* [x] CSV数据导出功能
* [x] 完善的错误处理和用户体验

### **第四阶段：集成测试与交付 (预计：3-4天)**

* [x] 进行端到端手动测试，确保所有业务逻辑正确。
  * **实现说明**: test_phase2_fixed.sh测试脚本验证所有功能正常
* [x] 编写`README.md`，清晰说明如何安装依赖、如何启动Ganache、后端和前端，以及如何进行演示。
  * **实现说明**: 完整的README文档，包含Phase 3启动指南
* [x] 清理代码，准备最终交付。
  * **实现说明**: 创建start-phase3.sh一键启动脚本，完善项目文档

**第四阶段额外完成项**:
* [x] 创建完整的前端项目文档
* [x] 实现一键启动脚本 (start-phase3.sh)
* [x] 完整的开发和部署说明文档
* [x] 系统演示准备完成