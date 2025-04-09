import time
import csv
import os
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests


def check_file_access(filename="sim_programmes_disciplines.csv"):
    """
    检查文件是否可读写，如果文件不存在则尝试创建它
    如果无法创建或写入文件，则会引发异常
    """
    try:
        # 检查文件是否存在
        if os.path.exists(filename):
            # 检查文件是否可读
            if not os.access(filename, os.R_OK):
                print(f"警告：文件 {filename} 不可读取")
                return False
                
            # 检查文件是否可写
            if not os.access(filename, os.W_OK):
                print(f"警告：文件 {filename} 不可写入")
                return False
                
            print(f"文件 {filename} 已存在且可读写")
            return True
        else:
            # 文件不存在，尝试创建它
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("")  # 写入空字符串
                print(f"文件 {filename} 已成功创建并可读写")
                return True
            except Exception as e:
                print(f"错误：无法创建文件 {filename}，原因：{e}")
                return False
    except Exception as e:
        print(f"检查文件访问权限时出错：{e}")
        return False


# 解析单个 listing-card，和你原来代码相同
def parse_listing_card(card):
    brief_data = {}

    # 1) data-id
    brief_data['data_id'] = card.get('data-id', '')

    # 2) 院校名称
    uni_name_tag = card.select_one('.slc-head-title h6')
    brief_data['university'] = uni_name_tag.get_text(strip=True) if uni_name_tag else ''

    # 3) 标签
    tag_elements = card.select('.slc-tags .slc-tag')
    tags = [tag.get_text(strip=True) for tag in tag_elements]
    brief_data['tags'] = ', '.join(tags) if tags else ''

    # 4) 项目标题、链接
    title_link_tag = card.select_one('a.slc-title.type-title')
    if title_link_tag:
        href = title_link_tag.get('href', '')
        # 处理相对路径URL
        if href.startswith('/'):
            href = f"https://www.sim.edu.sg{href}"
        elif href and not href.startswith(('http://', 'https://')):
            href = f"https://www.sim.edu.sg/{href}"
            
        brief_data['program_link'] = href
        temp_program_url = href
        name_span = title_link_tag.select_one('span')
        brief_data['program_name'] = name_span.get_text(strip=True) if name_span else ''
    else:
        brief_data['program_link'] = ''
        brief_data['program_name'] = ''
        temp_program_url = ''

    # 5) 简短描述
    desc_tag = card.select_one('.slc-content-detail.type-desc')
    brief_data['short_desc'] = desc_tag.get_text(strip=True) if desc_tag else ''

    # 6) 学术等级、课程类型、申请日期、学费等
    info_blocks = card.select('.slc-info-block')
    for block in info_blocks:
        label_tag = block.select_one('.type-label')
        value_tag = block.select_one('.type-lead-desc')
        if label_tag and value_tag:
            label = label_tag.get_text(strip=True)
            value = value_tag.get_text(strip=True)
            if label == 'Academic Level':
                brief_data['academic_level'] = value
            elif label == 'Programme Type':
                brief_data['programme_type'] = value
            elif label == 'Application Dates':
                brief_data['application_dates'] = value
            elif 'Estimated Fees' in label:
                brief_data['fees'] = value
    # 默认值
    brief_data.setdefault('academic_level', '')
    brief_data.setdefault('programme_type', '')
    brief_data.setdefault('application_dates', '')
    brief_data.setdefault('fees', '')
    try:
        brief_data.update(crawl_program_details(temp_program_url))
    except Exception as e:
        print(f"获取详细信息失败: {temp_program_url}, 错误: {e}")
        brief_data.update({
            'program_outline': '',
            'intake_list': '',
            'curriculum_modules': '',
            'admission_criteria': ''
        })

    return brief_data

def crawl_program_details(url):
    detail_data = {
        'program_outline': '',
        'intake_list': '',
        'curriculum_modules': '',
        'admission_criteria': ''
    }
    
    # 处理相对URL
    if url.startswith('/'):
        url = f"https://www.sim.edu.sg{url}"
    elif url and not url.startswith(('http://', 'https://')):
        url = f"https://www.sim.edu.sg/{url}"
    
    try: # Wrap requests in try-except
        # 添加了 timeout 参数
        response = requests.get(url, timeout=10)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        soup = BeautifulSoup(response.text, "html.parser")
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {url}, 错误: {e}")
        return detail_data

    # --- Program Outline (原General Content) ---
    # 注意：这里获取的 program_outline 可能包含下面专门提取的 admission 或 modules 部分，
    # 如果需要严格区分，后续可能需要更复杂的逻辑来排除。目前保持不变。
    
    # 创建一个用于收集program_outline部分的列表
    program_outline_parts = []
    
    # 1. 首先检查原始的general-content-body
    general_content_body = soup.find("div", class_="general-content-body")
    if general_content_body:
        program_outline_parts.append(general_content_body.get_text(separator="\\n", strip=True))
    else:
        print(f"未找到 general-content-body in {url}")
    
    # 2. 检查section id="outline-outcomes"结构
    outline_section = soup.find("section", id="outline-outcomes")
    if outline_section:
        print(f"找到 outline-outcomes section in {url}")
        # 检查内部是否有container-xx1或container-xxl
        container = outline_section.find(lambda tag: tag.name == "div" and tag.get("class") and any(c.startswith("container-xx") for c in tag.get("class", [])))
        if container:
            # 检查是否有Programme Outline标题
            header = container.find("div", class_="general-content-header")
            if header and header.find("h1", class_="sub", string=lambda t: t and "Programme Outline" in t):
                # 提取content-body内容
                content_body = container.find("div", class_="general-content-body")
                if content_body:
                    # 检查是否有内容块
                    content_blocks = content_body.find_all("div", class_="general-content-block")
                    if content_blocks:
                        blocks_content = []
                        for block in content_blocks:
                            block_text = block.get_text(separator="\\n", strip=True)
                            if block_text:
                                blocks_content.append(block_text)
                                print(f"  提取了outline-outcomes中的内容块，长度: {len(block_text)} in {url}")
                        
                        if blocks_content:
                            program_outline_parts.append("\\n\\n".join(blocks_content))
                        else:
                            program_outline_parts.append(content_body.get_text(separator="\\n", strip=True))
                    else:
                        program_outline_parts.append(content_body.get_text(separator="\\n", strip=True))
                    
                    print(f"从outline-outcomes section提取了Programme Outline内容 in {url}")
    
    # 3. 检查所有section class="general-content"中的Programme Outline
    general_sections = soup.find_all("section", class_="general-content")
    for section in general_sections:
        # 跳过已经处理过的section
        if section.get('id', '') == 'outline-outcomes':
            continue
            
        # 检查内部是否有container-xx开头的容器
        container = section.find(lambda tag: tag.name == "div" and tag.get("class") and any(c.startswith("container-xx") for c in tag.get("class", [])))
        if not container:
            continue
            
        # 检查是否有Programme Outline标题
        header = container.find("div", class_="general-content-header")
        if not header or not header.find("h1", class_="sub", string=lambda t: t and "Programme Outline" in t):
            continue
            
        # 提取content-body内容
        content_body = container.find("div", class_="general-content-body")
        if content_body:
            # 检查是否有内容块
            content_blocks = content_body.find_all("div", class_="general-content-block")
            if content_blocks:
                blocks_content = []
                for block in content_blocks:
                    block_text = block.get_text(separator="\\n", strip=True)
                    if block_text:
                        blocks_content.append(block_text)
                        print(f"  提取了general-content section中的Programme Outline内容块，长度: {len(block_text)} in {url}")
                
                if blocks_content:
                    program_outline_parts.append("\\n\\n".join(blocks_content))
                else:
                    program_outline_parts.append(content_body.get_text(separator="\\n", strip=True))
            else:
                program_outline_parts.append(content_body.get_text(separator="\\n", strip=True))
            
            print(f"从general-content section提取了Programme Outline内容 in {url}")
    
    # 4. 检查单独的general-content-block中的Programme Outline
    all_blocks = soup.find_all("div", class_="general-content-block")
    for block in all_blocks:
        # 检查是否有标题
        h4_tag = block.find("h4")
        if not h4_tag:
            continue
            
        header_text = h4_tag.get_text(strip=True)
        if "Programme Outline" in header_text or "Program Outline" in header_text:
            print(f"找到 '{header_text}' in general-content-block in {url}")
            program_outline_parts.append(block.get_text(separator="\\n", strip=True))
    
    # 合并所有收集到的program outline部分
    if program_outline_parts:
        detail_data['program_outline'] = "\\n\\n".join(program_outline_parts)
    else:
        print(f"最终未找到任何program_outline内容 in {url}")

    # --- Intake List ---
    intake_list_wrap = soup.find("div", class_="intake-list-wrap")
    if intake_list_wrap:
        detail_data['intake_list'] = intake_list_wrap.get_text(separator="\\n", strip=True)
    else:
        print(f"未找到 intake_list in {url}")

    # --- Admission Criteria (优先使用 ID) ---
    admission_criteria_parts = []  # 用于收集所有与入学要求相关的内容

    # 1. 首先检查带ID的部分
    admission_section = soup.find("section", id="admission-criteria")
    if admission_section:
        admission_body = admission_section.find("div", class_="general-content-body")
        if admission_body:
            admission_criteria_parts.append(admission_body.get_text(separator="\\n", strip=True))
        else:
            # 如果 section 里没找到 body，则提取整个 section 内容
            print(f"在 admission-criteria section 中未找到 general-content-body, 提取整个 section 内容 in {url}")
            admission_criteria_parts.append(admission_section.get_text(separator="\\n", strip=True))
    
    # 2. 检查tab-accordion中的入学要求相关内容
    tab_accordions = soup.find_all("div", class_="tab-accordion__accordion-container")
    admission_related_titles = ["Entry Requirements", "English Language Proficiency", "Admission Criteria"]
    
    for accordion in tab_accordions:
        headers = accordion.find_all("div", class_=lambda x: x and ("accordion__header" in x))
        
        for header in headers:
            span_text = header.find("span")
            if span_text and any(title in span_text.get_text(strip=True) for title in admission_related_titles):
                # 获取对应的内容块
                header_class = header.get("class", [])[0]  # 如 accordion__header 或 accordion__header_is-open
                header_id = header.get("id", "")
                
                # 尝试直接找到对应的内容区
                content_div = None
                if header.parent:
                    content_div = header.parent.find("div", class_=lambda x: x and "accordion__content" in x)
                
                # 如果上面方法找不到，尝试使用相邻元素
                if not content_div and header.next_sibling:
                    content_div = header.next_sibling
                    if hasattr(content_div, "class") and not any("accordion__content" in c for c in content_div.get("class", [])):
                        content_div = None
                
                if content_div:
                    section_text = f"{span_text.get_text(strip=True)}:\\n"
                    section_text += content_div.get_text(separator="\\n", strip=True)
                    admission_criteria_parts.append(section_text)
                    print(f"从折叠内容中提取了 '{span_text.get_text(strip=True)}' 部分 in {url}")
    
    # 3. 最后检查 general-content-block 中的内容
    all_blocks = soup.find_all("div", class_="general-content-block")
    for block in all_blocks:
        # 跳过已经在 admission_section 中处理过的 block
        if admission_section and block in admission_section.find_all("div", class_="general-content-block"):
            continue

        h4_tag = block.find("h4")
        if not h4_tag:
            continue  # 需要 h4 标题来识别

        header_text = h4_tag.get_text(strip=True)
        
        # 如果找到 "Admission Criteria" 标题
        if any(title in header_text for title in admission_related_titles):
            print(f"找到 '{header_text}' in general-content-block in {url}")
            admission_criteria_parts.append(block.get_text(separator="\\n", strip=True))

    # 4. 检查带有h1 class="sub"的"Admission Criteria"情况
    # 情况1: container-xx1结构
    container_divs = soup.find_all("div", class_=lambda c: c and c.startswith("container-xx"))
    for container in container_divs:
        header = container.find("div", class_="general-content-header")
        if not header:
            continue
            
        h1_tag = header.find("h1", class_="sub")
        if not h1_tag or "Admission Criteria" not in h1_tag.get_text(strip=True):
            continue
            
        # 找到对应的内容区
        content_body = container.find("div", class_="general-content-body")
        if content_body:
            print(f"找到 'Admission Criteria' in container-xx with h1.sub in {url}")
            # 提取所有内容块
            content_blocks = content_body.find_all("div", class_="general-content-block")
            if content_blocks:
                # 确保获取所有内容块的文本
                blocks_content = []
                for block in content_blocks:
                    block_text = block.get_text(separator="\\n", strip=True)
                    if block_text:  # 只添加非空内容
                        blocks_content.append(block_text)
                        print(f"  提取了一个general-content-block内容，长度: {len(block_text)} in {url}")
                
                if blocks_content:
                    # 合并所有block内容，添加到admission_criteria_parts
                    admission_criteria_parts.append("\\n\\n".join(blocks_content))
                else:
                    # 如果所有块都为空，则提取整个body
                    admission_criteria_parts.append(content_body.get_text(separator="\\n", strip=True))
            else:
                # 如果没有特定的内容块，提取整个body
                admission_criteria_parts.append(content_body.get_text(separator="\\n", strip=True))
    
    # 情况2: section class="general-content"结构
    general_sections = soup.find_all("section", class_="general-content")
    for section in general_sections:
        # 先检查section的id是否与入学要求相关
        section_id = section.get('id', '')
        if section_id in ['application-requirement', 'entry-requirements', 'admission-requirements']:
            print(f"找到入学要求相关section id='{section_id}' in {url}")
            # 提取该section的内容
            content_body = section.find("div", class_="general-content-body")
            if content_body:
                # 检查是否有内容块
                content_blocks = content_body.find_all("div", class_="general-content-block")
                if content_blocks:
                    # 处理所有内容块
                    blocks_content = []
                    for block in content_blocks:
                        block_text = block.get_text(separator="\\n", strip=True)
                        if block_text:
                            blocks_content.append(block_text)
                            print(f"  提取了{section_id}中的内容块，长度: {len(block_text)} in {url}")
                    
                    if blocks_content:
                        admission_criteria_parts.append("\\n\\n".join(blocks_content))
                    else:
                        admission_criteria_parts.append(content_body.get_text(separator="\\n", strip=True))
                else:
                    # 如果没有内容块，提取整个body
                    admission_criteria_parts.append(content_body.get_text(separator="\\n", strip=True))
            else:
                # 如果没有找到body，提取整个section
                admission_criteria_parts.append(section.get_text(separator="\\n", strip=True))
            continue  # 已处理，继续下一个section
            
        # 如果ID不相关，继续检查内部container结构
        container = section.find("div", class_=lambda c: c and c.startswith("container-xx"))
        if not container:
            continue
            
        header = container.find("div", class_="general-content-header")
        if not header:
            continue
            
        h1_tag = header.find("h1", class_="sub")
        if not h1_tag or "Admission Criteria" not in h1_tag.get_text(strip=True):
            continue
        
        # 找到对应的内容区
        content_body = container.find("div", class_="general-content-body")
        if content_body:
            print(f"找到 'Admission Criteria' in section.general-content with h1.sub in {url}")
            # 提取所有内容块
            content_blocks = content_body.find_all("div", class_="general-content-block")
            if content_blocks:
                # 确保获取所有内容块的文本
                blocks_content = []
                for block in content_blocks:
                    block_text = block.get_text(separator="\\n", strip=True)
                    if block_text:  # 只添加非空内容
                        blocks_content.append(block_text)
                        print(f"  提取了section.general-content中的block内容，长度: {len(block_text)} in {url}")
                
                if blocks_content:
                    # 合并所有block内容，添加到admission_criteria_parts
                    admission_criteria_parts.append("\\n\\n".join(blocks_content))
                else:
                    # 如果所有块都为空，则提取整个body
                    admission_criteria_parts.append(content_body.get_text(separator="\\n", strip=True))
            else:
                # 如果没有特定的内容块，提取整个body
                admission_criteria_parts.append(content_body.get_text(separator="\\n", strip=True))
    
    # 情况3: 检查fees-and-financial-aid部分，有时包含入学要求
    financial_aid_section = soup.find("section", id="fees-and-financial-aid")
    if financial_aid_section:
        # 查找该section中是否包含admission相关标题
        admission_headers = financial_aid_section.find_all(["h2", "h3", "h4", "h5"], string=lambda t: t and any(title in t for title in admission_related_titles))
        if admission_headers:
            for header in admission_headers:
                # 尝试提取该标题下的内容
                content = []
                element = header.next_sibling
                while element and element.name not in ["h2", "h3", "h4", "h5"]:
                    if element.name:  # 跳过NavigableString
                        content.append(element.get_text(separator="\\n", strip=True))
                    element = element.next_sibling
                
                if content:
                    admission_criteria_parts.append(f"{header.get_text(strip=True)}:\\n" + "\\n".join(content))
                    print(f"从fees-and-financial-aid部分提取了入学要求内容 in {url}")
    
    # 情况4: 检查普通accordion中的入学要求
    accordion_divs = soup.find_all("div", class_="accordion")
    for accordion_div in accordion_divs:
        # 查找accordion中可能包含admission相关标题的部分
        admission_headers = accordion_div.find_all(["h2", "h3", "h4", "h5"], string=lambda t: t and any(title in t for title in admission_related_titles))
        if admission_headers:
            for header in admission_headers:
                # 找到该header所在的section或div
                parent_section = header.find_parent(["section", "div"])
                if parent_section:
                    admission_criteria_parts.append(f"{header.get_text(strip=True)}:\\n" + parent_section.get_text(separator="\\n", strip=True))
                    print(f"从accordion中提取了'{header.get_text(strip=True)}'相关内容 in {url}")

    # 合并所有收集到的admission criteria部分
    if admission_criteria_parts:
        detail_data['admission_criteria'] = "\\n\\n".join(admission_criteria_parts)
    
    # --- Curriculum / Modules (优先使用 accordion) ---
    accordion = soup.find("div", class_="accordion")
    if accordion:
        # 创建 accordion 的临时副本进行处理，避免修改原始 soup
        temp_soup = BeautifulSoup(str(accordion), 'html.parser')
        temp_accordion_tag = temp_soup.find('div') # 获取最外层的 div

        if temp_accordion_tag:
            accordion_items = temp_accordion_tag.find_all("section", class_="accordion-item")
            for item in accordion_items:
                h5_tag = item.select_one(".accordion-header h5")
                # 过滤掉 "Minors"
                if h5_tag and h5_tag.get_text(strip=True) == "Minors":
                    item.decompose() # 从临时副本中移除
            detail_data['curriculum_modules'] = temp_accordion_tag.get_text(separator="\\n", strip=True)
        else:
            # 解析副本失败，使用原始 accordion 文本
            detail_data['curriculum_modules'] = accordion.get_text(separator="\\n", strip=True)
    # 如果没找到 accordion，尝试找modules相关的general-content-block
    
    # 如果modules还未提取，继续查找特定h4标题的block
    if not detail_data['curriculum_modules']:
        for block in all_blocks:
            # 跳过已经在 accordion 内部处理过的 block
            if accordion and block in accordion.find_all("div", class_="general-content-block"):
                continue

            h4_tag = block.find("h4")
            if not h4_tag:
                continue # 需要 h4 标题来识别

            header_text = h4_tag.get_text(strip=True)

            # 如果找到 "Modules" 标题
            if "Modules" in header_text:
                print(f"找到 'Modules' in general-content-block in {url}")
                detail_data['curriculum_modules'] = block.get_text(separator="\\n", strip=True)
                break  # 找到就退出循环

    # --- Final Checks and Logging ---
    if not detail_data['curriculum_modules']:
        print(f"最终未找到 curriculum/modules content in {url}")
    if not detail_data['admission_criteria']:
        print(f"最终未找到 admission_criteria content in {url}")

    return detail_data

def selenium_crawl_listing(driver):
    """
    使用Selenium从当前页面获取所有列表项
    在discipline筛选条件已经应用的情况下调用
    """
    all_data = []
    page_num = 1
    wait = WebDriverWait(driver, 10)  # 创建一个WebDriverWait对象，最长等待10秒

    while True:
        print(f"Processing page {page_num}...")
        try:
            # 等待页面加载完成，确保列表项可见
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.listing-card')))
            
            # 获取当前页面 HTML 并解析
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            cards = soup.select('div.listing-card')
            print(f"  Found {len(cards)} listing-card elements on this page.")

            # 如果没有找到任何卡片，可能是页面还没加载完或者没有结果
            if not cards:
                print("  No listing cards found on this page.")
                return all_data

            # 解析每个卡片
            for card in cards:
                try:
                    info = parse_listing_card(card)
                    all_data.append(info)
                except Exception as e:
                    print(f"Error parsing card: {e}")
                    continue
            
            # 尝试关闭cookie提示，如果存在的话
            try:
                cookie_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button[data-click="acceptCookie"]')))
                driver.execute_script("arguments[0].click();", cookie_button)
                print("  Closed cookie notification.")
            except:
                pass  # 如果没有找到cookie按钮或等待超时，继续执行
                
            # 查找下一页按钮
            try:
                next_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, f'a[page-number="{page_num + 1}"]')))
                # 确保按钮可点击
                wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f'a[page-number="{page_num + 1}"]')))
                # 使用JavaScript点击，避免元素不可见的问题
                driver.execute_script("arguments[0].click();", next_btn)
                print(f"  Clicked next page button, navigating to page {page_num + 1}")
                # 等待新页面加载
                time.sleep(1.5)
                page_num += 1
            except Exception as e:
                print(f"  No more pages found or error: {e}")
                break  # 如果找不到下一页按钮或点击失败，结束循环
                
        except Exception as e:
            print(f"Error processing page {page_num}: {e}")
            break

    print(f"Finished processing all pages, found {len(all_data)} items in total.")
    return all_data

def crawl_by_disciplines():
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 10)  # 创建一个WebDriverWait对象
    try:
        driver.get("https://www.sim.edu.sg/degrees-diplomas/programmes/programme-listing")
        # 等待页面加载完成
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "p.pl-filter-sub-title")))

        final_data = []  # 用来汇总所有结果

        # 找到所有大类标题元素
        discipline_titles = driver.find_elements(By.CSS_SELECTOR, "p.pl-filter-sub-title")
        print(f"Found {len(discipline_titles)} discipline titles.")

        for discipline_title in discipline_titles:
            try:
                # 取大类名称
                disc_name = discipline_title.find_element(By.TAG_NAME, "span").text.strip()
                print(f"\n--- Discipline: {disc_name} ---")

                # 点击展开大类
                try:
                    wait.until(EC.element_to_be_clickable(discipline_title))
                    driver.execute_script("arguments[0].click();", discipline_title)
                    time.sleep(0.5)
                except Exception as e:
                    print(f"Failed to click {disc_name}: {e}")
                    continue

                # 获取wrap_id并检查有效性
                wrap_id = discipline_title.get_attribute("data-bs-target")
                if not wrap_id:
                    print(f"No data-bs-target found for {disc_name}")
                    continue

                # 等待并查找子类复选框
                try:
                    sub_wrap = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, wrap_id)))
                    sub_checkboxes = sub_wrap.find_elements(By.CSS_SELECTOR, "div.form-field-checkbox input[type='checkbox']")
                except Exception as e:
                    print(f"Error finding checkboxes for {disc_name}: {e}")
                    continue

                for sub_checkbox in sub_checkboxes:
                    try:
                        # 获取子类名称
                        label_el = sub_checkbox.find_element(By.XPATH, "./following-sibling::label")
                        sub_name = label_el.text.strip()
                        print(f"   -> Sub-discipline: {sub_name}")

                        # 点击选中
                        wait.until(EC.element_to_be_clickable(sub_checkbox))
                        driver.execute_script("arguments[0].click();", sub_checkbox)
                        time.sleep(0.5)  # 等待页面刷新

                        # 获取当前过滤条件下的所有项目
                        page_data = selenium_crawl_listing(driver)
                        # 添加分类信息
                        for d in page_data:
                            d["discipline"] = disc_name
                            d["sub_discipline"] = sub_name
                        final_data.extend(page_data)

                        # 取消勾选
                        driver.execute_script("arguments[0].click();", sub_checkbox)
                        time.sleep(0.5)
                    except Exception as e:
                        print(f"Error processing sub-discipline {sub_name}: {e}")
                        continue

                # 点击收起大类
                try:
                    driver.execute_script("arguments[0].click();", discipline_title)
                    time.sleep(0.5)
                except Exception as e:
                    print(f"Failed to fold {disc_name}: {e}")

            except Exception as e:
                print(f"Error processing discipline {disc_name if 'disc_name' in locals() else 'Unknown'}: {e}")
                continue

        return final_data
    finally:
        driver.quit()  # 确保浏览器被关闭


def write_csv(data, filename="sim_programmes_disciplines.csv"):
    """
    写入 CSV，前面多加 discipline, sub_discipline 两列
    其余字段可根据 parse_listing_cards 的输出决定
    """
    # 假设 parse_listing_cards 返回了 "data_id", "program_name", "fees" 等
    # 并且我们手动加了 "discipline", "sub_discipline"
    if not data:
        print("No data to write.")
        return

    # 动态获取所有字段的并集，或手动写死
    fieldnames = list(data[0].keys())
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow(row)
    print(f"已写入 {len(data)} 行数据到 {filename}")


if __name__ == "__main__":
    # 定义默认输出文件名
    output_file = "sim_programmes_disciplines.csv"
    
    # 检查文件访问权限
    if not check_file_access(output_file):
        print("由于文件访问问题，程序无法继续执行。请检查文件权限或指定其他输出位置。")
        exit(1)  # 退出程序，返回错误码
    
    # 继续执行爬虫
    print("开始爬取数据...")
    final_data = crawl_by_disciplines()
    print(f"Total records scraped: {len(final_data)}")
    write_csv(final_data, output_file)
