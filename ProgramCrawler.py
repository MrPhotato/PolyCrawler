import asyncio
import json
import os
import re # Import re for parsing corrected JSON
import requests
import aiohttp # 引入 aiohttp
import html2text # 引入 html2text
import datetime # 引入 datetime 模块
from bs4 import BeautifulSoup, Comment # 引入 BeautifulSoup 和 Comment
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
# 移除了 crawl4ai 的 AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
# 但保留 LLMConfig 和 LLMExtractionStrategy 用于配置和 schema
from crawl4ai import LLMConfig
# from crawl4ai.extraction_strategy import LLMExtractionStrategy # 不再直接使用其实例方法

class Course(BaseModel):
    course_name: str = Field(description="课程名称")
    course_description: str = Field(description="课程描述，可以包括学分", default="")

class CourseModule(BaseModel):
    module_name: str = Field(description="课程模块名称")
    course_modules: List[Course] = Field(description="课程列表")

class AdmissionRequirement(BaseModel):
    requirement_type: str = Field(description="要求类型，如学术要求、语言要求等")
    requirement_description: str = Field(description="描述额外需求")
    specific_requirements: dict = Field(description="具体要求，例如{'TOEFL': '90', 'GPA': '3.0'}")

class ProgramInfo(BaseModel):
    program_name: str = Field(description="项目全名")
    university: str = Field(description="项目合作大学/学院名称")
    introduction: str = Field(description="项目简介")
    academic_level: str = Field(description="学术级别，如本科、硕士等")
    programme_type: str = Field(description="项目类型，如全日制4年制")
    domestic_total_fee: Optional[str] = Field(description="国内总学费", default="")
    international_total_fee: Optional[str] = Field(description="国际总学费", default="")
    application_period: Optional[str] = Field(description="申请时间", default="")
    course_modules: List[CourseModule] = Field(description="课程模块列表")
    admission_requirements: Dict[str, List[AdmissionRequirement]] = Field(description="录取要求，按国际生、国内生分两类，每个类别下包含具体的要求")

class ProgramCrawler:
    MAX_REFINEMENT_ATTEMPTS = 3 # Maximum correction attempts

    def __init__(self, url: str, base_url: str, api_key: str):
        self.url = url
        self.base_url = base_url # DeepSeek API base URL
        self.api_key = api_key
        self.session = None # requests session for fetch_html
        self.aiohttp_session = None # aiohttp session for API call
        
    def get_session(self):
        """获取或创建requests HTTP会话"""
        if self.session is None:
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            })
        return self.session
        
    async def get_aiohttp_session(self):
        """获取或创建aiohttp HTTP会话"""
        if self.aiohttp_session is None:
            self.aiohttp_session = aiohttp.ClientSession()
        return self.aiohttp_session

    def fetch_html(self, url: str) -> Optional[str]:
        """使用requests同步获取网页HTML内容"""
        try:
            print(f"开始发送HTTP请求 (requests): {url}")
            session = self.get_session()
            response = session.get(url, timeout=60)
            response.raise_for_status()
            html = response.text
            print(f"成功获取HTML内容，长度: {len(html)} 字符")
            return html
        except requests.RequestException as e:
            print(f"HTTP请求错误 (requests): {type(e).__name__} - {e}")
            return None
        except Exception as e:
            print(f"获取HTML内容时出错: {type(e).__name__} - {e}")
            return None

    def clean_html_to_markdown(self, html_content: str) -> str:
        """使用BeautifulSoup清理HTML并转换为Markdown"""
        print("开始清理HTML并转换为Markdown...")
        soup = BeautifulSoup(html_content, 'lxml')
        
        # 移除不需要的标签
        tags_to_remove = ['script', 'style', 'meta', 'link', 'header', 'footer', 'nav', 'aside']
        for tag_name in tags_to_remove:
            for tag in soup.find_all(tag_name):
                tag.decompose()
        
        # 移除注释
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()
            
        # 获取body内容，如果找不到则使用整个soup
        body = soup.find('body')
        target_html = str(body) if body else str(soup)
        
        # 配置html2text
        h = html2text.HTML2Text()
        h.ignore_links = False # 保留链接
        h.ignore_images = True # 忽略图片
        h.body_width = 0 # 不自动换行
        h.single_line_break = True # 将<br>转为单个换行符
        
        try:
            markdown_content = h.handle(target_html)
            print(f"HTML成功转换为Markdown，长度: {len(markdown_content)} 字符")
            
            # 将转换后的Markdown写入文件以供检查
            try:
                with open("cleaned_output.md", "w", encoding="utf-8") as f:
                    f.write(markdown_content)
                print("清理后的Markdown已保存到 cleaned_output.md 文件。")
            except Exception as e:
                print(f"保存清理后的Markdown到文件时出错: {e}")
                
            return markdown_content
        except Exception as e:
            print(f"html2text转换时出错: {e}")
            # 转换失败时，回退到纯文本提取
            print("回退到纯文本提取...")
            if body:
                 cleaned_text = body.get_text(separator='\n', strip=True)
            else:
                 cleaned_text = soup.get_text(separator='\n', strip=True)
            print(f"纯文本长度: {len(cleaned_text)} 字符")
            return cleaned_text

    async def _call_deepseek_api(self, messages: List[Dict[str, str]], max_tokens: int, temperature: float = 0.0) -> Dict[str, Any]:
        """通用函数，用于调用DeepSeek API"""
        api_endpoint = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "deepseek-chat",
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        
        try:
            # 打印系统时间
            print(f"当前系统时间: {datetime.datetime.now()}")
            print(f"发送请求到 DeepSeek API ({messages[-1]['role']}...) Timeout: {180 if max_tokens > 1000 else 60}")
            session = await self.get_aiohttp_session()
            # 根据max_tokens调整超时
            timeout = 180 if max_tokens > 1000 else 60
            async with session.post(api_endpoint, headers=headers, json=payload, timeout=timeout) as response:
                response_data = await response.json()
                if response.status == 200:
                    print(f"DeepSeek API 请求成功 (状态码: {response.status})")
                    return {"success": True, "data": response_data}
                else:
                    print(f"DeepSeek API 请求失败！状态码: {response.status}")
                    print("API错误信息:", response_data)
                    return {"success": False, "error": f"API request failed with status {response.status}", "details": response_data}
        except aiohttp.ClientError as e:
            print(f"请求 DeepSeek API 时发生网络错误: {e}")
            return {"success": False, "error": f"Network error during API call: {e}"}
        except asyncio.TimeoutError:
             print(f"请求 DeepSeek API 超时 (Timeout: {timeout}s)")
             return {"success": False, "error": "API call timed out"}
        except Exception as e:
            print(f"调用 DeepSeek API 过程中发生未知错误: {type(e).__name__} - {e}")
            return {"success": False, "error": f"An unexpected error occurred during API call: {e}"}

    def _parse_llm_json_response(self, response_data: Dict[str, Any]) -> tuple[Optional[Dict], str]:
        """解析LLM返回的JSON内容，处理Markdown代码块"""
        assistant_message_content = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
        if not assistant_message_content:
            return None, "Empty content in API response"

        cleaned_json_string = assistant_message_content.strip()
        # 改进清理逻辑以应对不同的代码块标记
        match = re.match(r"^```(?:json)?\s*(.*?)\s*```$", cleaned_json_string, re.DOTALL | re.IGNORECASE)
        if match:
            cleaned_json_string = match.group(1).strip()
        elif cleaned_json_string.startswith("```") and cleaned_json_string.endswith("```"):
             # 备用：简单移除首尾```
             cleaned_json_string = cleaned_json_string[3:-3].strip()
        
        try:
            structured_data = json.loads(cleaned_json_string)
            return structured_data, "Success"
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse JSON: {e}"
            print(error_msg)
            print("Attempted to parse:", cleaned_json_string)
            print("Original API content:", assistant_message_content)
            return None, error_msg

    async def crawl(self) -> Dict[str, Any]:
        """获取HTML，清理，提取信息，并进行迭代验证和修正"""
        print(f"开始爬取: {self.url}")
        
        # 1. 获取HTML和清理
        html_content = self.fetch_html(self.url)
        if html_content is None: return {"error": "Failed to fetch HTML content"}
        cleaned_markdown = self.clean_html_to_markdown(html_content)
        if not cleaned_markdown: return {"error": "Cleaned Markdown content is empty"}
            
        # --- 初始提取 --- 
        print("--- 开始初始提取 ---")
        extraction_instruction = f"""
        请从此Markdown内容中提取信息，并严格按照以下JSON Schema格式化输出:
        ```json
        {json.dumps(ProgramInfo.model_json_schema(), indent=2)}
        ```
        (指令的其余部分，如关键信息点)
        确保提取的信息准确完整。只输出符合Schema的JSON对象，不要包含任何额外的解释或标记。
        以下是需要处理的Markdown内容:
        ```markdown
        {cleaned_markdown}
        ```
        """
        messages = [
             {"role": "system", "content": "你是一个精确的数据提取助手，根据用户提供的Schema和Markdown内容提取信息，并只输出JSON对象。"},
             {"role": "user", "content": extraction_instruction}
        ]
        api_result = await self._call_deepseek_api(messages, max_tokens=8000)
        
        if not api_result["success"]:
            return {"error": "Initial extraction API call failed", "details": api_result.get("error", "Unknown API error")}
            
        current_json, parse_error = self._parse_llm_json_response(api_result["data"])
        if current_json is None:
            return {"error": "Failed to parse initial extraction JSON", "details": parse_error}
            
        # --- 迭代验证和修正循环 --- 
        validation_reason = "Initial extraction seems ok, proceeding to validation."
        for attempt in range(self.MAX_REFINEMENT_ATTEMPTS):
            print(f"--- 开始第 {attempt + 1} 次验证/修正 ---")
            
            validation_prompt = f"""
            You are a data validation expert. You are given a target JSON schema, a Markdown text, and a JSON object supposedly extracted from the text according to the schema.

            Target JSON Schema:
            ```json
            {json.dumps(ProgramInfo.model_json_schema(), indent=2)}
            ```

            Your task is to:
            1. Compare the information in the provided JSON object with the information present in the Markdown text.
            2. Assess if the JSON object accurately, completely, and logically represents the key information *as defined by the Target JSON Schema*, based on the Markdown text. Fields not defined in the schema should be ignored for validation.
            3. **Verify that the JSON object's hierarchy and format strictly adhere to the Target JSON Schema.**
            4. Output ONLY "True" or "False" as the very first word on the first line, indicating whether the JSON is a valid, logical, and correctly formatted extraction *according to the schema*.
            5. On the next line, provide a brief, one-sentence reason for your assessment.
            6. **IMPORTANT: If the first line is "False", output the corrected JSON object (adhering to the schema's content, hierarchy, and format) starting from the third line.** Use the provided Markdown to make corrections only for the fields defined in the schema.

            Markdown Text:
            ```markdown
            {cleaned_markdown}
            ```

            JSON to Validate:
            ```json
            {json.dumps(current_json, indent=2, ensure_ascii=False)}
            ```

            Does the JSON correctly represent the information defined in the schema (including hierarchy and format) based on the text? (Start your response with True or False):
            Reason:
            (Corrected JSON if False):
            """
            
            messages = [
                {"role": "system", "content": "You are a meticulous data validator comparing JSON against a schema (including structure) and Markdown. Respond with True/False, a reason, and optionally a corrected schema-compliant JSON."},
                {"role": "user", "content": validation_prompt}
            ]
            
            api_result = await self._call_deepseek_api(messages, max_tokens=8000)
            
            if not api_result["success"]:
                 print(f"第 {attempt + 1} 次验证API调用失败，中止修正。")
                 return {"error": f"Validation/Correction API call failed (Attempt {attempt + 1})", "last_json": current_json, "details": api_result.get("error")}
                 
            validation_content = api_result["data"].get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            if not validation_content:
                  print(f"第 {attempt + 1} 次验证响应为空，中止修正。")
                  return {"error": f"Empty validation/correction response (Attempt {attempt + 1})", "last_json": current_json}
                  
            print(f"验证/修正响应内容 (Attempt {attempt+1}): \n{validation_content}")
            
            lines = validation_content.split('\n', 2) 
            is_valid_str = lines[0].strip().lower()
            validation_reason = lines[1].strip() if len(lines) > 1 else "No reason provided."
            
            if is_valid_str == "true":
                print(f"验证通过 (Attempt {attempt + 1})! Reason: {validation_reason}")
                return current_json 
            elif is_valid_str == "false":
                print(f"验证失败 (Attempt {attempt + 1}). Reason: {validation_reason}. 尝试解析修正后的JSON...")
                if len(lines) > 2:
                    raw_corrected_json_str = lines[2].strip()
                    json_start_index = -1
                    first_brace = raw_corrected_json_str.find('{')
                    first_bracket = raw_corrected_json_str.find('[')
                    if first_brace != -1 and first_bracket != -1: json_start_index = min(first_brace, first_bracket)
                    elif first_brace != -1: json_start_index = first_brace
                    elif first_bracket != -1: json_start_index = first_bracket
                    if json_start_index != -1:
                        potential_json_str = raw_corrected_json_str[json_start_index:]
                        if potential_json_str.endswith("```"): potential_json_str = potential_json_str[:-3].strip()
                        try:
                            corrected_json = json.loads(potential_json_str)
                            print("成功解析修正后的JSON，进入下一次迭代。")
                            current_json = corrected_json
                            continue 
                        except json.JSONDecodeError as e:
                             parse_error = f"Failed to parse corrected JSON: {e}"
                             print(f"无法解析修正后的JSON: {parse_error}")
                             print("尝试解析的字符串:", potential_json_str)
                             return {"error": f"Failed to parse corrected JSON (Attempt {attempt + 1})", "reason": validation_reason, "last_json": current_json, "raw_correction": raw_corrected_json_str}
                    else:
                        print("在修正部分未找到有效的JSON开始标记 ({ 或 [)。中止修正。")
                        return {"error": f"Could not find start of corrected JSON (Attempt {attempt + 1})", "reason": validation_reason, "last_json": current_json, "raw_correction": raw_corrected_json_str}
                else:
                    print("验证失败，但未找到修正后的JSON。中止修正。")
                    return {"error": f"Validation failed but no corrected JSON found (Attempt {attempt + 1})", "reason": validation_reason, "last_json": current_json}
            else:
                print(f"第 {attempt + 1} 次验证响应格式无效 (未以True/False开头)。中止修正。")
                return {"error": f"Invalid validation response format (Attempt {attempt + 1})", "reason": validation_reason, "last_json": current_json, "raw_response": validation_content}
                
        # 如果循环结束仍未验证通过
        print(f"已达到最大修正次数 ({self.MAX_REFINEMENT_ATTEMPTS})，验证仍未通过。")
        return {"error": f"Validation failed after {self.MAX_REFINEMENT_ATTEMPTS} attempts", "reason": validation_reason, "last_json": current_json}

    async def close(self):
        """关闭请求会话"""
        if self.session:
            self.session.close()
            self.session = None
            print("requests HTTP会话已关闭")
        if self.aiohttp_session and not self.aiohttp_session.closed:
            await self.aiohttp_session.close()
            self.aiohttp_session = None
            print("aiohttp HTTP会话已关闭")

async def main():
    # 示例用法
    url = "https://www.sim.edu.sg/degrees-diplomas/programmes/programme-listing/bachelor-of-arts-communication-and-psychology"
    base_url = "https://api.deepseek.com"
    api_key = "sk-768de9d58b864f7cb54882fc66780bfc"
    
    crawler = ProgramCrawler(url, base_url, api_key)
    try:
        result = await crawler.crawl()
        print("--- 最终结果 ---")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    finally:
        # 关闭会话
        await crawler.close() # close 现在是异步的

if __name__ == "__main__":
    asyncio.run(main()) 