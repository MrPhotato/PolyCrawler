# SIM项目向量搜索服务

这是一个基于BGE（BAAI General Embedding）和LLM（Large Language Model）的向量搜索服务，用于智能检索SIM（新加坡管理学院）的项目信息。

## 功能特性

- **BGE向量嵌入**：对项目数据生成高质量语义向量
- **MongoDB存储**：使用MongoDB存储向量和原始数据
- **三种搜索模式**：
  - **关键词搜索**：基于文本匹配
  - **语义搜索**：基于向量相似度
  - **智能搜索**：基于LLM动态权重分析

## 安装与设置

### 依赖安装

```bash
pip install -r requirements.txt
```

### 环境变量配置

创建`.env`文件并设置以下变量（参考`.env.example`）：

```
OPENAI_API_KEY=your_openai_api_key_here
MONGODB_URI=mongodb://localhost:27017/
```

### MongoDB设置

启动MongoDB服务：

```bash
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

## 使用方法

### 1. 数据初始化

首次使用前，运行以下命令初始化数据库并生成向量嵌入：

```bash
python vector_embedding.py
```

### 2. 启动API服务

```bash
python vector_search_api.py
```

服务默认在 http://localhost:5000 上运行。

### 3. API端点

- **`/api/search`**: 主搜索API
  - 参数：
    - `query`: 搜索查询文本
    - `use_vector`: 是否使用向量搜索 (true/false)
    - `use_llm`: 是否使用LLM动态权重搜索 (true/false)
    - `top_k`: 返回结果数量上限

- **`/api/weights`**: 获取查询的动态权重配置
  - 参数：
    - `query`: 需要分析的搜索查询

- **`/api/health`**: 健康检查端点

- **`/api/init`**: 重新初始化数据(POST请求)

## LLM动态权重搜索

该服务的核心特性是基于LLM的动态权重分析，其工作原理为：

1. LLM分析用户查询意图，为不同字段分配权重
2. 对权重较高的字段进行优先过滤获取候选文档
3. 结合向量相似度和字段匹配度计算最终分数
4. 返回排序后的结果及使用的权重配置

## 前端集成

前端搜索组件已集成三种搜索模式，用户可以根据需要选择合适的搜索方式：

- **关键词搜索**：精确匹配，速度快
- **语义搜索**：理解查询含义，找到语义相关内容
- **智能搜索**：根据查询动态调整权重，提供最相关结果

## 开发者说明

- `vector_embedding.py`: 核心向量生成和存储模块
- `llm_weight_search.py`: LLM动态权重搜索实现
- `vector_search_api.py`: API服务和请求处理

## 性能优化

服务使用以下技术提高性能：

- 搜索权重缓存机制
- 两阶段检索策略（过滤+重排）
- 异步API处理 