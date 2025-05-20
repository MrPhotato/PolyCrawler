import os
import json
from openai import OpenAI # 使用 OpenAI 库
from dotenv import load_dotenv

load_dotenv() # 加载 .env 文件中的环境变量

# 从环境变量获取API配置，不在代码中硬编码
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
DASHSCOPE_BASE_URL = os.getenv("DASHSCOPE_BASE_URL")
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "qwen-plus") # 默认使用qwen-plus但优先使用环境变量

# 假设SIM_programs.json在backend目录下
PROGRAM_DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'SIM_programs.json')

AVAILABLE_FILTERS_INFO = {}

def load_program_data_for_llm():
    """加载项目数据并提取各筛选字段的唯一值，供LLM参考"""
    global AVAILABLE_FILTERS_INFO
    try:
        with open(PROGRAM_DATA_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        AVAILABLE_FILTERS_INFO['discipline'] = sorted(list(set(p.get('discipline', '') for p in data if p.get('discipline'))))
        AVAILABLE_FILTERS_INFO['sub_discipline'] = sorted(list(set(p.get('sub_discipline', '') for p in data if p.get('sub_discipline'))))
        AVAILABLE_FILTERS_INFO['university'] = sorted(list(set(p.get('university', '') for p in data if p.get('university'))))
        AVAILABLE_FILTERS_INFO['academic_level'] = sorted(list(set(p.get('academic_level', '') for p in data if p.get('academic_level'))))
        AVAILABLE_FILTERS_INFO['programme_type'] = sorted(list(set(p.get('programme_type', '') for p in data if p.get('programme_type'))))
        AVAILABLE_FILTERS_INFO['fee_range'] = ["0-100000", "100000-150000", "150000-200000", "200000-999999999"]
        print("Successfully loaded filter options for LLM.")
        return True
    except Exception as e:
        print(f"Error loading program data for LLM: {e}")
        return False

# 应用启动时加载一次数据
load_program_data_for_llm()

def get_llm_response_stream(query: str):
    """
    与LLM交互，获取流式响应。
    query: 用户输入的搜索查询。
    """
    if not DASHSCOPE_API_KEY or not DASHSCOPE_BASE_URL:
        print("Error: LLM API key or base URL not configured.")
        yield "data: Error: LLM API key or base URL not configured.\n\n"
        yield "data: <<STREAM_END>>\n\n"
        return

    if not AVAILABLE_FILTERS_INFO:
        print("Error: Filter options for LLM not loaded.")
        yield "data: Error: Filter options for LLM not loaded.\n\n"
        yield "data: <<STREAM_END>>\n\n"
        return

    client = OpenAI(
        api_key=DASHSCOPE_API_KEY,
        base_url=DASHSCOPE_BASE_URL,
    )

    # 为每个筛选字段准备完整的选项列表的JSON字符串
    filter_options_json = {}
    for key in AVAILABLE_FILTERS_INFO:
        filter_options_json[key] = AVAILABLE_FILTERS_INFO[key]
    
    filter_options_str = json.dumps(filter_options_json, ensure_ascii=False)

    system_prompt_content = f"""
你是一个智能课程筛选助手。
你的任务是理解用户的查询，模拟一个清晰的思考过程，然后输出一个JSON对象，指明要应用的筛选条件。

输出规则：
1. 你的思考过程会以文本行的形式逐步输出。请在思考的逻辑断点处使用换行符（\n）来分隔不同的思考步骤或段落。
2. 在思考过程完全结束后，你必须另起一行（或确保清晰分离）输出一个特殊标记：<END_OF_THOUGHTS>
3. 在这个特殊标记之后，紧接着输出一个有效的、单行的、紧凑的JSON对象，这是你整个回复的最后一部分。不得在JSON对象之后添加任何其他文本或换行符。
4. JSON对象的格式必须是：{{"filters": {{"field_name1": ["value1", "value2"], "field_name2": ["value3"]}} }}。
   - field_name 必须是下面提供的可用筛选字段之一。
   - value 必须是对应字段的合理值，且必须严格从提供的选项列表中选择，不要创造不存在的值。
   - 如果某个筛选字段不适用，请不要在JSON中包含该字段。

5. 非常重要：你只能使用系统提供的实际存在的筛选值选项。不要创建或推断不存在的选项值。

请注意标记 <END_OF_THOUGHTS> 必须完整地出现在你的回答中，不要分割这个标记。
"""

    user_prompt_content = f"""
用户的查询是："{query}"。

以下是完整的筛选字段及其所有可用选项：
{filter_options_str}

你必须严格从这些选项中进行选择。如果用户查询的意图在现有选项中找不到完全匹配，请选择最接近的选项或不应用该筛选字段。

现在，开始你的思考过程，并在思考结束后严格按照上述规则输出特殊标记和JSON：
"""
    
    messages = [
        {"role": "system", "content": system_prompt_content},
        {"role": "user", "content": user_prompt_content}
    ]
    print(f"Sending prompt to LLM for query '{query}':\nSystem: {system_prompt_content}\nUser: {user_prompt_content}\n")

    # For handling marker detection across chunks
    thinking_buffer = ""
    thinking_process_ended = False
    json_buffer = ""
    MARKER = "<END_OF_THOUGHTS>"

    try:
        stream = client.chat.completions.create(
            model=LLM_MODEL_NAME,
            messages=messages,
            stream=True,
            temperature=0.3, 
        )
        
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                print(f"<<<LLM_CHUNK_RAW>>>: ---{content}---")

                if not thinking_process_ended:
                    # Add new content to buffer for marker detection
                    thinking_buffer += content
                    
                    # Check for marker in buffer
                    marker_pos = thinking_buffer.find(MARKER)
                    
                    if marker_pos != -1:
                        thinking_process_ended = True
                        
                        # Part before the marker is thinking process
                        before_marker = thinking_buffer[:marker_pos]
                        if before_marker:
                            print(f"<<<SSE_YIELDING (thinking/buffer)>>>: ---{before_marker}---")
                            yield f"data: {before_marker}\n\n"
                        
                        # Yield the marker itself as a special signal
                        print(f"<<<SSE_YIELDING (marker)>>>: ---{MARKER}---")
                        yield f"data: {MARKER}\n\n"
                        
                        # Part after the marker in buffer is start of JSON
                        after_marker = thinking_buffer[marker_pos + len(MARKER):]
                        if after_marker: 
                            json_buffer += after_marker
                            print(f"<<<JSON_BUFFER_INIT>>>: ---{json_buffer}---")
                        
                        # Clear thinking buffer since we've processed it
                        thinking_buffer = ""
                    else:
                        # No marker yet, check if buffer is getting large
                        # Keep last 20 chars in case marker starts but not complete
                        if len(thinking_buffer) > 100: 
                            to_yield = thinking_buffer[:-20]  # Keep last 20 chars in buffer
                            print(f"<<<SSE_YIELDING (thinking/partial)>>>: ---{to_yield}---")
                            yield f"data: {to_yield}\n\n"
                            thinking_buffer = thinking_buffer[-20:]  # Keep potential start of marker
                else:
                    # Thinking process ended, accumulate JSON
                    json_buffer += content
                    print(f"<<<JSON_BUFFER_APPEND>>>: ---{json_buffer}---")
            
            elif chunk.choices and chunk.choices[0].finish_reason == "stop":
                print("<<<LLM_FINISH_REASON>>>: stop")
                break 
        
        # After all chunks are processed, yield any remaining content in thinking buffer
        if not thinking_process_ended and thinking_buffer:
            print(f"<<<SSE_YIELDING (thinking/final)>>>: ---{thinking_buffer}---")
            yield f"data: {thinking_buffer}\n\n"
        
        # Send JSON if marker was found
        if thinking_process_ended and json_buffer.strip():
            final_json_payload = json_buffer.strip()
            print(f"<<<SSE_YIELDING (json_payload)>>>: ---{final_json_payload}---")
            yield f"data: {final_json_payload}\n\n"
        elif thinking_process_ended and not json_buffer.strip():
            print("<<<WARNING>>>: Thinking process ended (marker found) but JSON buffer is empty.")
        elif not thinking_process_ended:
            # If we processed all chunks and never found the marker
            # Do one last check on the entire buffer just in case
            marker_pos = thinking_buffer.find(MARKER)
            if marker_pos != -1:
                print("<<<INFO>>>: Found marker in final buffer check.")
                # Similar processing as in main loop
                before_marker = thinking_buffer[:marker_pos]
                after_marker = thinking_buffer[marker_pos + len(MARKER):]
                
                if before_marker:
                    print(f"<<<SSE_YIELDING (thinking/last-buffer)>>>: ---{before_marker}---")
                    yield f"data: {before_marker}\n\n"
                
                print(f"<<<SSE_YIELDING (marker/last)>>>: ---{MARKER}---")
                yield f"data: {MARKER}\n\n"
                
                if after_marker:
                    json_buffer = after_marker.strip() 
                    print(f"<<<SSE_YIELDING (json_payload/last)>>>: ---{json_buffer}---")
                    yield f"data: {json_buffer}\n\n"
            else:
                print("<<<WARNING>>>: Stream ended but <END_OF_THOUGHTS> marker was not found.")

        yield "data: <<STREAM_END>>\n\n"
        print("<<<SSE_YIELDING (stream_end_signal)>>>: ---<<STREAM_END>>---")

    except OpenAI.APIError as e:
        error_message = f"OpenAI API Error: {str(e)}"
        print(error_message)
        yield f"data: Error: {error_message}\n\n"
        yield "data: <<STREAM_END>>\n\n"
    except Exception as e:
        error_message = f"Unexpected error in LLM service: {str(e)}"
        print(error_message)
        yield f"data: Error: {error_message}\n\n"
        yield "data: <<STREAM_END>>\n\n" 