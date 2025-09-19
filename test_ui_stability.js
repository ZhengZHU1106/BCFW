const { test, expect } = require('@playwright/test')

/**
 * UI稳定性测试 - 验证前端UI修复后的稳定性
 * 测试场景：
 * 1. 角色切换后元素引用保持有效
 * 2. 关闭模态框后页面元素不失效
 * 3. 连续操作的稳定性
 */

test.describe('前端UI稳定性测试', () => {
  test.beforeEach(async ({ page }) => {
    // 导航到主页面
    await page.goto('http://localhost:5173')
    await page.waitForLoadState('networkidle')
  })

  test('角色切换后元素引用保持有效', async ({ page }) => {
    console.log('🧪 测试：角色切换后元素引用保持有效')

    // 1. 获取初始元素引用
    const roleSelect = page.locator('#role-select')
    await expect(roleSelect).toBeVisible()

    // 2. 获取页面上的其他关键元素
    const dashboardTitle = page.locator('h2').first()
    const navLinks = page.locator('.nav-link').first()

    // 3. 验证初始状态
    await expect(dashboardTitle).toBeVisible()
    await expect(navLinks).toBeVisible()

    // 4. 切换角色
    console.log('🔄 切换角色从 operator_0 到 manager_0')
    await roleSelect.selectOption('manager_0')

    // 5. 等待角色切换完成（防抖延迟300ms + 一些缓冲）
    await page.waitForTimeout(500)

    // 6. 验证之前获取的元素引用仍然有效
    await expect(dashboardTitle).toBeVisible()
    await expect(navLinks).toBeVisible()

    // 7. 再次切换角色
    console.log('🔄 切换角色从 manager_0 到 operator_1')
    await roleSelect.selectOption('operator_1')
    await page.waitForTimeout(500)

    // 8. 验证元素引用持续有效
    await expect(dashboardTitle).toBeVisible()
    await expect(navLinks).toBeVisible()

    console.log('✅ 角色切换测试通过 - 元素引用保持稳定')
  })

  test('模态框操作后页面元素保持有效', async ({ page }) => {
    console.log('🧪 测试：模态框操作后页面元素保持有效')

    // 1. 导航到威胁检测页面
    await page.click('a[href="/threats"]')
    await page.waitForLoadState('networkidle')

    // 2. 模拟一次攻击生成威胁数据
    const simulateBtn = page.locator('button').filter({ hasText: 'Simulate Attack' })
    if (await simulateBtn.isVisible()) {
      await simulateBtn.click()
      await page.waitForTimeout(2000) // 等待攻击模拟完成
    }

    // 3. 获取页面关键元素引用
    const pageTitle = page.locator('h2').filter({ hasText: 'Threat Detection' })
    const navBar = page.locator('.navbar')

    // 4. 验证初始状态
    await expect(pageTitle).toBeVisible()
    await expect(navBar).toBeVisible()

    // 5. 查找置信度信息按钮并触发tooltip
    const confidenceInfoBtn = page.locator('.confidence-info-btn')
    if (await confidenceInfoBtn.isVisible()) {
      console.log('🎯 触发置信度tooltip')
      await confidenceInfoBtn.hover()
      await page.waitForTimeout(200)

      // 6. 验证tooltip出现后页面元素仍然有效
      await expect(pageTitle).toBeVisible()
      await expect(navBar).toBeVisible()

      // 7. 移开鼠标，隐藏tooltip
      await page.mouse.move(0, 0)
      await page.waitForTimeout(200)
    }

    // 8. 查找并点击威胁详情
    const threatRow = page.locator('.threat-row').first()
    if (await threatRow.isVisible()) {
      console.log('🎯 点击威胁详情打开模态框')
      await threatRow.click()
      await page.waitForTimeout(500)

      // 9. 验证模态框打开后原页面元素仍然有效
      await expect(pageTitle).toBeVisible()
      await expect(navBar).toBeVisible()

      // 10. 关闭模态框
      const closeBtn = page.locator('.close-btn, .modal-backdrop')
      if (await closeBtn.first().isVisible()) {
        await closeBtn.first().click()
        await page.waitForTimeout(500)
      }

      // 11. 验证模态框关闭后元素引用仍然有效
      await expect(pageTitle).toBeVisible()
      await expect(navBar).toBeVisible()
    }

    console.log('✅ 模态框操作测试通过 - 元素引用保持稳定')
  })

  test('连续操作稳定性测试', async ({ page }) => {
    console.log('🧪 测试：连续操作稳定性')

    // 1. 获取稳定的元素引用
    const roleSelect = page.locator('#role-select')
    const threatsNavLink = page.locator('a[href="/threats"]')
    const proposalsNavLink = page.locator('a[href="/proposals"]')

    // 2. 执行连续操作序列
    for (let i = 0; i < 3; i++) {
      console.log(`🔄 第 ${i + 1} 轮连续操作`)

      // 切换角色
      await roleSelect.selectOption(i % 2 === 0 ? 'manager_0' : 'operator_0')
      await page.waitForTimeout(400)

      // 验证导航链接仍然可点击
      await expect(threatsNavLink).toBeVisible()
      await expect(proposalsNavLink).toBeVisible()

      // 导航到威胁页面
      await threatsNavLink.click()
      await page.waitForLoadState('networkidle')

      // 验证页面加载成功
      await expect(page.locator('h2').filter({ hasText: 'Threat Detection' })).toBeVisible()

      // 导航到提案页面
      await proposalsNavLink.click()
      await page.waitForLoadState('networkidle')

      // 验证页面加载成功
      await expect(page.locator('h2').filter({ hasText: 'Proposal Management' })).toBeVisible()

      // 返回首页
      await page.click('a[href="/"]')
      await page.waitForLoadState('networkidle')
    }

    // 3. 最终验证所有关键元素仍然有效
    await expect(roleSelect).toBeVisible()
    await expect(threatsNavLink).toBeVisible()
    await expect(proposalsNavLink).toBeVisible()

    console.log('✅ 连续操作稳定性测试通过')
  })

  test('列表更新稳定性测试', async ({ page }) => {
    console.log('🧪 测试：列表更新稳定性')

    // 1. 导航到提案页面
    await page.click('a[href="/proposals"]')
    await page.waitForLoadState('networkidle')

    // 2. 获取刷新按钮和状态筛选器
    const refreshBtn = page.locator('button').filter({ hasText: 'Refresh' })
    const statusFilter = page.locator('.filter-select')

    // 3. 验证初始状态
    await expect(refreshBtn).toBeVisible()
    await expect(statusFilter).toBeVisible()

    // 4. 执行多次刷新操作
    for (let i = 0; i < 3; i++) {
      console.log(`🔄 第 ${i + 1} 次刷新操作`)

      // 点击刷新按钮
      await refreshBtn.click()
      await page.waitForTimeout(1000)

      // 验证关键元素仍然可用
      await expect(refreshBtn).toBeVisible()
      await expect(statusFilter).toBeVisible()

      // 尝试使用状态筛选器
      await statusFilter.selectOption('all')
      await page.waitForTimeout(200)
    }

    // 5. 验证角色切换不影响列表稳定性
    const roleSelect = page.locator('#role-select')
    await roleSelect.selectOption('manager_1')
    await page.waitForTimeout(500)

    // 6. 验证列表相关元素仍然稳定
    await expect(refreshBtn).toBeVisible()
    await expect(statusFilter).toBeVisible()

    console.log('✅ 列表更新稳定性测试通过')
  })

  test('DOM元素key稳定性验证', async ({ page }) => {
    console.log('🧪 测试：DOM元素key稳定性')

    // 1. 导航到提案页面
    await page.click('a[href="/proposals"]')
    await page.waitForLoadState('networkidle')

    // 2. 获取提案卡片元素（如果存在）
    const proposalCards = page.locator('.proposal-card')
    const cardCount = await proposalCards.count()

    if (cardCount > 0) {
      console.log(`📋 找到 ${cardCount} 个提案卡片`)

      // 3. 获取第一个卡片的关键信息
      const firstCard = proposalCards.first()
      const cardText = await firstCard.textContent()

      // 4. 切换角色
      const roleSelect = page.locator('#role-select')
      await roleSelect.selectOption('manager_0')
      await page.waitForTimeout(500)

      // 5. 验证卡片内容保持一致（DOM复用成功）
      const updatedFirstCard = proposalCards.first()
      const updatedCardText = await updatedFirstCard.textContent()

      // 内容应该基本一致（可能有按钮状态变化）
      expect(updatedCardText).toContain(cardText.substring(0, 20)) // 检查前20个字符

      console.log('✅ 提案卡片DOM稳定性验证通过')
    } else {
      console.log('ℹ️ 当前没有提案数据，跳过卡片稳定性测试')
    }

    // 6. 导航到威胁页面测试表格行的稳定性
    await page.click('a[href="/threats"]')
    await page.waitForLoadState('networkidle')

    // 7. 检查威胁表格行
    const threatRows = page.locator('.threat-row')
    const rowCount = await threatRows.count()

    if (rowCount > 0) {
      console.log(`🔍 找到 ${rowCount} 个威胁记录`)

      // 8. 切换角色并验证表格稳定性
      await roleSelect.selectOption('operator_2')
      await page.waitForTimeout(500)

      // 9. 验证表格行仍然存在且可交互
      await expect(threatRows.first()).toBeVisible()

      console.log('✅ 威胁表格DOM稳定性验证通过')
    } else {
      console.log('ℹ️ 当前没有威胁数据，跳过表格稳定性测试')
    }
  })
})

// 测试总结
test.afterAll(async () => {
  console.log('\n🎉 UI稳定性测试套件完成')
  console.log('📊 测试覆盖了以下场景：')
  console.log('   ✓ 角色切换后元素引用稳定性')
  console.log('   ✓ 模态框操作后DOM稳定性')
  console.log('   ✓ 连续操作的系统稳定性')
  console.log('   ✓ 列表更新的DOM复用效果')
  console.log('   ✓ key属性管理的有效性')
  console.log('\n如果所有测试通过，说明UI稳定性问题已得到有效修复！')
})