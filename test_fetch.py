import requests

# 目标URL
url = "https://www.sim.edu.sg/degrees-diplomas/programmes/programme-listing/bachelor-of-arts-communication-and-psychology"

# 模拟浏览器的请求头
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

try:
    print(f"正在发送HTTP GET请求到: {url}")
    response = requests.get(url, headers=headers, timeout=30) # 设置30秒超时

    # 检查响应状态码
    if response.status_code == 200:
        print("请求成功！状态码: 200")
        # 打印HTML内容的前500个字符，看看是否是正常的HTML
        print("\nHTML内容（前500字符）:")
        print(response.text[:500])
        print("\n------")
        print(f"完整HTML内容长度: {len(response.text)} 字符")

        # 尝试保存到文件，方便检查
        with open("fetched_page.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        print("HTML内容已保存到 fetched_page.html 文件。")

    else:
        print(f"请求失败！状态码: {response.status_code}")
        print("响应内容:")
        print(response.text[:500]) # 打印部分响应内容以供调试

except requests.exceptions.Timeout:
    print("请求超时！请检查网络连接或增加超时时间。")
except requests.exceptions.RequestException as e:
    print(f"请求过程中发生错误: {e}")
except Exception as e:
    print(f"发生未知错误: {e}") 