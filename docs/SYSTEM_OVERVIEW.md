### 项目总结文稿：区块链智能安防平台 (BCFW)

#### 1. 项目愿景与核心理念
BCFW (Blockchain Firewall) 是一个集成了人工智能（AI）与区块链技术的创新安防演示平台。其核心理念是：利用AI的高效性自动检测网络威胁，同时利用区块链的去中心化、透明和不可篡改特性，对高风险安全响应进行民主化、可审计的决策。项目旨在解决传统安全系统“中心化决策”和“操作不透明”的痛点。

#### 2. 系统架构
系统由四个核心部分组成：
*   **前端 (Frontend)**: 基于 **Vue 3 + Vite** 构建的现代化Web界面，是用户与系统交互的主窗口。
*   **后端 (Backend)**: 基于 **FastAPI (Python)** 构建的高性能API服务，是系统的"大脑"，负责处理业务逻辑、与AI模型和区块链交互。
*   **AI模型 (AI Model)**: 一个预训练的 **PyTorch** 模型 (`HierarchicalTransformerIDS`)，用于分类网络流量，识别DDoS、端口扫描等多种攻击。
*   **区块链 (Blockchain)**: 使用 **DevLeChain** (Geth 1.10.22) 真实的以太坊私有链，运行一个自定义的 **Solidity** 智能合约 (`MultiSigProposal.sol`)，负责处理提案的投票和执行。

**技术演进 (Phase 17完成):**
*   **Phase 1-16**: 使用Ganache模拟器，HD钱包助记词管理账户
*   **Phase 17**: 完成向DevLeChain真实私有链的迁移，Keystore文件管理账户，实现区块链优先架构

#### 3. 完整功能拆解

**3.1. 角色与权限 (Role-Based Access Control)**
系统定义了两种核心角色，其权限由智能合约在链上强制执行：
*   **Operator (操作员)**: 一线监控人员。**只能创建提案**，不能签名。
*   **Manager (管理者)**: 高级决策人员。**只能签名或否决提案**，不能创建。
*   **前端实现**: `RoleSwitch.vue` 组件允许用户在不同角色（如 `operator_0`, `manager_1`）之间切换，UI会根据当前角色动态显示/隐藏相关操作按钮。

**3.2. 核心工作流：从检测到响应**
1.  **威胁检测**: 用户在`Threats`页面点击“Simulate Attack”，后端`ThreatDetectionService`从预置数据中随机抽取一个样本，交由AI模型进行分析。
2.  **分级响应**:
    *   **高置信度 (>90%)**: 后端自动执行响应（模拟），并记录日志。
    *   **中高置信度 (80%-90%)**: 后端自动创建提案，进入多签流程。
    *   **中低置信度 (70%-80%)**: 前端产生告警，等待`Operator`手动为该告警创建提案。
    *   **低置信度 (<70%)**: 静默记录，无前端告警。
3.  **多签审批 (链上)**:
    *   提案需要 **2/3** 的`Manager`签名才能通过。
    *   **一票否决 (1-vote veto)**: 任何一个`Manager`都可以直接否决提案。
    *   **前端实现**: `ProposalCard.vue` 组件根据当前角色和提案状态，显示“Sign”或“Reject”按钮。
4.  **执行与激励**:
    *   一旦签名达到阈值，提案状态变为`Approved`，并模拟执行。
    *   **奖励机制**: 系统从奖金池中，根据贡献度算法向参与签名的`Manager`自动分配奖励。

**3.3. Demo Mode (演示模式)**
*   **目的**: 这是您提到的我之前遗漏的关键功能。它的主要目的是**为了方便向评审官进行功能演示**。
*   **实现**: 由`DemoModeToggle.vue`组件控制。
*   **功能**:
    1.  **解除角色限制**: 在Demo Mode下，**无论当前选择什么角色，用户都可以在提案卡片上看到所有`Manager`的“Sign”和“Reject”按钮**。这允许演示者一人分饰多角，快速完成签名流程，而无需频繁切换角色。
    2.  **增强可视化**: 按钮上可能会有特殊标记（如`🎯`），以表明处于演示模式。

**3.4. 网络拓扑与节点管理 (DevLeChain环境)**
*   **可视化**: `Network.vue`页面通过Canvas动态展示所有节点（Managers, Operators, Treasury）的连接关系和状态。
*   **节点配置**: 系统使用DevLeChain的Keystore预定义核心账户：
    - **Keystore位置**: `/home/devlechain/ChainData/20000_20000_ethash_0/keystore`
    - **核心账户**: manager_0/1/2 (Manager角色), treasury (金库), operator_0/1 (Operator角色)
    - **账户密码**: "devlechain" (配置在DEVLECHAIN_CONFIG中)
    - **账户加载**: 使用eth_account.Account.decrypt()从Keystore文件解密私钥
*   **账户管理变化 (Phase 17)**:
    - **动态创建已废弃**: DevLeChain使用预定义Keystore账户，不支持运行时动态创建节点
    - **API端点**: `/api/network/nodes/create` 已废弃，返回501错误
    - **历史功能**: Phase 1-16的Ganache环境支持动态账户创建，现已移除

**3.5. 历史与审计**
`History.vue`页面提供了所有威胁检测日志和响应执行日志的完整列表，并以图表形式对攻击类型、置信度分布等进行了可视化分析，实现了完整的可追溯性。

**3.6. 置信度解释系统 (Phase 16新增)**
*   **轻量级提示**: `ConfidenceTooltip.vue`组件提供悬停触发的tooltip，显示置信度计算公式和快速阈值参考。
*   **详细解释**: 增强的模态框显示数学公式和详细参数解释。
*   **用户体验优化**: 为有经验的用户减少中断，同时保留教育内容。

**3.7. 已知技术限制**
*   **用户体验问题**: 提案签名后存在5秒延迟，这是由于同步奖励分配和区块链交易确认造成的。这个问题已在Phase 10计划中标记为优先解决项。
*   **Withdraw功能**: 前端UI已实现，数据库模型支持，但后端服务层实现不完整。

---

### Playwright 测试计划 (详尽版)

基于以上理解，以下是详尽的、可执行的 **Playwright 测试清单**。

**1. 核心流程测试 (Happy Path)**
*   [x] **(已完成)** 模拟一次中高置信度攻击。
*   [x] **(已完成)** 验证`Threats`页面出现新告警，且`Proposals`页面自动创建新提案。
*   [x] **(已完成)** 切换为`Manager 0`角色，签名提案。验证签名进度变为`1/2`。
*   [x] **(已完成)** 切换为`Manager 1`角色，再次签名。验证提案状态变为`Approved`，签名进度`2/2`，并显示奖励信息。
*   [ ] 导航到`History`页面，验证此次攻击、提案和执行的日志都已正确记录。

**2. 角色权限与UI验证 (RBAC Test)**
*   [x] **(已完成)** 切换为`Operator`角色，在`Proposals`页面验证**没有**“Sign/Reject”按钮。
*   [x] **(已完成)** 切换为`Manager`角色，在`Proposals`页面验证**有**“Sign/Reject”按钮。
*   [ ] 切换为`Manager`角色，在`Threats`页面验证**没有**为告警手动创建提案的按钮。
*   [ ] 切换为`Operator`角色，找到一个“Manual Decision”级别的告警，点击进入详情，验证**可以**成功创建提案。

**3. Demo Mode 功能测试**
*   [x] **(已完成)** 在导航栏打开 **Demo Mode** 开关。
*   [x] **(已完成)** 在`Proposals`页面找到一个`Pending`状态的提案。
*   [x] **(已完成)** **验证**：无论当前角色是什么，该提案卡片上都**同时显示**了`Manager 0`, `Manager 1`, `Manager 2`三人的“Sign”和“Reject”按钮。
*   [ ] 点击`Manager 0`的签名按钮，验证签名成功。
*   [ ] 接着点击`Manager 1`的签名按钮，验证提案被成功批准。

**4. 提案拒绝与撤回流程**
*   [x] **(已实现)** 模拟一次攻击，生成一个新提案。
*   [x] **(已实现)** 切换为`Manager 0`角色，点击"Reject"按钮。
*   [x] **(已实现)** **验证**：提案状态立即变为`Rejected`，并显示被`Manager 0`拒绝。
*   [ ] **(部分实现)** 模拟另一次攻击，生成一个新提案。
*   [ ] **(部分实现)** 切换为`Operator 0`角色，找到该提案，点击"Withdraw"按钮。
*   [ ] **(待完善)** **验证**：提案状态变为`Withdrawn`。（注：前端UI已实现，但后端API未完全实现）

**5. 网络页面交互与节点管理测试**
*   [ ] 导航到`Network`页面，验证所有预定义节点都已正确显示。
*   [ ] 在`Dashboard`页面，使用`AccountList.vue`组件的"Account Manager"创建一个新账户并为其注资。
*   [ ] 返回`Network`页面，**验证**：新创建的账户已动态添加到网络拓扑中。
*   [ ] 点击任意一个节点，验证`NodeDetail`模态框弹出，并显示该节点的正确信息（地址、余额、角色等）。
*   [ ] 选择一个非核心节点（非Manager_0-2或Treasury），点击"Delete Node"按钮删除该节点。
*   [ ] **验证**：该节点从网络拓扑中消失，余额已转回Treasury。
*   [ ] 验证网络拓扑图正确显示Manager、Operator、Treasury等不同类型节点的连接关系。
*   [ ] 测试节点状态的实时更新（如余额变化）。

---

### 项目当前状态总结 (2025年10月)

**✅ 已完成的主要功能:**
- ✅ Phase 1-4: 完整的AI威胁检测+区块链多签决策系统
- ✅ Phase 8: 合约级角色分离和权限管理
- ✅ Phase 8.5: 一票否决提案拒绝系统
- ✅ Phase 9: AI模型性能优化 (99.30%二分类，98.90%多分类准确率)
- ✅ Phase 15: UI一致性优化，修复ThreatAlert组件显示问题
- ✅ Phase 16: 置信度解释UX增强，实现轻量级tooltip系统
- ✅ Phase A: 完整奖励池机制，基于贡献度的公平分配算法
- ✅ **Phase 17: DevLeChain区块链迁移** - 从Ganache模拟器完全迁移到真实私有链

**Phase 17核心变更:**
- ✅ **区块链平台**: Ganache → DevLeChain (Geth 1.10.22, PoW ethash)
- ✅ **账户管理**: HD钱包助记词 → Keystore文件解密加载
- ✅ **数据架构**: 数据库优先 → 智能合约优先（数据库作为只读缓存）
- ✅ **合约部署**: 0x5FbDB...0aa3 (Ganache) → 0x7A267...D992 (DevLeChain)
- ✅ **业务逻辑**: 完全重构sign_proposal、create_proposal为区块链优先
- ✅ **API调整**: 废弃动态节点创建API (DevLeChain使用预定义账户)

**⚠️ 功能变化说明:**
- ❌ **动态节点创建已废弃**: DevLeChain使用预定义Keystore账户，不支持运行时创建节点
- ❌ **Withdraw提案功能**: 前端UI完整，但后端实现不完整（技术债务）
- 🔄 **5秒延迟用户体验问题**: 由于同步奖励分发导致的性能瓶颈（Phase 10计划中）

**🎯 未来发展方向:**
- 🔄 Phase 10: 用户体验优化（异步奖励处理）
- 🔄 Phase 11: MetaMask集成（7-10天预估）
- 🔄 高级角色管理功能
- 🔄 WebSocket实时更新

---

### 🔧 技术问题详细分析 (2025年9月测试发现)

**问题1: Withdraw提案功能缺失**
- **位置**: `backend/main.py:264` 调用 `proposal_service.withdraw_proposal()`
- **问题**: `backend/app/services.py` 中 `ProposalService` 类完全没有此方法实现
- **影响**: 前端UI完整，但点击Withdraw按钮返回500错误
- **修复需求**: 实现 `withdraw_proposal()` 方法，验证Operator权限，更新提案状态

**问题2: Create Node API已废弃 (Phase 17变更)**
- **位置**: `/api/network/nodes/create` 端点
- **状态**: 已废弃，返回501 Not Implemented错误
- **原因**: DevLeChain使用预定义的Keystore账户，不支持运行时动态创建节点
- **历史功能**: Phase 1-16的Ganache环境支持通过HD钱包动态创建账户
- **当前机制**: 所有账户在系统启动时从Keystore加载，账户列表固定

**问题3: 性能瓶颈分析**
- **位置**: `backend/app/services.py:435-461` 同步奖励循环
- **问题**: 为每个签名者依次发送区块链交易，阻塞用户界面
- **影响**: 提案签名后需等待5秒才能继续操作
- **优化方案**: 异步奖励处理或批量交易机制
