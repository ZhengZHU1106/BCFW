# 项目分析报告

本报告旨在识别和总结当前项目中存在的功能重复、实现冲突以及可以被清理的冗余文件，并为后续的优化工作提供建议。

## 一、 功能重复与实现冲突汇总

经过分析，项目中存在几处明显的功能重复或实现逻辑分散的问题，这可能导致维护困难和行为不一致。

### 1. 核心问题：提案签名与状态管理

这是最核心的实现冲突，直接导致应用行为与文档描述不符。

*   **冲突方 A**: `backend/app/services.py` -> `ProposalService`
    *   **实现方式**: **纯数据库模拟**。通过 `SQLAlchemy` 与 SQLite 数据库中的 `proposals` 表进行交互。
    *   **当前状态**: **API 正在使用此版本**。它负责处理所有来自前端的提案相关请求。
    *   **特点**: 逻辑简单，仅更新数据库状态，不包含完整的智能合约逻辑（如奖励、事件日志）。

*   **冲突方 B**: `backend/blockchain/multisig_contract.py` -> `MultiSigContract`
    *   **实现方式**: **带区块链交互的内存模拟**。它在内存中（一个Python字典）管理提案，但在需要时（如执行奖励）会调用 `web3_manager` 与区块链进行真实交互。
    *   **当前状态**: **未被 API 使用**。虽然功能更完整，更接近文档描述，但它完全被架空了。
    *   **特点**: 包含了签名、执行、奖励分配、贡献度更新等复杂逻辑，更符合项目文档的描述。

*   **根本问题**: 用户体验到的是 `ProposalService` 提供的简化版功能，而开发者意图实现的、更完整的功能在 `MultiSigContract` 中并未被激活。

---

### 2. 分散的逻辑：奖金池与贡献度管理

管理奖金池和Manager贡献度的逻辑同样分散在两个不同的类中，存在数据一致性风险。

*   **冲突方 A**: `backend/app/services.py` -> `RewardPoolService`
    *   **实现方式**: **基于JSON文件的状态管理**。它直接读取和写入 `backend/assets/reward_pool_state.json` 和 `manager_contributions_state.json` 这两个文件来维护状态。
    *   **当前状态**: **API 正在使用此版本**来展示奖金池和贡献度信息。
    *   **特点**: 作为一个独立的服务，专门负责这部分信息的增删改查。

*   **冲突方 B**: `backend/blockchain/multisig_contract.py` -> `MultiSigContract`
    *   **实现方式**: **同样基于JSON文件的状态管理**。此类在其内部方法中，也读取和写入相同的JSON文件。
    *   **当前状态**: **未被 API 直接使用**。
    *   **特点**: 将贡献度更新等逻辑与提案签名、执行等核心流程耦合在一起。

*   **根本问题**: 两个不同的类都在直接操作同一个外部状态文件，这是非常危险的设计。如果它们的内部逻辑稍有不同，极易导致状态文件损坏或数据不一致。

---

### 3. 轻微重复：合约部署脚本

在 `scripts/` 目录下，存在两个功能相似的部署脚本，可能导致混淆。

*   **脚本 A**: `deploy_multisig_simple.js`
    *   **功能**: 一个非常基础的部署脚本，仅将 `MultiSigProposal.sol` 合约部署到区块链上。
    *   **当前状态**: **`system.sh` 启动脚本正在使用此版本**。

*   **脚本 B**: `deploy_multisig.js`
    *   **功能**: 一个更复杂的脚本，包含了设置合约拥有者（owners）等更高级的功能。
    *   **当前状态**: 未被自动化脚本使用。

*   **根本问题**: 虽然不算严重冲突，但可能导致混淆。例如，开发者手动运行了 `deploy_multisig.js` 并设置了不同的权限，但 `system.sh` 启动时又用 `simple` 版本覆盖了配置，可能会产生意料之外的权限问题。

## 二、 未使用及冗余文件汇总

以下文件在项目运行时未使用，或其功能已被替代，可以考虑清理或归档。

| 文件/目录 | 路径 | 原因分析 |
| :--- | :--- | :--- |
| **冗余贡献度文件** | `backend/assets/manager_contributions.json` | 该文件未被任何代码引用。系统实际使用的是 `manager_contributions_state.json`。 |
| **冗余接口文件** | `backend/assets/multisig_interface.json` | 一个早期的、不完整的合约ABI版本。系统实际使用的是 `multisig_contract.json`。 |
| **一次性工具脚本** | `create_balanced_inference_data.py` | 用于生成AI推理数据的开发工具，在程序运行时无需使用。 |
| **开发过程记录** | `CLAUDE.md` | 开发日志或与AI助手的对话记录，可安全归档。 |
| **冗余状态文件** | `backend/assets/contributions_state.json` | 与 `manager_contributions_state.json` 功能完全重叠，是未被使用的 `MultiSigContract` 类意图使用的状态文件。 |
| **原始数据目录** | `original_data/` | 包含原始数据，对于理解项目背景很重要，但程序运行时不直接依赖此目录。 |
