import json
import os
import sys
from typing import List, Dict, Any, Optional, Union
import numpy as np
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from FlagEmbedding import FlagModel

# 配置常量
MODEL_NAME = 'BAAI/bge-base-en-v1.5'
MONGODB_URI = "mongodb://localhost:27017/"
DB_NAME = "sim_programs"
COLLECTION_NAME = "programs"

# 默认字段权重配置
DEFAULT_FIELD_WEIGHTS = {
    "program_name": 3.0,
    "university": 2.0,
    "discipline": 2.5,
    "sub_discipline": 2.0,
    "tags": 1.5,
    "academic_level": 1.5,
    "programme_type": 1.5,
    "introduction": 1.0
}

class VectorEmbedding:
    def __init__(self, model_name: str = MODEL_NAME, use_fp16: bool = True):
        """初始化BGE模型和MongoDB连接"""
        print("正在加载BGE模型...")
        self.model = FlagModel(
            model_name,
            query_instruction_for_retrieval="Represent this text for retrieval:",
            use_fp16=use_fp16
        )
        print(f"BGE模型 {model_name} 加载完成")
        
        # 初始化MongoDB连接
        self.client = MongoClient(MONGODB_URI)
        self.db = self.client[DB_NAME]
        self.collection = self.db[COLLECTION_NAME]
        print(f"已连接到MongoDB: {MONGODB_URI}, 数据库: {DB_NAME}, 集合: {COLLECTION_NAME}")
    
    def prepare_text_from_program(self, program: Dict[str, Any]) -> str:
        """从项目数据中准备用于生成嵌入的文本"""
        # 组合项目名称、学科、子学科、简介等信息
        text_parts = [
            program.get('program_name', ''),
            program.get('university', ''),
            program.get('discipline', ''),
            program.get('sub_discipline', ''),
            program.get('tags', ''),
            program.get('academic_level', ''),
            program.get('programme_type', ''),
            program.get('introduction', '')
        ]
        # 过滤掉空字符串并用空格连接
        return ' '.join(filter(None, text_parts))
    
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """为文本列表生成嵌入向量"""
        print(f"为 {len(texts)} 条文本生成嵌入向量...")
        embeddings = self.model.encode(texts)
        print(f"嵌入向量生成完成，维度: {embeddings.shape}")
        return embeddings
    
    def generate_weighted_embedding(self, program: Dict[str, Any], field_weights: Dict[str, float] = None) -> np.ndarray:
        """生成考虑字段权重的嵌入向量
        
        Args:
            program: 项目数据字典
            field_weights: 字段权重配置，如果为None则使用默认权重
            
        Returns:
            加权嵌入向量
        """
        # 使用默认权重或传入的权重
        weights = field_weights or DEFAULT_FIELD_WEIGHTS
        
        # 为每个字段单独生成嵌入
        field_embeddings = {}
        total_weight = 0.0
        
        for field, weight in weights.items():
            if field in program and program[field] and isinstance(program[field], str):
                # 提取字段文本
                field_text = str(program[field]).strip()
                if field_text:  # 确保不是空文本
                    # 为字段生成嵌入并乘以权重
                    field_embedding = self.model.encode([field_text])[0] * weight
                    field_embeddings[field] = field_embedding
                    total_weight += weight
        
        # 如果没有生成任何有效的字段嵌入，则使用整体文本
        if not field_embeddings or total_weight == 0:
            return self.model.encode([self.prepare_text_from_program(program)])[0]
        
        # 计算加权平均
        weighted_embedding = np.zeros_like(next(iter(field_embeddings.values())))
        for embedding in field_embeddings.values():
            weighted_embedding += embedding
        
        weighted_embedding = weighted_embedding / total_weight
        
        # 归一化向量
        norm = np.linalg.norm(weighted_embedding)
        if norm > 0:
            weighted_embedding = weighted_embedding / norm
            
        return weighted_embedding
    
    def generate_weighted_embeddings(self, programs: List[Dict[str, Any]], field_weights: Dict[str, float] = None) -> np.ndarray:
        """为多个项目生成加权嵌入向量
        
        Args:
            programs: 项目数据列表
            field_weights: 字段权重配置
            
        Returns:
            加权嵌入向量数组
        """
        print(f"为 {len(programs)} 个项目生成加权嵌入向量...")
        embeddings = []
        
        for i, program in enumerate(programs):
            if i % 100 == 0 and i > 0:
                print(f"已处理 {i}/{len(programs)} 个项目")
                
            embedding = self.generate_weighted_embedding(program, field_weights)
            embeddings.append(embedding)
            
        print(f"加权嵌入向量生成完成")
        return np.array(embeddings)
    
    def store_embeddings_to_mongodb(self, programs: List[Dict[str, Any]], embeddings: np.ndarray) -> None:
        """将嵌入向量存储到MongoDB"""
        print("正在将嵌入向量存储到MongoDB...")
        # 先清空集合
        self.collection.delete_many({})
        
        # 批量插入所有程序和其对应的嵌入向量
        documents = []
        for i, program in enumerate(programs):
            program_copy = program.copy()
            # 将numpy数组转换为Python列表以便JSON序列化
            program_copy['embedding'] = embeddings[i].tolist()
            documents.append(program_copy)
        
        # 批量插入文档
        if documents:
            self.collection.insert_many(documents)
        print(f"成功存储 {len(documents)} 个文档到MongoDB")
    
    def create_vector_index(self) -> None:
        """在MongoDB中创建向量索引（仅适用于MongoDB Atlas）"""
        try:
            # 检查索引是否已存在
            existing_indexes = self.collection.list_indexes()
            index_exists = False
            for index in existing_indexes:
                if 'embedding' in index['key']:
                    index_exists = True
                    break
            
            if not index_exists:
                # 创建常规索引，适用于非Atlas MongoDB实例
                self.collection.create_index("embedding")
                print("创建了常规索引，对于向量搜索功能建议使用MongoDB Atlas")
            else:
                print("向量索引已存在")
        except Exception as e:
            print(f"创建索引时出错: {e}")
            print("如需完整向量搜索功能，请使用MongoDB Atlas并配置向量索引")
    
    def query_similar_documents(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """使用向量相似度搜索相关文档"""
        print(f"搜索与查询相似的文档: {query}")
        query_vec = self.model.encode([query])[0]
        
        # 使用Atlas向量搜索（假设已创建适当的索引）
        try:
            pipeline = [
                {
                    "$vectorSearch": {
                        "index": "vector_index",
                        "path": "embedding",
                        "queryVector": query_vec.tolist(),
                        "numCandidates": top_k * 10,
                        "limit": top_k
                    }
                }
            ]
            results = list(self.collection.aggregate(pipeline))
            if results:
                print(f"找到 {len(results)} 个相关文档")
                return results
        except Exception as e:
            print(f"向量搜索出错，尝试使用替代方法: {e}")
        
        # 替代方法：手动计算相似度（适用于没有配置Atlas向量搜索的情况）
        all_docs = list(self.collection.find({}))
        if not all_docs:
            print("集合中没有文档")
            return []
        
        # 从所有文档中提取嵌入向量
        doc_vecs = [np.array(doc['embedding']) for doc in all_docs]
        
        # 计算余弦相似度
        similarities = [np.dot(query_vec, doc_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(doc_vec)) 
                     for doc_vec in doc_vecs]
        
        # 按相似度排序并获取前k个
        top_indices = np.argsort(similarities)[::-1][:top_k]
        results = [all_docs[i] for i in top_indices]
        print(f"通过手动相似度计算找到 {len(results)} 个相关文档")
        return results

def process_sim_programs(field_weights: Dict[str, float] = None):
    """处理SIM程序数据，生成并存储嵌入向量
    
    Args:
        field_weights: 可选的字段权重配置，默认使用DEFAULT_FIELD_WEIGHTS
    """
    # 读取SIM程序数据
    file_path = os.path.join(os.path.dirname(__file__), "SIM_programs.json")
    with open(file_path, 'r', encoding='utf-8') as f:
        programs = json.load(f)
    
    print(f"加载了 {len(programs)} 个SIM项目")
    
    # 使用的字段权重
    weights = field_weights or DEFAULT_FIELD_WEIGHTS
    print(f"使用的字段权重配置: {weights}")
    
    # 初始化向量嵌入处理器
    vec_processor = VectorEmbedding()
    
    # 生成加权嵌入向量
    embeddings = vec_processor.generate_weighted_embeddings(programs, weights)
    
    # 存储到MongoDB
    vec_processor.store_embeddings_to_mongodb(programs, embeddings)
    
    # 创建向量索引
    vec_processor.create_vector_index()
    
    print("处理完成")

if __name__ == "__main__":
    process_sim_programs() 