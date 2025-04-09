import time
import csv
import os
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import asyncio
from ProgramCrawler import ProgramCrawler
import json

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

def crawl_program_details(url, crawler_instance=None):
    """
    使用ProgramCrawler获取项目详细信息，并将结果立即写入JSON文件
    """
    try:
        # 处理相对URL
        if url.startswith('/'):
            url = f"https://www.sim.edu.sg{url}"
        elif url and not url.startswith(('http://', 'https://')):
            url = f"https://www.sim.edu.sg/{url}"
        
        # 设置API配置
        base_url = "https://api.deepseek.com"
        api_key = "sk-768de9d58b864f7cb54882fc66780bfc"
        
        # 创建或使用现有的爬虫实例
        need_to_close = False
        if crawler_instance is None:
            crawler = ProgramCrawler(url, base_url, api_key)
            need_to_close = True
        else:
            crawler = crawler_instance
            # 更新URL
            crawler.url = url
        
        try:
            # 获取数据
            result = asyncio.run(crawler.crawl())
            
            # 如果爬取成功，立即写入文件
            if isinstance(result, dict) and "error" not in result:
                # 读取现有的JSON文件
                try:
                    with open("SIM_programs.json", "r", encoding="utf-8") as f:
                        existing_data = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError):
                    existing_data = []
                
                # 确保existing_data是列表
                if not isinstance(existing_data, list):
                    existing_data = []
                
                # 添加新的数据
                existing_data.append(result)
                
                # 立即写入更新后的数据
                with open("SIM_programs.json", "w", encoding="utf-8") as f:
                    json.dump(existing_data, f, ensure_ascii=False, indent=2)
                
                print(f"成功将数据写入SIM_programs.json，当前共有{len(existing_data)}条记录")
                return result
            else:
                print(f"爬取失败: {result.get('error', '未知错误')}")
                return {
                    'program_outline': '',
                    'intake_list': '',
                    'curriculum_modules': '',
                    'admission_criteria': ''
                }
                
        except Exception as e:
            print(f"爬取过程中出错: {e}")
            return {
                'program_outline': '',
                'intake_list': '',
                'curriculum_modules': '',
                'admission_criteria': ''
            }
        finally:
            # 如果是新创建的爬虫实例，则需要关闭
            if need_to_close:
                try:
                    # 使用 asyncio.run() 来执行异步的 close 方法
                    asyncio.run(crawler.close())
                except Exception as e:
                    print(f"关闭爬虫实例时出错: {e}")
            
    except Exception as e:
        print(f"爬取项目详情时出错: {e}")
        return {
            'program_outline': '',
            'intake_list': '',
            'curriculum_modules': '',
            'admission_criteria': ''
        }

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
    crawler = None  # 用于存储ProgramCrawler实例
    
    try:
        driver.get("https://www.sim.edu.sg/degrees-diplomas/programmes/programme-listing")
        # 等待页面加载完成
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "p.pl-filter-sub-title")))

        final_data = []  # 用来汇总所有结果

        # 找到所有大类标题元素
        discipline_titles = driver.find_elements(By.CSS_SELECTOR, "p.pl-filter-sub-title")
        print(f"Found {len(discipline_titles)} discipline titles.")

        # 创建一个共享的ProgramCrawler实例
        base_url = "https://api.deepseek.com"
        api_key = "sk-768de9d58b864f7cb54882fc66780bfc"
        # 使用一个占位URL初始化
        crawler = ProgramCrawler("", base_url, api_key)

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

                # 处理每个子类
                for checkbox in sub_checkboxes:
                    try:
                        # 获取子类名称
                        label_el = checkbox.find_element(By.XPATH, "./following-sibling::label")
                        sub_name = label_el.text.strip()
                        print(f"   -> Sub-discipline: {sub_name}")

                        # 点击选中
                        wait.until(EC.element_to_be_clickable(checkbox))
                        driver.execute_script("arguments[0].click();", checkbox)
                        time.sleep(0.5)  # 等待页面刷新

                        # 获取当前过滤条件下的所有项目
                        page_data = selenium_crawl_listing(driver)
                        # 添加分类信息
                        for d in page_data:
                            d["discipline"] = disc_name
                            d["sub_discipline"] = sub_name
                        final_data.extend(page_data)

                        # 取消勾选
                        driver.execute_script("arguments[0].click();", checkbox)
                        time.sleep(0.5)
                    except Exception as e:
                        print(f"处理子类时出错: {e}")
                        continue

                # 点击收起大类
                try:
                    driver.execute_script("arguments[0].click();", discipline_title)
                    time.sleep(0.5)
                except Exception as e:
                    print(f"Failed to fold {disc_name}: {e}")

            except Exception as e:
                print(f"处理大类时出错: {e}")
                continue

    finally:
        # 关闭所有资源
        try:
            driver.quit()
        except Exception as e:
            print(f"关闭Selenium浏览器时出错: {e}")
            
        # 关闭爬虫实例
        if crawler is not None:
            try:
                # 使用 asyncio.run() 来执行异步的 close 方法
                asyncio.run(crawler.close())
            except Exception as e:
                print(f"关闭爬虫实例时出错: {e}")

    return final_data


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
    
    
    # 继续执行爬虫
    print("开始爬取数据...")
    final_data = crawl_by_disciplines()
    print(f"Total records scraped: {len(final_data)}")
    # write_csv(final_data, output_file)
