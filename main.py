import time
import csv
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 解析单个 listing-card，和你原来代码相同
def parse_listing_card(card):
    data = {}

    # 1) data-id
    data['data_id'] = card.get('data-id', '')

    # 2) 院校名称
    uni_name_tag = card.select_one('.slc-head-title h6')
    data['university'] = uni_name_tag.get_text(strip=True) if uni_name_tag else ''

    # 3) 标签
    tag_elements = card.select('.slc-tags .slc-tag')
    tags = [tag.get_text(strip=True) for tag in tag_elements]
    data['tags'] = ', '.join(tags) if tags else ''

    # 4) 项目标题、链接
    title_link_tag = card.select_one('a.slc-title.type-title')
    if title_link_tag:
        data['program_link'] = title_link_tag.get('href', '')
        name_span = title_link_tag.select_one('span')
        data['program_name'] = name_span.get_text(strip=True) if name_span else ''
    else:
        data['program_link'] = ''
        data['program_name'] = ''

    # 5) 简短描述
    desc_tag = card.select_one('.slc-content-detail.type-desc')
    data['short_desc'] = desc_tag.get_text(strip=True) if desc_tag else ''

    # 6) 学术等级、课程类型、申请日期、学费等
    info_blocks = card.select('.slc-info-block')
    for block in info_blocks:
        label_tag = block.select_one('.type-label')
        value_tag = block.select_one('.type-lead-desc')
        if label_tag and value_tag:
            label = label_tag.get_text(strip=True)
            value = value_tag.get_text(strip=True)
            if label == 'Academic Level':
                data['academic_level'] = value
            elif label == 'Programme Type':
                data['programme_type'] = value
            elif label == 'Application Dates':
                data['application_dates'] = value
            elif 'Estimated Fees' in label:
                data['fees'] = value
    # 默认值
    data.setdefault('academic_level', '')
    data.setdefault('programme_type', '')
    data.setdefault('application_dates', '')
    data.setdefault('fees', '')

    return data

def selenium_crawl_listing():
    # 初始化 Chrome 驱动（确保 chromedriver 在 PATH 中）
    driver = webdriver.Chrome()
    # 打开列表页
    LISTING_URL = "https://www.sim.edu.sg/degrees-diplomas/programmes/programme-listing"
    driver.get(LISTING_URL)
    time.sleep(3)  # 等待页面加载

    all_data = []
    page_num = 1

    while True:
        print(f"Processing page {page_num}...")
        # 获取当前页面 HTML 并解析
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        cards = soup.select('div.listing-card')
        print(f"  Found {len(cards)} listing-card elements on this page.")

        for card in cards:
            info = parse_listing_card(card)
            all_data.append(info)
        try:
            button = driver.find_element(By.CSS_SELECTOR, 'button[data-click="acceptCookie"]')
            button.click()
        except Exception as e:
            print("Cookie button not found. Skipping.", e)
        # 尝试点击“Next”按钮；假设该按钮带有 aria-label="Next"

        try:
            next_btn = driver.find_element(By.CSS_SELECTOR, 'a[page-number="{}"]'.format(page_num+1))
            # 滚动到按钮附近并点击
            # driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_btn)
            # driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            driver.execute_script("arguments[0].click();", next_btn)
            time.sleep(1)  # 等待下一页加载
            page_num += 1
        except Exception as e:
            print("Next button not found or click failed. Ending pagination.", e)
            break

    driver.quit()
    return all_data

def write_to_csv(data, filename="sim_programmes_selenium.csv"):
    fieldnames = [
        'data_id', 'university', 'tags', 'program_name', 'program_link',
        'short_desc', 'academic_level', 'programme_type', 'application_dates',
        'fees'
    ]
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow(row)
    print(f"Data saved to {filename}.")

if __name__ == "__main__":
    data = selenium_crawl_listing()
    print(f"Total records scraped: {len(data)}")
    write_to_csv(data)
