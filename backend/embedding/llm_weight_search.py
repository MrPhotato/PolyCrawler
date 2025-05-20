import json
import os
import sys
import asyncio
from typing import Dict, List, Any, Optional, Union
import numpy as np
from pymongo import MongoClient
from openai import OpenAI
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置常量 - 从环境变量获取API配置
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
DASHSCOPE_BASE_URL = os.getenv("DASHSCOPE_BASE_URL")
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "qwen-plus")  # 默认使用qwen-plus但优先使用环境变量
MAX_CACHE_SIZE = 100  # 权重缓存大小

class LLMDynamicWeightSearch:
    """基于LLM的动态权重搜索系统"""
    
    def __init__(self, vector_model, mongodb_collection, api_key=DASHSCOPE_API_KEY, model=LLM_MODEL_NAME):
        """初始化LLM动态权重搜索系统
        
        Args:
            vector_model: 向量嵌入模型实例
            mongodb_collection: MongoDB集合对象
            api_key: LLM API密钥
            model: 使用的LLM模型名称
        """
        self.vector_model = vector_model
        self.collection = mongodb_collection
        
        # 初始化API客户端
        self.client = OpenAI(
            api_key=api_key,
            base_url=DASHSCOPE_BASE_URL,
        )
        self.model = model
        
        # 权重缓存
        self.weight_cache = {}
        
    async def get_dynamic_weights(self, query: str) -> Dict[str, float]:
        """使用LLM分析查询并生成字段权重
        
        Args:
            query: 用户搜索查询
            
        Returns:
            字段权重字典，如 {"program_name": 3.0, "discipline": 2.5, ...}
        """
        # 检查缓存
        cache_key = query.lower().strip()
        if cache_key in self.weight_cache:
            print(f"使用缓存的权重配置: {cache_key}")
            return self.weight_cache[cache_key]
            
        try:
            # 准备LLM提示
            prompt = f"""
            作为教育项目搜索引擎的分析器，分析以下查询，输出用于搜索的最佳字段权重配置。
            
            查询: "{query}"
            
            可用字段:
            - program_name: 项目名称
            - discipline: 学科领域(如商科、IT等)
            - sub_discipline: 子学科(如金融、计算机科学等)
            - university: 大学名称
            - academic_level: 学术水平(本科/硕士等)
            - programme_type: 项目类型(全日制/非全日制)
            - introduction: 项目介绍文本
            - fee_range: 学费范围
            - admission_requirements: 入学要求
            
            分析这个查询的主要意图(如查找特定学科、特定类型或特定学校的项目等)，
            并为每个相关字段分配1.0到5.0的权重值。
            
            仅输出JSON格式，不要任何解释:
            {{
                "字段1": 权重值,
                "字段2": 权重值,
                ...
            }}
            """
            
            # 调用LLM
            response = await asyncio.to_thread(
                lambda: self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "你是一个专门分析教育项目搜索意图的AI助手。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1
                )
            )
            
            # 解析响应
            content = response.choices[0].message.content
            try:
                weights = json.loads(content)
                # 规范化权重
                normalized_weights = {k: min(max(float(v), 1.0), 5.0) for k, v in weights.items()}
                
                # 更新缓存
                if len(self.weight_cache) >= MAX_CACHE_SIZE:
                    # 如果缓存已满，删除一个随机条目
                    self.weight_cache.pop(next(iter(self.weight_cache)))
                self.weight_cache[cache_key] = normalized_weights
                
                print(f"LLM生成的权重: {normalized_weights}")
                return normalized_weights
                
            except json.JSONDecodeError as e:
                print(f"无法解析LLM响应: {e}, 响应内容: {content}")
                # 返回默认权重
                return self._get_default_weights()
                
        except Exception as e:
            print(f"获取动态权重时出错: {e}")
            return self._get_default_weights()
            
    def _get_default_weights(self) -> Dict[str, float]:
        """获取默认权重配置"""
        return {
            "program_name": 3.0,
            "discipline": 2.5,
            "sub_discipline": 2.0,
            "university": 2.0,
            "academic_level": 1.5,
            "programme_type": 1.5,
            "introduction": 1.0
        }
        
    async def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """执行基于LLM动态权重的搜索
        
        Args:
            query: 用户搜索查询
            top_k: 返回结果数量
            
        Returns:
            搜索结果列表及元数据
        """
        if not query or not query.strip():
            return []
            
        # 获取动态权重
        weights = await self.get_dynamic_weights(query)
        
        # 生成查询向量
        query_vec = self.vector_model.encode([query])[0]
        
        # 第一阶段：基于关键词快速过滤潜在相关文档
        query_terms = [term for term in query.split() if len(term) > 2]
        filter_conditions = []
        
        # 为每个字段和查询词生成匹配条件
        for field, weight in weights.items():
            if weight >= 2.0:  # 只对权重较高的字段应用预过滤
                for term in query_terms:
                    filter_conditions.append({field: {"$regex": term, "$options": "i"}})
        
        # 如果有过滤条件，则应用它们
        filter_query = {"$or": filter_conditions} if filter_conditions else {}
        
        # 检索候选文档
        candidates = list(self.collection.find(filter_query))
        if not candidates:
            print(f"未找到匹配'{query}'的候选文档")
            # 如果没有找到匹配项，尝试不使用过滤器
            candidates = list(self.collection.find({}))
            if not candidates:
                return []
        
        # 第二阶段：应用动态权重和向量相似度
        results = []
        for doc in candidates:
            score = 0.0
            
            # 基础向量相似度分数
            if "embedding" in doc:
                doc_vec = np.array(doc["embedding"])
                similarity = np.dot(query_vec, doc_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(doc_vec))
                score += similarity
            
            # 应用字段权重增加分数
            for field, weight in weights.items():
                if field in doc and doc[field]:
                    # 字段匹配加分
                    field_value = str(doc[field]).lower()
                    query_lower = query.lower()
                    
                    # 完全匹配得高分
                    if query_lower in field_value:
                        score += 0.3 * weight
                    # 部分匹配得中等分数
                    elif any(term in field_value for term in query_lower.split()):
                        score += 0.15 * weight
            
            # 创建结果副本，移除嵌入向量减小大小
            result_doc = doc.copy()
            if "embedding" in result_doc:
                del result_doc["embedding"]
            
            # 确保_id是字符串
            if "_id" in result_doc:
                result_doc["_id"] = str(result_doc["_id"])
                
            results.append({
                "document": result_doc,
                "score": float(score),
                "match_info": {
                    "weights_used": weights,
                    "query": query
                }
            })
        
        # 按分数排序并返回前K个结果
        sorted_results = sorted(results, key=lambda x: x["score"], reverse=True)[:top_k]
        
        print(f"LLM权重搜索找到 {len(sorted_results)} 个结果(共 {len(candidates)} 个候选项)")
        return sorted_results 