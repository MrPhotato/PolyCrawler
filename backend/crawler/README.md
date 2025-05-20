# SIM项目爬虫与向量搜索服务

本项目包含两个主要功能：
1. 爬取SIM（新加坡管理学院）的项目信息
2. 基于BGE（BAAI General Embedding）的向量搜索服务

## 环境设置

### 安装依赖

```bash
pip install -r requirements.txt
```

### MongoDB设置

需要运行MongoDB服务作为数据存储。推荐使用Docker运行：

```bash
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

## 服务组件

### 1. 爬虫功能

- `sim_crawling_list.py`: 爬取SIM项目列表
- `batch_crawling_details.py`: 批量爬取项目详情
- `crawling_single_program_detail.py`: 爬取单个项目详情

### 2. 向量嵌入和搜索

- `vector_embedding.py`: BGE模型嵌入生成和管理
- `vector_search_api.py`: 提供向量搜索API服务

## 使用方法

### 1. 数据初始化与向量嵌入

运行以下命令生成向量嵌入并存储到MongoDB：

```bash
python vector_embedding.py
```

### 2. 启动向量搜索API服务

```bash
python vector_search_api.py
```

服务默认在 http://localhost:5000 运行，提供以下端点：

- `/api/search`: 搜索API
  - 参数：
    - `query`: 搜索查询文本
    - `use_vector`: 是否使用向量搜索 (true/false)
    - `top_k`: 返回结果数量上限

- `/api/health`: 健康检查
  
- `/api/init`: 重新初始化数据（POST请求）

### 3. 前端集成

前端搜索框已集成向量搜索功能，用户可以选择：
- 关键词搜索：基于传统文本匹配
- 语义搜索：使用BGE模型的向量相似度搜索

## 高级配置

### 使用MongoDB Atlas进行向量搜索

如果您希望使用MongoDB Atlas的向量搜索功能，请修改`vector_embedding.py`中的`MONGODB_URI`，并按照Atlas文档创建向量索引。

### 修改嵌入模型

可以在`vector_embedding.py`中修改`MODEL_NAME`常量，选择其他BGE模型：
- `BAAI/bge-base-en-v1.5`: 英文基础模型
- `BAAI/bge-m3`: 多语言多功能模型 