from flask import Blueprint, Response, request, stream_with_context
from backend.search.streaming_service import get_llm_response_stream

search_bp = Blueprint('search_bp', __name__)

@search_bp.route('/ai_stream_search', methods=['GET'])
def ai_stream_search_route():
    query = request.args.get('query', '')

    if not query:
        return Response("Query parameter is missing", status=400)

    # 使用真实的LLM流式服务
    return Response(stream_with_context(get_llm_response_stream(query)), mimetype='text/event-stream') 