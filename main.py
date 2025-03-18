import requests
from bs4 import BeautifulSoup
import time
import csv
import certifi
from selenium import webdriver
from selenium.webdriver.common.by import By


session = requests.Session()
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0",
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en,zh-CN;q=0.9,zh;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
    "Referer": "https://www.sim.edu.sg/degrees-diplomas/programmes/programme-listing",
}
base_form_data = {
    "SortBy": "Az",
    "SelectedFilterCopy": "more selected filters",
    "HiddenID": "",
    "SectionPath": "/Degrees-Diplomas/Programmes/Programme-Listing",
    "AcademicLevelItems[0].Value": "1",
    "AcademicLevelItems[0].Name": "Diploma",
    "AcademicLevelItems[1].Value": "2",
    "AcademicLevelItems[1].Name": "Bachelor's Degree",
    "AcademicLevelItems[2].Value": "3",
    "AcademicLevelItems[2].Name": "Postgraduate/Masters",
    "AcademicLevelItems[3].Value": "4",
    "AcademicLevelItems[3].Name": "Certificate/Foundation",
    "ProgrammeTypeItems[0].Value": "1",
    "ProgrammeTypeItems[0].Name": "Full-time",
    "ProgrammeTypeItems[0].IsHidden": "False",
    "ProgrammeTypeItems[1].Value": "2",
    "ProgrammeTypeItems[1].Name": "Part-time",
    "ProgrammeTypeItems[1].IsHidden": "False",
    "ProgrammeTypeItems[2].Value": "3",
    "ProgrammeTypeItems[2].IsHidden": "True",
    "LearningModeItems[0].Value": "1",
    "LearningModeItems[0].Name": "Campus Learning",
    "LearningModeItems[1].Value": "2",
    "LearningModeItems[1].Name": "Online Learning",
    "DisciplineItems[0].ChildItems[0].Value": "3",
    "DisciplineItems[0].ChildItems[0].Name": "Communication",
    "DisciplineItems[0].ChildItems[1].Value": "4",
    "DisciplineItems[0].ChildItems[1].Name": "Design",
    "DisciplineItems[0].ChildItems[2].Value": "7",
    "DisciplineItems[0].ChildItems[2].Name": "Sociology",
    "DisciplineItems[0].ChildItems[3].Value": "8",
    "DisciplineItems[0].ChildItems[3].Name": "Social Sciences ",
    "DisciplineItems[0].ChildItems[4].Value": "9",
    "DisciplineItems[0].ChildItems[4].Name": "Psychology",
    "DisciplineItems[0].ChildItems[5].Value": "29",
    "DisciplineItems[0].ChildItems[5].Name": "International Relations ",
    "DisciplineItems[0].ChildItems[6].Value": "59",
    "DisciplineItems[0].ChildItems[6].Name": "Politics",
    "DisciplineItems[1].ChildItems[0].Value": "10",
    "DisciplineItems[1].ChildItems[0].Name": "Accountancy ",
    "DisciplineItems[1].ChildItems[1].Value": "13",
    "DisciplineItems[1].ChildItems[1].Name": "Banking ",
    "DisciplineItems[1].ChildItems[2].Value": "15",
    "DisciplineItems[1].ChildItems[2].Name": "Business Administration ",
    "DisciplineItems[1].ChildItems[3].Value": "16",
    "DisciplineItems[1].ChildItems[3].Name": "Business Analytics ",
    "DisciplineItems[1].ChildItems[4].Value": "20",
    "DisciplineItems[1].ChildItems[4].Name": "Digital Media ",
    "DisciplineItems[1].ChildItems[5].Value": "21",
    "DisciplineItems[1].ChildItems[5].Name": "Economics ",
    "DisciplineItems[1].ChildItems[6].Value": "22",
    "DisciplineItems[1].ChildItems[6].Name": "Economics and Finance ",
    "DisciplineItems[1].ChildItems[7].Value": "23",
    "DisciplineItems[1].ChildItems[7].Name": "Engineering Business Management",
    "DisciplineItems[1].ChildItems[8].Value": "24",
    "DisciplineItems[1].ChildItems[8].Name": "Entrepreneurship & Innovation ",
    "DisciplineItems[1].ChildItems[9].Value": "25",
    "DisciplineItems[1].ChildItems[9].Name": "Finance ",
    "DisciplineItems[1].ChildItems[10].Value": "26",
    "DisciplineItems[1].ChildItems[10].Name": "Financial Management ",
    "DisciplineItems[1].ChildItems[11].Value": "27",
    "DisciplineItems[1].ChildItems[11].Name": "Human Resource Management ",
    "DisciplineItems[1].ChildItems[12].Value": "28",
    "DisciplineItems[1].ChildItems[12].Name": "International Business ",
    "DisciplineItems[1].ChildItems[13].Value": "30",
    "DisciplineItems[1].ChildItems[13].Name": "Logistics and Supply Chain ",
    "DisciplineItems[1].ChildItems[14].Value": "32",
    "DisciplineItems[1].ChildItems[14].Name": "Management ",
    "DisciplineItems[1].ChildItems[15].Value": "34",
    "DisciplineItems[1].ChildItems[15].Name": "Marketing ",
    "DisciplineItems[1].ChildItems[16].Value": "35",
    "DisciplineItems[1].ChildItems[16].Name": "Organisational Leadership and Change ",
    "DisciplineItems[1].ChildItems[17].Value": "37",
    "DisciplineItems[1].ChildItems[17].Name": "Project Management ",
    "DisciplineItems[1].ChildItems[18].Value": "38",
    "DisciplineItems[1].ChildItems[18].Name": "Retail Marketing ",
    "DisciplineItems[1].ChildItems[19].Value": "39",
    "DisciplineItems[1].ChildItems[19].Name": "Sport and Marketing ",
    "DisciplineItems[1].ChildItems[20].Value": "40",
    "DisciplineItems[1].ChildItems[20].Name": "Strategy ",
    "DisciplineItems[1].ChildItems[21].Value": "41",
    "DisciplineItems[1].ChildItems[21].Name": "Tourism & Hospitality",
    "DisciplineItems[1].ChildItems[22].Value": "60",
    "DisciplineItems[1].ChildItems[22].Name": "Digital Innovation",
    "DisciplineItems[1].ChildItems[23].Value": "61",
    "DisciplineItems[1].ChildItems[23].Name": "Events Management",
    "DisciplineItems[1].ChildItems[24].Value": "63",
    "DisciplineItems[1].ChildItems[24].Name": "International Trade",
    "DisciplineItems[2].ChildItems[0].Value": "42",
    "DisciplineItems[2].ChildItems[0].Name": "Artificial Intelligence",
    "DisciplineItems[2].ChildItems[1].Value": "43",
    "DisciplineItems[2].ChildItems[1].Name": "Big Data",
    "DisciplineItems[2].ChildItems[2].Value": "45",
    "DisciplineItems[2].ChildItems[2].Name": "Cyber Security Management ",
    "DisciplineItems[2].ChildItems[3].Value": "46",
    "DisciplineItems[2].ChildItems[3].Name": "Data Science",
    "DisciplineItems[2].ChildItems[4].Value": "47",
    "DisciplineItems[2].ChildItems[4].Name": "Digital Systems Security",
    "DisciplineItems[2].ChildItems[5].Value": "48",
    "DisciplineItems[2].ChildItems[5].Name": "Financial Technology (FinTech)",
    "DisciplineItems[2].ChildItems[6].Value": "49",
    "DisciplineItems[2].ChildItems[6].Name": "Game and Mobile Development",
    "DisciplineItems[2].ChildItems[7].Value": "50",
    "DisciplineItems[2].ChildItems[7].Name": "Information Technology",
    "DisciplineItems[2].ChildItems[8].Value": "51",
    "DisciplineItems[2].ChildItems[8].Name": "Machine Learning",
    "DisciplineItems[2].ChildItems[9].Value": "52",
    "DisciplineItems[2].ChildItems[9].Name": "Web and Mobile Development",
    "DisciplineItems[2].ChildItems[10].Value": "62",
    "DisciplineItems[2].ChildItems[10].Name": "Data Analytics",
    "DisciplineItems[2].ChildItems[11].Value": "64",
    "DisciplineItems[2].ChildItems[11].Name": "Computer Science",
    "DisciplineItems[3].ChildItems[0].Value": "53",
    "DisciplineItems[3].ChildItems[0].Name": "Aviation",
    "DisciplineItems[3].ChildItems[1].Value": "54",
    "DisciplineItems[3].ChildItems[1].Name": "Construction and Management",
    "DisciplineItems[3].ChildItems[2].Value": "55",
    "DisciplineItems[3].ChildItems[2].Name": "Fashion, Design and Luxury Management",
    "DisciplineItems[3].ChildItems[3].Value": "56",
    "DisciplineItems[3].ChildItems[3].Name": "Geographic Information Science",
    "DisciplineItems[3].ChildItems[4].Value": "57",
    "DisciplineItems[3].ChildItems[4].Name": "Nursing",
    "DisciplineItems[4].ChildItems[0].Value": "58",
    "DisciplineItems[4].ChildItems[0].Name": "Non-discipline specific category",
    "UniversityItems[0].Value": "UnitedKingdom",
    "UniversityItems[0].Name": "United Kingdom",
    "UniversityItems[0].ChildItems[0].Value": "1",
    "UniversityItems[0].ChildItems[0].Name": "University of London",
    "UniversityItems[0].ChildItems[1].Value": "9",
    "UniversityItems[0].ChildItems[1].Name": "The University of Warwick",
    "UniversityItems[0].ChildItems[2].Value": "10",
    "UniversityItems[0].ChildItems[2].Name": "University of Birmingham",
    "UniversityItems[0].ChildItems[3].Value": "11",
    "UniversityItems[0].ChildItems[3].Name": "University of Stirling",
    "UniversityItems[1].Value": "Australia",
    "UniversityItems[1].Name": "Australia",
    "UniversityItems[1].ChildItems[0].Value": "2",
    "UniversityItems[1].ChildItems[0].Name": "La Trobe University ",
    "UniversityItems[1].ChildItems[1].Value": "3",
    "UniversityItems[1].ChildItems[1].Name": "Monash College",
    "UniversityItems[1].ChildItems[2].Value": "4",
    "UniversityItems[1].ChildItems[2].Name": "RMIT University",
    "UniversityItems[1].ChildItems[3].Value": "5",
    "UniversityItems[1].ChildItems[3].Name": "The University of Sydney",
    "UniversityItems[1].ChildItems[4].Value": "6",
    "UniversityItems[1].ChildItems[4].Name": "University of Wollongong",
    "UniversityItems[2].Value": "France",
    "UniversityItems[2].Name": "France",
    "UniversityItems[2].ChildItems[0].Value": "7",
    "UniversityItems[2].ChildItems[0].Name": "Grenoble Ecole de Management",
    "UniversityItems[3].Value": "Singapore",
    "UniversityItems[3].Name": "Singapore",
    "UniversityItems[3].ChildItems[0].Value": "8",
    "UniversityItems[3].ChildItems[0].Name": "SIM Global Education",
    "UniversityItems[4].Value": "USA",
    "UniversityItems[4].Name": "USA",
    "UniversityItems[4].ChildItems[0].Value": "12",
    "UniversityItems[4].ChildItems[0].Name": "University at Buffalo",
    "UniversityItems[5].Value": "Canada",
    "UniversityItems[5].Name": "Canada",
    "UniversityItems[5].ChildItems[0].Value": "13",
    "UniversityItems[5].ChildItems[0].Name": "University of Alberta",
    "SeedValue": "-1020170997",
    "CurrentPage": "1",
    "TotalRecord": "151",
    "PageSize": "9",
    "__RequestVerificationToken": "CfDJ8MGoMzCL_2tJsyM0kNPlHQ0kxCzXrLVJ6VAcOr1vdoJHRhH5f4bDAQBsFd_72_bQcIET4MUoGwTVixMwo8-92KlNNiULfM6DSH0d8wzPGBXGQrgPV9WaGH92dyXow9XYPNp657qaazK6dzMa8jnpWZo",
    "AcademicLevelItems[0].IsChecked": "false",
    "AcademicLevelItems[1].IsChecked": "false",
    "AcademicLevelItems[2].IsChecked": "false",
    "AcademicLevelItems[3].IsChecked": "false",
    "ProgrammeTypeItems[0].IsChecked": "false",
    "ProgrammeTypeItems[1].IsChecked": "false",
    "ProgrammeTypeItems[2].IsChecked": "false",
    "LearningModeItems[0].IsChecked": "false",
    "LearningModeItems[1].IsChecked": "false",
    "DisciplineItems[0].ChildItems[0].IsChecked": "false",
    "DisciplineItems[0].ChildItems[1].IsChecked": "false",
    "DisciplineItems[0].ChildItems[2].IsChecked": "false",
    "DisciplineItems[0].ChildItems[3].IsChecked": "false",
    "DisciplineItems[0].ChildItems[4].IsChecked": "false",
    "DisciplineItems[0].ChildItems[5].IsChecked": "false",
    "DisciplineItems[0].ChildItems[6].IsChecked": "false",
    "DisciplineItems[1].ChildItems[0].IsChecked": "false",
    "DisciplineItems[1].ChildItems[1].IsChecked": "false",
    "DisciplineItems[1].ChildItems[2].IsChecked": "false",
    "DisciplineItems[1].ChildItems[3].IsChecked": "false",
    "DisciplineItems[1].ChildItems[4].IsChecked": "false",
    "DisciplineItems[1].ChildItems[5].IsChecked": "false",
    "DisciplineItems[1].ChildItems[6].IsChecked": "false",
    "DisciplineItems[1].ChildItems[7].IsChecked": "false",
    "DisciplineItems[1].ChildItems[8].IsChecked": "false",
    "DisciplineItems[1].ChildItems[9].IsChecked": "false",
    "DisciplineItems[1].ChildItems[10].IsChecked": "false",
    "DisciplineItems[1].ChildItems[11].IsChecked": "false",
    "DisciplineItems[1].ChildItems[12].IsChecked": "false",
    "DisciplineItems[1].ChildItems[13].IsChecked": "false",
    "DisciplineItems[1].ChildItems[14].IsChecked": "false",
    "DisciplineItems[1].ChildItems[15].IsChecked": "false",
    "DisciplineItems[1].ChildItems[16].IsChecked": "false",
    "DisciplineItems[1].ChildItems[17].IsChecked": "false",
    "DisciplineItems[1].ChildItems[18].IsChecked": "false",
    "DisciplineItems[1].ChildItems[19].IsChecked": "false",
    "DisciplineItems[1].ChildItems[20].IsChecked": "false",
    "DisciplineItems[1].ChildItems[21].IsChecked": "false",
    "DisciplineItems[1].ChildItems[22].IsChecked": "false",
    "DisciplineItems[1].ChildItems[23].IsChecked": "false",
    "DisciplineItems[1].ChildItems[24].IsChecked": "false",
    "DisciplineItems[2].ChildItems[0].IsChecked": "false",
    "DisciplineItems[2].ChildItems[1].IsChecked": "false",
    "DisciplineItems[2].ChildItems[2].IsChecked": "false",
    "DisciplineItems[2].ChildItems[3].IsChecked": "false",
    "DisciplineItems[2].ChildItems[4].IsChecked": "false",
    "DisciplineItems[2].ChildItems[5].IsChecked": "false",
    "DisciplineItems[2].ChildItems[6].IsChecked": "false",
    "DisciplineItems[2].ChildItems[7].IsChecked": "false",
    "DisciplineItems[2].ChildItems[8].IsChecked": "false",
    "DisciplineItems[2].ChildItems[9].IsChecked": "false",
    "DisciplineItems[2].ChildItems[10].IsChecked": "false",
    "DisciplineItems[2].ChildItems[11].IsChecked": "false",
    "DisciplineItems[3].ChildItems[0].IsChecked": "false",
    "DisciplineItems[3].ChildItems[1].IsChecked": "false",
    "DisciplineItems[3].ChildItems[2].IsChecked": "false",
    "DisciplineItems[3].ChildItems[3].IsChecked": "false",
    "DisciplineItems[3].ChildItems[4].IsChecked": "false",
    "DisciplineItems[4].ChildItems[0].IsChecked": "false",
    "UniversityItems[0].IsChecked": "false",
    "UniversityItems[0].ChildItems[0].IsChecked": "false",
    "UniversityItems[0].ChildItems[1].IsChecked": "false",
    "UniversityItems[0].ChildItems[2].IsChecked": "false",
    "UniversityItems[0].ChildItems[3].IsChecked": "false",
    "UniversityItems[1].IsChecked": "false",
    "UniversityItems[1].ChildItems[0].IsChecked": "false",
    "UniversityItems[1].ChildItems[1].IsChecked": "false",
    "UniversityItems[1].ChildItems[2].IsChecked": "false",
    "UniversityItems[1].ChildItems[3].IsChecked": "false",
    "UniversityItems[1].ChildItems[4].IsChecked": "false",
    "UniversityItems[2].IsChecked": "false",
    "UniversityItems[2].ChildItems[0].IsChecked": "false",
    "UniversityItems[3].IsChecked": "false",
    "UniversityItems[3].ChildItems[0].IsChecked": "false",
    "UniversityItems[4].IsChecked": "false",
    "UniversityItems[4].ChildItems[0].IsChecked": "false",
    "UniversityItems[5].IsChecked": "false",
    "UniversityItems[5].ChildItems[0].IsChecked": "false",
}

# 示例：一个列表页链接（根据实际URL更改）
LISTING_URL = "https://www.sim.edu.sg/degrees-diplomas/programmes/programme-listing"

def parse_listing_card(card):
    """
    从单个 listing-card DOM 元素中提取所有主要信息。
    """
    data = {}

    # 1) data-id
    data['data_id'] = card.get('data-id', '')

    # 2) 院校名称（例如 <h6>University at Buffalo</h6>）
    uni_name_tag = card.select_one('.slc-head-title h6')
    if uni_name_tag:
        data['university'] = uni_name_tag.get_text(strip=True)
    else:
        data['university'] = ''

    # 3) 标签（如 Double Major）
    tag_elements = card.select('.slc-tags .slc-tag')
    tags = [tag.get_text(strip=True) for tag in tag_elements]
    data['tags'] = ', '.join(tags) if tags else ''

    # 4) 项目标题、链接
    #    a.slc-title 下的 <span> 一般是项目名称
    title_link_tag = card.select_one('a.slc-title.type-title')
    if title_link_tag:
        data['program_link'] = title_link_tag.get('href', '')
        name_span = title_link_tag.select_one('span')
        if name_span:
            data['program_name'] = name_span.get_text(strip=True)
        else:
            data['program_name'] = ''
    else:
        data['program_link'] = ''
        data['program_name'] = ''

    # 5) 简短描述（例如 slc-content-detail）
    desc_tag = card.select_one('.slc-content-detail.type-desc')
    if desc_tag:
        data['short_desc'] = desc_tag.get_text(strip=True)
    else:
        data['short_desc'] = ''

    # 6) 学术等级、课程类型、申请日期、学费等
    #    在 <div class="slc-info-block"> 里，通过 <p class="type-label"> + <p class="type-lead-desc">
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

    # 如果上述字段不存在，可以给一个默认值
    data.setdefault('academic_level', '')
    data.setdefault('programme_type', '')
    data.setdefault('application_dates', '')
    data.setdefault('fees', '')

    # 7) 图片链接（位于 slc-head-bg-wrap img）
    img_tag = card.select_one('.slc-head-bg-wrap img')
    if img_tag:
        data['image_url'] = img_tag.get('src', '')
    else:
        data['image_url'] = ''

    return data

def crawl_listing_page(url):
    """
    抓取列表页所有 listing-card 信息，并将其保存到 CSV。
    """
    response = requests.post(url, headers=headers,data=base_form_data, verify=certifi.where())
    if response.status_code != 200:
        print(f"Failed to fetch listing page: {url}, status code: {response.status_code}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')

    # 定位所有项目容器
    cards = soup.select('div.listing-card')
    print(f"Found {len(cards)} listing-card elements on the page.")

    data_list = []
    for idx, card in enumerate(cards, start=1):
        info = parse_listing_card(card)
        data_list.append(info)
        print(f"[{idx}] {info.get('program_name', '')} -> {info.get('program_link', '')}")
        time.sleep(0.2)  # 小延时，避免过快抓取

    # 将数据保存到CSV
    fieldnames = [
        'data_id', 'university', 'tags', 'program_name', 'program_link',
        'short_desc', 'academic_level', 'programme_type', 'application_dates',
        'fees', 'image_url'
    ]
    with open("sim_programmes.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in data_list:
            writer.writerow(item)

    print("Scraping complete. Data saved to sim_programmes.csv.")

if __name__ == "__main__":
    crawl_listing_page(LISTING_URL)
