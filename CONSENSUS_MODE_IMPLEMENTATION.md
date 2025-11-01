# DevLeChain PoA 演示模式实施说明

> **版本**: v3.0
> **发布日期**: 2025-01-02
> **状态**: 演示环境默认运行于 PoA，PoW 留作历史数据保留

---

## 🎯 目标与范围

本说明书描述如何将 DevLeChain 演示环境切换为 **单一 PoA (Clique)** 模式，并保留现有 PoW 历史数据用于展示。更新重点：

- 统一运行模式：PoA 为默认且唯一的活动链，确保 1s 出块与顺畅演示。
- 自动化初始化：提供 `bootstrap_poa_demo.py` 一键完成 Genesis、数据目录、合约部署与角色配置。
- 历史数据兼容：保留旧 PoW 合约配置与数据库记录，所有旧提案在前端以只读方式展示。
- 系统脚本更新：`system.sh` 自动终止残留的 PoW geth 进程并启动 PoA 全栈。

---

## 🧱 架构调整概览

| 模块 | 说明 |
|------|------|
| `backend/config.py` | 精简为 PoA 单链配置，`deployed_contract.json` 仅记录 PoA 合约，旧 PoW 文件自动归档为 `deployed_contract_pow_legacy.json`。 |
| `backend/blockchain/web3_manager.py` | 始终连接 PoA；若合同缺失返回清晰提示。 |
| `backend/app/services.py` | 签名/拒绝前验证提案所属合约，旧 PoW 提案保持只读。 |
| `system.sh` | 移除多模式逻辑，固定启动 PoA，启动前会终止占用 8545 的传统 geth。 |
| `scripts/bootstrap_poa_demo.py` | 一键生成 genesis、初始化数据目录、部署合约、分配角色与资金。 |
| `frontend` | 移除共识切换组件；UI 自动展示所有提案（含 PoW 历史）并对 PoA 提案提供完全操作。 |

---

## ♻️ 数据重置

当 PoA 演示环境出现数据漂移（例如遗留的 PoW 提案或孤立合约 ID）时，可按以下步骤恢复干净状态：

```bash
./scripts/reset_poa_demo.sh
python3 scripts/bootstrap_poa_demo.py --force
./system.sh start
```

重置脚本会：
- 归档当前数据库与合约文件到 `.backups/<timestamp>/`
- 清理 `backend/security_platform.db`、`backend/database/bcfw.db`
- 清除 `/home/devlechain/ChainData/poa_chain`，停止正在运行的 geth
- 保留旧 PoW 合约备份，方便以后回顾

之后重新执行 bootstrap 与 system.sh，即可得到完全同步的 PoA 演示数据。

若需要巡检现有提案与链上状态是否一致，可使用：

```bash
python3 scripts/validate_proposals.py          # 仅报告
python3 scripts/validate_proposals.py --fix    # 将缺失的提案标记为 invalid
```

---

## ⚙️ 一键部署流程

### 1. 运行 PoA 引导脚本

```bash
python scripts/bootstrap_poa_demo.py
```

功能：
1. 检查并生成 `genesis_poa.json`。
2. `geth init` 初始化 `ChainData/poa_chain`。
3. 检测现有 `backend/assets/deployed_contract.json`：
   - 若为旧 PoW 合约（chain_id 20000），自动移动到 `deployed_contract_pow_legacy.json` 备份；
   - 若为有效 PoA 合约（chain_id 20001），跳过部署；
   - 否则自动启动临时 geth，执行 `deploy_and_init.py` 完成部署、角色分配与奖金池充值。

支持参数：
- `--force`：重新生成 genesis、重建数据目录并强制部署新合约。
- `--redeploy`：仅强制重新部署合约（保留数据目录）。

> **注意**：脚本会在启动临时节点前自动结束占用 8545 端口的任何进程，包括历史 PoW geth。

### 2. 启动全栈服务

```bash
./system.sh start
```

脚本行为：
1. 再次终止残留 geth（防止 PoW 链占用 8545）。
2. 校验数据目录、keystore、PoA 合约配置是否齐全。
3. 启动 PoA geth、FastAPI、Vue 前端。日志统一输出到 `.logs/`。

常用命令：

```bash
./system.sh status    # 查看服务与区块高度
./system.sh restart   # 重启全栈
./system.sh stop      # 停止所有服务
./system.sh blockchain restart  # 仅重启 geth
```

---

## 🗃️ 历史数据处理策略

- **数据库**：保留所有 PoW 时代生成的提案、执行日志与威胁记录。
- **旧合约文件**：部署脚本会自动将 `backend/assets/deployed_contract.json`（chain_id 20000）重命名为 `deployed_contract_pow_legacy.json`。如需手动恢复，可复制回原路径。
- **只读保护**：当对旧提案执行签名或拒绝操作时，后端会返回提示：
  > “该提案创建于旧的 PoW 合约，已作为历史记录保留。”

---

## 🧪 验证步骤

1. 执行 `python scripts/bootstrap_poa_demo.py`，确保输出包含
   - `PoA contract deployment finished`
   - `Temporary geth node stopped`
2. 运行 `./system.sh start`，检查日志：
   - `PoA chain running (PID ...)`
   - 后端启动成功且无合约缺失错误。
3. 打开 `http://localhost:5173`，验证：
   - Dashboard 中存在旧提案（标记只读）与新提案创建入口。
   - 创建/签名新提案 < 2s 完成。
   - 奖金池余额展示正常。

4. 可选：运行 `python scripts/bootstrap_poa_demo.py --force` 重新生成演示环境；旧合约 artefact 将另存为带时间戳的备份。

---

## ❓ 常见问题

| 问题 | 解决方案 |
|------|----------|
| `PoA multisig contract未初始化` | 运行 `python scripts/bootstrap_poa_demo.py` 生成合约。 |
| `系统启动提示 Contract config not found` | 合约文件缺失或被移动，再次执行引导脚本。 |
| 端口 8545 被占用 | `system.sh` 与引导脚本会自动终止冲突进程；若仍存在，手动执行 `lsof -ti:8545 | xargs kill`. |
| 需要演示 PoW 历史 | 使用前端查看旧提案或引用 `backend/assets/deployed_contract_pow_legacy.json` 中的地址。 |

---

## 📚 变更记录

- **v3.0**: 移除多模式切换，PoA 成为唯一运行模式；新增自动化引导脚本与只读保护逻辑。 
- **v2.x**: 旧版文档保留于 Git 历史中，仅供参考。

---

如需进一步自定义（例如重新引入 PoW 做教学对比），建议将当前流程封装为脚本后再扩展自定义逻辑，避免影响演示稳定性。
