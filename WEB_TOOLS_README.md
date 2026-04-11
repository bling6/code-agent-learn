# Web 工具使用说明

## 功能概述

已成功为你的 AI Agent 添加了联网能力，包括：

### 1. web_search - 网页搜索
使用 DuckDuckGo 搜索引擎查找信息

**参数：**
- `query` (必需): 搜索关键词或问题
- `num_results` (可选): 返回结果数量，默认5条

**返回：**
- 搜索结果摘要和相关链接

**示例：**
```python
# Agent 会自动调用
web_search(query="Python 异步编程", num_results=5)
```

### 2. web_fetch - 网页抓取
抓取指定 URL 的网页内容

**参数：**
- `url` (必需): 要抓取的网页 URL
- `timeout` (可选): 超时时间（秒），默认15秒

**返回：**
- 网页内容预览（最多2000字符）

**示例：**
```python
# Agent 会自动调用
web_fetch(url="https://docs.python.org", timeout=15)
```

## 技术实现

### 文件结构
```
agents/
├── web_tools.py          # Web 工具实现
├── tools.py              # 工具注册和映射
└── agent.py              # Agent 主逻辑
```

### 关键特性
- ✅ 使用 DuckDuckGo API 进行搜索（无需 API Key）
- ✅ 支持自定义 User-Agent
- ✅ 自动检测和处理网页编码
- ✅ 超时控制（默认15秒）
- ✅ 错误处理和友好提示
- ✅ 内容清理和预览限制

### 依赖
- `requests`: HTTP 请求库（已安装）

## 使用场景

Agent 现在可以：
1. 搜索最新的技术文档和教程
2. 查询 API 使用方法
3. 获取库和框架的更新信息
4. 抓取网页内容进行分析
5. 解决编程问题的最新方案

## 测试

已测试通过：
- ✅ 搜索功能正常
- ✅ 网页抓取正常
- ✅ 错误处理正常

## 下一步优化建议

如果需要增强功能，可以考虑：
1. 添加更多搜索引擎支持（Google、Bing 等）
2. 支持网页内容智能提取（去除 HTML 标签）
3. 添加网页截图功能
4. 支持 JavaScript 渲染的网页（需要浏览器）
5. 添加缓存机制避免重复请求