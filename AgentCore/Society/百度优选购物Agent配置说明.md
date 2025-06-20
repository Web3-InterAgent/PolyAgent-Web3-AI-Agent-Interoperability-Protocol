# 百度优选购物Agent配置说明

## 概述

本项目已成功集成百度优选MCP服务器，提供智能购物、商品搜索、参数对比、品牌排行和订单管理等功能。

## 已完成的配置

### 1. MCP服务器配置
- ✅ 创建了 `AgentCore/Mcp/youxuan_server.json` 配置文件
- ✅ 配置了百度优选MCP服务器连接参数

### 2. 购物Agent实现
- ✅ 创建了 `AgentCore/Society/youxuan_shopping_agent.py`
- ✅ 实现了智能路由系统，支持8种核心购物功能：
  - 🔍 商品检索 (spu_list)
  - 📊 手机参数对比 (param_compare)
  - 🏆 品牌排行榜 (brand_rank)
  - 📱 商品详情查询 (spu_detail)
  - 🛒 商品下单 (order_create)
  - 📋 订单管理 (order_detail, order_history)
  - 🔧 售后服务 (after_service)

### 3. 后端集成
- ✅ 修改了 `app.py`，将原来的 `market-monitor` 接口替换为 `youxuan-shopping` 接口
- ✅ 集成了百度优选购物Agent到主要的Agent管理器中

### 4. 前端更新
- ✅ 修改了前端 `App.tsx`，将"加密货币市场助手"更改为"百度优选购物助手"
- ✅ 更新了Agent描述和图标
- ✅ 修改了API调用端点

## 使用步骤

### 第一步：申请百度优选Token
1. 访问百度优选开放平台
2. 申请服务端Token
3. 获取您的专属Token

### 第二步：配置Token
编辑 `AgentCore/Mcp/youxuan_server.json` 文件：

```json
{
  "mcpServers": {
    "youxuan-mcp": {
      "url": "https://mcp-youxuan.baidu.com/mcp/sse?key={token}",
      "env": {
        "YOUXUAN_TOKEN": "your_actual_token_here"
      },
      "disabled": false,
      "autoApprove": [],
      "clientRequestTimeout": 60000
    }
  }
}
```

将 `your_actual_token_here` 替换为您申请到的真实Token。

### 第三步：启动应用
```bash
# 启动后端服务
python app.py

# 启动前端服务（在另一个终端）
cd frontEnd
npm run dev
```

### 第四步：测试购物功能
在前端界面中：
1. 选择"百度优选购物助手"
2. 尝试以下测试查询：
   - "我想买一部华为手机"
   - "对比iPhone15和华为Mate60"
   - "手机品牌排行榜"
   - "查看我的订单"

## 功能特性

### 智能购物搜索
- 支持自然语言商品搜索
- 智能关键词提取
- 分页浏览商品结果

### 商品对比分析
- 专业的手机参数对比
- 全维度参数解读
- 智能推荐建议

### 品牌排行服务
- 实时品牌排行榜
- 多类别商品排名
- 专业排行分析

### 订单管理
- 在线下单购买
- 订单状态查询
- 订单历史管理
- 售后服务支持

## 安全提醒

⚠️ **重要安全提示**：
- Token与您的百度账号强绑定
- 切勿将Token提供给他人
- 定期检查Token使用情况
- 如有必要可前往平台注销Token

## 技术架构

```
前端 (React + TypeScript)
    ↓ HTTP请求
后端 (Flask + Python)
    ↓ Agent调用
百度优选购物Agent
    ↓ MCP协议
百度优选MCP服务器
    ↓ API调用
百度优选开放平台
```

## 故障排除

### 常见问题

1. **Token无效错误**
   - 检查Token是否正确配置
   - 确认Token是否已过期
   - 验证网络连接

2. **MCP连接失败**
   - 检查网络连接
   - 确认MCP服务器状态
   - 验证配置文件格式

3. **购物功能无响应**
   - 检查后端日志
   - 确认Agent是否正确初始化
   - 验证前端API调用

### 调试方法

1. **查看后端日志**：
   ```bash
   python app.py
   # 观察控制台输出
   ```

2. **检查前端网络请求**：
   - 打开浏览器开发者工具
   - 查看Network标签页
   - 检查API请求状态

3. **测试MCP连接**：
   ```bash
   # 在项目根目录运行
   python -c "from AgentCore.Society.youxuan_shopping_agent import YouxuanShoppingAgent; print('导入成功')"
   ```

## 更新日志

- **2025-01-07**: 完成百度优选MCP服务器集成
- **2025-01-07**: 实现购物Agent智能路由系统
- **2025-01-07**: 更新前后端接口和UI

## 联系支持

如遇到技术问题，请：
1. 检查本文档的故障排除部分
2. 查看项目GitHub Issues
3. 联系技术支持团队

---

*百度优选购物Agent - 让AI购物更智能* 