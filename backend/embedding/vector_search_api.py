from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import asyncio
from dotenv import load_dotenv
from vector_embedding import VectorEmbedding, DEFAULT_FIELD_WEIGHTS
from llm_weight_search import LLMDynamicWeightSearch

# 加载环境变量
load_dotenv()

# 获取API密钥和URL从环境变量
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
DASHSCOPE_BASE_URL = os.getenv("DASHSCOPE_BASE_URL")
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "qwen-plus")

app = Flask(__name__)
CORS(app)  # 启用跨域资源共享，以便前端可以访问API

# 初始化向量嵌入处理器
vec_processor = None
llm_searcher = None

@app.route('/api/search', methods=['GET'])
async def search():
    """处理搜索请求"""
    global vec_processor, llm_searcher
    
    # 懒加载向量处理器
    if vec_processor is None:
        vec_processor = VectorEmbedding()
    
    query = request.args.get('query', '')
    use_vector = request.args.get('use_vector', 'false').lower() == 'true'
    use_llm = request.args.get('use_llm', 'false').lower() == 'true'
    top_k = int(request.args.get('top_k', '10'))
    
    if not query:
        return jsonify({"error": "查询不能为空"}), 400
    
    try:
        # LLM动态权重搜索
        if use_llm:
            # 懒加载LLM搜索器
            if llm_searcher is None:
                llm_searcher = LLMDynamicWeightSearch(
                    vector_model=vec_processor.model,
                    mongodb_collection=vec_processor.collection,
                    api_key=DASHSCOPE_API_KEY
                )
                
            results = await llm_searcher.search(query, top_k)
            
            return jsonify({
                "results": [item["document"] for item in results],
                "weights": results[0]["match_info"]["weights_used"] if results else {},
                "search_type": "llm_dynamic_weights",
                "query": query,
                "count": len(results)
            })
                
        # 向量搜索
        elif use_vector:
            # 使用向量搜索
            results = vec_processor.query_similar_documents(query, top_k)
            # 移除嵌入向量以减少响应大小
            for doc in results:
                if 'embedding' in doc:
                    del doc['embedding']
                if '_id' in doc:
                    doc['_id'] = str(doc['_id'])  # 转换ObjectId为字符串
            
            return jsonify({
                "results": results,
                "search_type": "vector",
                "query": query,
                "count": len(results)
            })
        # 常规关键词搜索    
        else:
            # 使用常规关键词搜索 - 在MongoDB中执行文本搜索
            # 这里我们简单使用正则表达式进行文本匹配
            regex_query = {
                "$or": [
                    {"program_name": {"$regex": query, "$options": "i"}},
                    {"university": {"$regex": query, "$options": "i"}},
                    {"discipline": {"$regex": query, "$options": "i"}},
                    {"sub_discipline": {"$regex": query, "$options": "i"}},
                    {"introduction": {"$regex": query, "$options": "i"}}
                ]
            }
            
            results = list(vec_processor.collection.find(regex_query).limit(top_k))
            # 移除嵌入向量以减少响应大小
            for doc in results:
                if 'embedding' in doc:
                    del doc['embedding']
                if '_id' in doc:
                    doc['_id'] = str(doc['_id'])  # 转换ObjectId为字符串
            
            return jsonify({
                "results": results,
                "search_type": "keyword",
                "query": query,
                "count": len(results)
            })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({"status": "ok", "message": "向量搜索API服务正常运行"})

@app.route('/api/init', methods=['POST'])
async def init_data():
    """初始化数据端点 - 从SIM_programs.json重新加载数据并生成嵌入"""
    global vec_processor, llm_searcher
    
    try:
        # 使用默认权重初始化数据
        from vector_embedding import process_sim_programs
        process_sim_programs()
        
        # 重新加载向量处理器
        vec_processor = VectorEmbedding()
        llm_searcher = None  # 重置LLM搜索器，会在下次查询时重新初始化
        
        return jsonify({
            "status": "success", 
            "message": "数据初始化完成，已重新生成嵌入向量并存储到MongoDB",
            "weights_used": DEFAULT_FIELD_WEIGHTS
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
@app.route('/api/weights', methods=['GET'])
async def get_weights_for_query():
    """获取查询的动态权重配置"""
    global vec_processor, llm_searcher
    
    query = request.args.get('query', '')
    if not query:
        return jsonify({"error": "查询不能为空"}), 400
    
    try:
        # 懒加载LLM搜索器
        if llm_searcher is None:
            if vec_processor is None:
                vec_processor = VectorEmbedding()
                
            llm_searcher = LLMDynamicWeightSearch(
                vector_model=vec_processor.model,
                mongodb_collection=vec_processor.collection,
                api_key=DASHSCOPE_API_KEY
            )
            
        # 获取动态权重配置
        weights = await llm_searcher.get_dynamic_weights(query)
        
        return jsonify({
            "query": query,
            "weights": weights,
            "status": "success"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 让Flask异步处理请求
def run_async(debug=True):
    """使Flask应用支持异步处理请求"""
    import asyncio
    from hypercorn.asyncio import serve
    from hypercorn.config import Config
    
    config = Config()
    config.bind = ["0.0.0.0:5000"]
    config.debug = debug
    
    asyncio.run(serve(app, config))

if __name__ == '__main__':
    # 初始化向量嵌入处理器
    vec_processor = VectorEmbedding()
    
    # 使用异步方式运行Flask应用
    run_async(debug=True) 