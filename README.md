# PolyCrawler 项目

PolyCrawler 是一个结合向量搜索和大语言模型的智能搜索引擎，专门用于教育项目信息的检索。系统支持三种搜索模式：关键词搜索、向量语义搜索和基于大语言模型的智能搜索。

## 功能特点

- **关键词搜索**：传统的基于关键词匹配的搜索方式
- **向量语义搜索**：使用BGE模型进行文本嵌入，支持语义理解的搜索
- **智能搜索**：利用大语言模型动态分析用户查询意图，调整字段权重进行更精准的搜索

## 系统架构

- **前端**：React + TypeScript + Ant Design
- **后端**：Flask + MongoDB
- **嵌入模型**：BGE-base-en-v1.5
- **大语言模型**：阿里云百炼 Qwen-Plus

## 配置与安装

### 环境要求

- Python 3.8+
- MongoDB
- Node.js 14+

### 安装步骤

1. 克隆代码仓库
```bash
git clone <repository-url>
cd PolyCrawler
```

2. 安装Python依赖
```bash
pip install -r requirements.txt
```

3. 安装前端依赖
```bash
cd frontend
npm install
```

4. 配置环境变量
创建`.env`文件并添加以下内容：
```
# 大模型 API 配置
DASHSCOPE_API_KEY=your_api_key_here
DASHSCOPE_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
LLM_MODEL_NAME=qwen-plus

# MongoDB 配置
MONGODB_URI=mongodb://localhost:27017/
DB_NAME=sim_programs
COLLECTION_NAME=programs
```

5. 启动MongoDB服务
```bash
mongod --dbpath <path-to-data-directory>
```

### 运行项目

1. 安装Flask异步支持
```bash
pip install flask[async]
```

2. 启动后端服务
```bash
python backend/app.py
```

3. 启动前端开发服务器
```bash
cd frontend
npm start
```

4. 初始化数据
访问 http://localhost:3000，点击"初始化"按钮或使用API endpoint `/api/init`

## 使用说明

1. **搜索模式**
   - 关键词搜索：适用于精确匹配关键词的场景
   - 语义搜索：适用于需要理解语义的搜索场景
   - 智能搜索：利用大语言模型分析查询意图，动态调整权重

2. **智能搜索权重分析**
   智能搜索模式下，系统会使用大语言模型分析用户的搜索意图，为不同字段分配权重。例如：
   - 对于"悉尼大学商科本科项目"，系统会识别大学名称、学科和学位类型的重要性
   - 对于"人工智能全日制硕士"，系统会识别学科领域、学位和项目类型的重要性

## API参考

### 搜索API
```
GET /api/search?query=<search_term>&use_vector=<true|false>&use_llm=<true|false>&top_k=<num_results>
```

### 获取动态权重API
```
GET /api/weights?query=<search_term>
```

### AI流式搜索API
```
GET /api/ai_stream_search?query=<search_term>
```

## 贡献指南

欢迎提交问题或改进建议。请遵循以下步骤：
1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request 