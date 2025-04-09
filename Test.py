import time
import csv
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 尝试不同的URL，找一个确定包含Programme Outline的页面
url = "https://www.sim.edu.sg/degrees-diplomas/programmes/programme-listing/master-of-science-gerontology-and-global-ageing"

print(f"正在爬取URL: {url}")
response = requests.get(url)
if response.status_code == 200:
    soup = BeautifulSoup(response.text, "html.parser")

    print("\n\n=== 提取Programme Outline内容 ===\n")
    
    # 打印页面中所有section的ID和class，帮助调试
    print("页面中的section元素:")
    for section in soup.find_all("section"):
        section_id = section.get('id', '无ID')
        section_class = section.get('class', ['无class'])
        print(f"  Section ID: {section_id}, Class: {section_class}")
        
        # 检查是否有container-xxl
        containers = section.find_all("div", class_=lambda c: c and "container-xx" in c)
        if containers:
            for container in containers:
                container_class = container.get('class', ['无class'])
                print(f"    Container Class: {container_class}")
                
                # 检查是否有Programme Outline标题
                headers = container.find_all(string=lambda t: t and "Programme Outline" in t)
                if headers:
                    print(f"      找到Programme Outline文本: {headers[0]}")
    
    print("\n尝试直接查找container-xx开头的元素:")
    container_elements = soup.find_all("div", class_=lambda c: c and "container-xx" in c)
    for container in container_elements:
        container_class = container.get('class', ['无class'])
        print(f"  Container Class: {container_class}")
    
    # 直接寻找所有h1标签，查找包含Programme Outline字样的标题
    # 这样不管它在什么结构里，都能找到
    programme_headers = soup.find_all("h1", class_="sub", string=lambda t: t and "Programme Outline" in t)
    
    if programme_headers:
        print(f"\n找到{len(programme_headers)}个Programme Outline标题")
        
        for i, header in enumerate(programme_headers):
            print(f"\n--- 第{i+1}个Programme Outline标题 ---")
            
            # 找到标题所在的header容器
            header_container = header.parent
            if header_container and "general-content-header" in header_container.get("class", []):
                print("找到header容器")
                
                # 找到container-xx容器(支持任何container-xx前缀的类)
                container = header_container.parent
                container_classes = container.get("class", [])
                
                # 打印container的class以便调试
                print(f"Container的class: {container_classes}")
                
                # 检查是否有任何以container-xx开头的类
                is_container_xx = any(c.startswith("container-xx") for c in container_classes)
                if is_container_xx:
                    print(f"找到container-xx容器")
                    
                    # 在container中找到general-content-body
                    content_body = container.find("div", class_="general-content-body")
                    if content_body:
                        print("找到general-content-body内容")
                        
                        # 打印全部内容
                        body_text = content_body.get_text(separator="\n", strip=True)
                        print("\n内容：")
                        print(body_text)
                        
                        # 如果需要，还可以提取具体的内容块
                        content_blocks = content_body.find_all("div", class_="general-content-block")
                        if content_blocks:
                            print(f"\n找到{len(content_blocks)}个content-block")
                            for j, block in enumerate(content_blocks):
                                block_text = block.get_text(separator="\n", strip=True)
                                print(f"\nBlock {j+1}内容:")
                                print(block_text)
                    else:
                        print("未找到general-content-body")
                else:
                    print("未找到container-xx开头的容器")
            else:
                print("标题不在general-content-header容器中")
    else:
        print("未找到Programme Outline标题")
        
        # 尝试查找任何section中的Programme Outline
        print("\n尝试查找任何section中的Programme Outline...")
        all_sections = soup.find_all("section")
        for section in all_sections:
            # 首先检查section中的container-xx
            containers = section.find_all("div", class_=lambda c: c and "container-xx" in c)
            for container in containers:
                headers = container.find_all(string=lambda t: t and "Programme Outline" in t)
                if headers:
                    print(f"在section的container-xx中找到Programme Outline文本：{headers[0]}")
                    # 找到container中的general-content-body
                    content_body = container.find("div", class_="general-content-body")
                    if content_body:
                        print("找到general-content-body内容")
                        body_text = content_body.get_text(separator="\n", strip=True)
                        print("\n内容：")
                        print(body_text)
                        break
            
            # 如果在container-xx中没找到，直接检查section本身
            if not containers or not headers:
                headers = section.find_all(string=lambda t: t and "Programme Outline" in t)
                if headers:
                    print(f"在section中找到Programme Outline文本：{headers[0]}")
                    # 找到section中的general-content-body
                    content_body = section.find("div", class_="general-content-body")
                    if content_body:
                        print("找到general-content-body内容")
                        body_text = content_body.get_text(separator="\n", strip=True)
                        print("\n内容：")
                        print(body_text)
                        break
    
    # 任何文本内容中包含Programme Outline的搜索
    print("\n尝试查找任何包含'Programme Outline'文本的元素...")
    outline_texts = soup.find_all(string=lambda t: t and "Programme Outline" in t)
    for i, text in enumerate(outline_texts):
        print(f"文本{i+1}: {text}")
        # 尝试查找父元素
        parent = text.parent
        print(f"父元素: {parent.name}, class: {parent.get('class', '无class')}")
        
        # 尝试上溯找到container或section
        current = parent
        for _ in range(5):  # 最多往上找5层
            if current.name == "section" or (current.name == "div" and current.get("class") and any(c.startswith("container-") for c in current.get("class", []))):
                print(f"找到祖先元素: {current.name}, class: {current.get('class', '无class')}")
                # 在这个元素中查找general-content-body
                content_body = current.find("div", class_="general-content-body")
                if content_body:
                    print("在祖先元素中找到general-content-body")
                    body_text = content_body.get_text(separator="\n", strip=True)
                    print(f"内容长度: {len(body_text)} 字符")
                    if len(body_text) > 500:
                        print(body_text[:500] + "...")  # 只显示前500个字符
                    else:
                        print(body_text)
                break
            current = current.parent
            if not current:
                break
else:
    print("请求失败，状态码：", response.status_code)