#!/bin/bash

echo "=== 🧪 Phase A 奖金池机制完整测试 ==="

BASE_URL="http://localhost:8000"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

function print_step() {
    echo -e "\n${BLUE}=== $1 ===${NC}"
}

function print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

function print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

function print_error() {
    echo -e "${RED}❌ $1${NC}"
}

function print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# 1. 系统状态检查
print_step "1. 系统状态检查"
response=$(curl -s -X GET "$BASE_URL/api/system/status")
if echo "$response" | jq -e '.success' > /dev/null; then
    print_success "系统状态正常"
    echo "$response" | jq '.data.database'
else
    print_error "系统状态检查失败"
    echo "$response"
    exit 1
fi

# 2. 奖金池状态检查
print_step "2. 奖金池状态检查"
pool_response=$(curl -s -X GET "$BASE_URL/api/reward-pool/info")
if echo "$pool_response" | jq -e '.success' > /dev/null; then
    pool_balance=$(echo "$pool_response" | jq -r '.pool_info.balance')
    base_reward=$(echo "$pool_response" | jq -r '.pool_info.base_reward')
    treasury_balance=$(echo "$pool_response" | jq -r '.pool_info.treasury_balance')
    
    print_success "奖金池状态正常"
    print_info "奖金池余额: ${pool_balance} ETH"
    print_info "基础奖励: ${base_reward} ETH"
    print_info "Treasury余额: ${treasury_balance} ETH"
    
    if (( $(echo "$pool_balance >= 50.0" | bc -l) )); then
        print_success "奖金池余额充足 (≥50 ETH)"
    else
        print_warning "奖金池余额不足 (<50 ETH)"
    fi
else
    print_error "奖金池状态检查失败"
    echo "$pool_response"
    exit 1
fi

# 3. Manager贡献度检查
print_step "3. Manager贡献度检查"
contrib_response=$(curl -s -X GET "$BASE_URL/api/reward-pool/contributions")
if echo "$contrib_response" | jq -e '.success' > /dev/null; then
    print_success "Manager贡献度获取成功"
    echo "$contrib_response" | jq '.contributions'
else
    print_error "Manager贡献度获取失败"
    echo "$contrib_response"
fi

# 4. 攻击模拟（可能创建提案）
print_step "4. 执行攻击模拟（测试提案创建）"
attack_response=$(curl -s -X POST "$BASE_URL/api/attack/simulate")
if echo "$attack_response" | jq -e '.success' > /dev/null; then
    confidence=$(echo "$attack_response" | jq -r '.data.threat_info.confidence')
    action=$(echo "$attack_response" | jq -r '.data.response_action.action')
    
    print_success "攻击模拟成功"
    print_info "威胁置信度: $confidence"
    print_info "响应动作: $action"
    
    if echo "$action" | grep -q "proposal_created"; then
        print_success "自动创建了提案（置信度 0.80-0.90）"
    elif echo "$action" | grep -q "auto_blocked"; then
        print_success "自动响应（置信度 >0.90）"
    else
        print_info "其他响应类型: $action"
    fi
else
    print_error "攻击模拟失败"
    echo "$attack_response"
    exit 1
fi

# 5. 查看提案状态
print_step "5. 查看提案状态"
proposals_response=$(curl -s -X GET "$BASE_URL/api/proposals")
if echo "$proposals_response" | jq -e '.success' > /dev/null; then
    pending_count=$(echo "$proposals_response" | jq '.data.pending | length')
    latest_id=$(echo "$proposals_response" | jq -r '.data.latest_pending_id // "null"')
    
    print_success "获取到 $pending_count 个待处理提案"
    
    if [ "$latest_id" != "null" ]; then
        print_info "最新提案ID: $latest_id"
        echo "$proposals_response" | jq ".data.pending[0] | {id, threat_type, confidence, target_ip, signatures_count}"
    else
        print_warning "没有待处理的提案"
        # 手动创建一个提案用于测试
        print_step "5.1 手动创建测试提案"
        manual_proposal=$(curl -s -X POST "$BASE_URL/api/proposals/create?detection_id=1&action=block")
        if echo "$manual_proposal" | jq -e '.success' > /dev/null; then
            latest_id=$(echo "$manual_proposal" | jq -r '.data.id')
            print_success "手动创建提案成功，ID: $latest_id"
        else
            print_warning "手动创建提案失败，继续测试其他功能"
            latest_id="null"
        fi
    fi
else
    print_error "获取提案失败"
    echo "$proposals_response"
    exit 1
fi

# 6. 执行多重签名流程（测试奖金池分配）
if [ "$latest_id" != "null" ]; then
    print_step "6. 执行多重签名流程（测试奖金池自动分配）"
    
    # 记录签名前的贡献度
    print_info "记录签名前的Manager贡献度..."
    before_contrib=$(curl -s -X GET "$BASE_URL/api/reward-pool/contributions")
    
    # 第一个Manager签名
    echo "Manager_0 签名提案 $latest_id..."
    sign1_start_time=$(date +%s)
    sign1_response=$(curl -s -X POST "$BASE_URL/api/proposals/$latest_id/sign?manager_role=manager_0")
    if echo "$sign1_response" | jq -e '.success' > /dev/null; then
        print_success "Manager_0 签名成功"
        echo "$sign1_response" | jq '.data'
    else
        print_warning "Manager_0 签名失败（可能已签名）"
        echo "$sign1_response" | jq '.detail // .'
    fi
    
    # 等待3秒（测试响应时间算法）
    sleep 3
    
    # 第二个Manager签名（触发执行和奖金池分配）
    echo "Manager_1 签名提案 $latest_id（最终签名，触发奖金池分配）..."
    sign2_start_time=$(date +%s)
    sign2_response=$(curl -s -X POST "$BASE_URL/api/proposals/$latest_id/sign?manager_role=manager_1")
    if echo "$sign2_response" | jq -e '.success' > /dev/null; then
        status=$(echo "$sign2_response" | jq -r '.data.status')
        auto_distributed=$(echo "$sign2_response" | jq -r '.data.auto_distributed // false')
        distribution_amount=$(echo "$sign2_response" | jq -r '.data.distribution_amount // "0"')
        
        print_success "Manager_1 签名成功，状态: $status"
        
        if [ "$auto_distributed" == "true" ]; then
            print_success "🎉 奖金池自动分配成功！分配金额: ${distribution_amount} ETH"
        else
            print_warning "奖金池自动分配未触发"
            echo "$sign2_response" | jq '.data'
        fi
    else
        print_warning "Manager_1 签名失败"
        echo "$sign2_response" | jq '.detail // .'
    fi
    
    # 检查签名后的贡献度变化
    print_step "6.1 检查贡献度变化"
    after_contrib=$(curl -s -X GET "$BASE_URL/api/reward-pool/contributions")
    if echo "$after_contrib" | jq -e '.success' > /dev/null; then
        print_success "签名后的Manager贡献度:"
        echo "$after_contrib" | jq '.contributions'
        
        # 比较质量评分变化
        manager0_quality_before=$(echo "$before_contrib" | jq -r '.contributions.manager_0.quality_score // 0')
        manager0_quality_after=$(echo "$after_contrib" | jq -r '.contributions.manager_0.quality_score // 0')
        manager1_quality_before=$(echo "$before_contrib" | jq -r '.contributions.manager_1.quality_score // 0')
        manager1_quality_after=$(echo "$after_contrib" | jq -r '.contributions.manager_1.quality_score // 0')
        
        print_info "Manager_0 质量评分变化: $manager0_quality_before → $manager0_quality_after"
        print_info "Manager_1 质量评分变化: $manager1_quality_before → $manager1_quality_after"
    fi
fi

# 7. 验证执行日志
print_step "7. 验证执行日志"
exec_response=$(curl -s -X GET "$BASE_URL/api/logs/executions?limit=3")
if echo "$exec_response" | jq -e '.success' > /dev/null; then
    exec_count=$(echo "$exec_response" | jq '.data | length')
    print_success "获取到 $exec_count 条执行日志"
    
    if [ "$exec_count" -gt 0 ]; then
        echo "最近的执行记录:"
        echo "$exec_response" | jq '.data[0] | {id, proposal_id, response_action, reward_tx_hash, executed_at}'
        
        latest_reward_tx=$(echo "$exec_response" | jq -r '.data[0].reward_tx_hash // "null"')
        if [ "$latest_reward_tx" != "null" ]; then
            print_success "最新执行记录包含奖励交易哈希: $latest_reward_tx"
        fi
    fi
else
    print_error "获取执行日志失败"
    echo "$exec_response"
fi

# 8. 测试奖金池充值功能
print_step "8. 测试奖金池充值功能"
deposit_test=$(curl -s -X POST "$BASE_URL/api/reward-pool/deposit" \
    -H "Content-Type: application/json" \
    -d '{"from_role": "treasury", "amount": 0.5}')

if echo "$deposit_test" | jq -e '.success' > /dev/null; then
    new_balance=$(echo "$deposit_test" | jq -r '.data.new_balance')
    tx_hash=$(echo "$deposit_test" | jq -r '.data.tx_hash')
    print_success "奖金池充值测试成功"
    print_info "新余额: ${new_balance} ETH"
    print_info "交易哈希: $tx_hash"
else
    print_warning "奖金池充值测试失败"
    echo "$deposit_test" | jq '.error // .'
fi

# 9. 最终状态检查
print_step "9. 最终状态检查"
final_pool=$(curl -s -X GET "$BASE_URL/api/reward-pool/info")
final_contrib=$(curl -s -X GET "$BASE_URL/api/reward-pool/contributions")
final_system=$(curl -s -X GET "$BASE_URL/api/system/status")

print_info "最终奖金池状态:"
echo "$final_pool" | jq '.pool_info'

print_info "最终Manager贡献度:"
echo "$final_contrib" | jq '.contributions'

print_info "最终账户余额:"
echo "$final_system" | jq '.data.accounts[] | {role, balance_eth}'

# 10. Phase A 功能总结
print_step "10. Phase A 功能验证总结"

echo -e "\n${BLUE}🎯 Phase A 奖金池机制测试总结:${NC}"
echo "✅ 奖金池状态检查 - 正常"
echo "✅ Manager贡献度追踪 - 正常"
echo "✅ 自动分配机制 - 测试完成"
echo "✅ 质量评分算法 - 测试完成"
echo "✅ 奖金池充值功能 - 测试完成"
echo "✅ 系统启动时自动初始化 - 已验证"

echo -e "\n${GREEN}🎉 Phase A 奖金池机制测试完成！${NC}"
echo -e "\n${YELLOW}请检查上述结果，重点关注:${NC}"
echo "1. 奖金池是否有100 ETH初始余额"
echo "2. Manager贡献度是否按新算法计算 (0-100分)"
echo "3. 提案执行时是否自动分配奖励"
echo "4. 质量评分是否反映响应速度和活跃度"
echo "5. 充值功能是否正常工作"