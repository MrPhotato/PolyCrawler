import pandas as pd
import asyncio
import json
import time
import concurrent.futures
import threading
import queue  # 新增: 用于任务重试队列
from crawling_single_program_detail import ProgramCrawler # 假设 ProgramCrawler 类在此文件中或可导入

def crawl_program_details(url, csv_data, lock, task_retry_data=None):
    """
    使用ProgramCrawler获取项目详细信息（同步包装器）
    
    参数:
        url: 要爬取的URL
        csv_data: CSV行数据
        lock: 文件写入锁
        task_retry_data: 包含重试次数等信息的字典(当是重试任务时提供)
    
    返回:
        成功时返回merged_data，
        失败时返回None（表示需要重试）
    """
    # 获取或初始化重试信息
    if task_retry_data is None:
        task_retry_data = {'attempt': 1}
    else:
        task_retry_data['attempt'] += 1
    
    # 如果达到最大重试次数(全局重试5次)，强制写入错误信息
    max_global_retries = 5
    if task_retry_data['attempt'] > max_global_retries:
        print(f"警告: 已达到全局最大重试次数 {max_global_retries}，URL {url} 将被记录为永久失败")
        merged_data = csv_data.copy()
        merged_data['error'] = f"Failed after {max_global_retries} global retry attempts"
        
        # 写入JSON(只有达到最大重试次数才强制写入)
        with lock:
            try:
                with open("SIM_programs.json", "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                existing_data = []

            if not isinstance(existing_data, list):
                existing_data = []
                
            existing_data.append(merged_data)
            
            with open("SIM_programs.json", "w", encoding="utf-8") as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)
                
            print(f"线程 {threading.current_thread().name}: 达到最大重试次数 {max_global_retries}，将失败数据写入 SIM_programs.json (URL: {url})")
            
        return merged_data  # 返回错误数据，表示处理完成(不再重试)
    
    # API配置
    base_url = "https://api.deepseek.com"
    api_key = "sk-768de9d58b864f7cb54882fc66780bfc"
    crawler = None
    success = False  # 是否成功爬取的标志
    crawled_result = {}  # 初始化爬取结果为空字典
    
    print(f"线程 {threading.current_thread().name}: 开始处理URL {url} (全局尝试 {task_retry_data['attempt']}/{max_global_retries})")

    try:
        # --- URL处理 ---
        if not isinstance(url, str) or not url.strip():
            print(f"无效的URL: {url}，跳过处理。")
            return None  # 返回None表示需要重试
        else:
            if url.startswith('/'):
                full_url = f"https://www.sim.edu.sg{url}"
            elif url and not url.startswith(('http://', 'https://')):
                full_url = f"https://www.sim.edu.sg/{url}"
            else:
                full_url = url

            # --- 爬虫执行 (无局部重试) ---
            crawler = ProgramCrawler(full_url, base_url, api_key)
            
            try:
                print(f"线程 {threading.current_thread().name}: 尝试爬取 {full_url}")
                crawled_result = asyncio.run(crawler.crawl())  # 在线程内运行asyncio事件循环
                
                # 检查结果是否有错误
                if 'error' not in crawled_result:
                    print(f"线程 {threading.current_thread().name}: 爬取成功 {full_url}")
                    success = True
                else:
                    print(f"线程 {threading.current_thread().name}: 爬取包含错误: {crawled_result.get('error', 'Unknown error')}")
                    success = False  # 显式标记失败
            except Exception as e:
                print(f"线程 {threading.current_thread().name}: 爬取过程中捕获到异常 ({url}): {e}")
                crawled_result = {'error': f'Exception during crawl for {url}: {str(e)}'}
                success = False

    except Exception as e:
        print(f"处理 {url} 时发生顶层错误: {e} (线程 {threading.current_thread().name})")
        success = False  # 确保失败

    finally:
        # 确保关闭爬虫资源
        if crawler:
            try:
                print(f"线程 {threading.current_thread().name}: 正在关闭 {url} 的爬虫资源...")
                if asyncio.iscoroutinefunction(getattr(crawler, 'close', None)):
                    asyncio.run(crawler.close())
                elif hasattr(crawler, 'close'):
                    crawler.close()
                print(f"线程 {threading.current_thread().name}: 成功关闭 {url} 的爬虫资源。")
            except Exception as e:
                print(f"关闭 Crawler 时出错 ({url}): {e} (线程 {threading.current_thread().name})")

    # 如果爬取成功，才合并数据并写入JSON
    if success:
        # --- 合并数据 ---
        merged_data = csv_data.copy()
        merged_data.update(crawled_result)

        # --- 加锁写入JSON ---
        with lock:
            try:
                with open("SIM_programs.json", "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                existing_data = []

            if not isinstance(existing_data, list):
                print(f"警告 (线程 {threading.current_thread().name}): SIM_programs.json内容不是列表，将重置。")
                existing_data = []

            existing_data.append(merged_data)  # 追加合并后的数据

            with open("SIM_programs.json", "w", encoding="utf-8") as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)

            print(f"线程 {threading.current_thread().name}: 成功将数据写入 SIM_programs.json (URL: {url}). 当前记录数: {len(existing_data)}")

        return merged_data  # 返回处理结果
    else:
        # 失败了，返回None表示需要重试
        print(f"线程 {threading.current_thread().name}: 处理 {url} 失败，将加入重试队列")
        return None

def main():
    csv_file = "sim_program_listing.csv"
    json_file = "SIM_programs.json"
    max_workers = 3 # 保持较低的并发数
    
    # 定义需要从CSV提取的列及顺序
    csv_columns_ordered = [
        'data_id', 'program_name', 'university', 'discipline', 'sub_discipline', 
        'tags', 'academic_level', 'programme_type', 'application_dates', 
        'fee_range', 'program_link'
    ]
    
    # 初始化JSON文件为空列表
    print(f"初始化或清空JSON文件: {json_file}")
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump([], f)

    # 读取CSV文件
    try:
        df = pd.read_csv(csv_file)
        print(f"成功读取CSV文件: {csv_file}，包含 {len(df)} 行数据。")
        
        # 检查所需列是否存在
        missing_cols = [col for col in csv_columns_ordered if col not in df.columns]
        if missing_cols:
            print(f"错误：CSV文件中缺少以下列: {', '.join(missing_cols)}")
            return
            
    except FileNotFoundError:
        print(f"错误：CSV文件未找到: {csv_file}")
        return
    except Exception as e:
        print(f"读取CSV文件时出错: {e}")
        return

    # 准备要处理的数据：选择列，填充NaN (移除按program_link去重)
    try:
        # 选择需要的列
        df_selected = df[csv_columns_ordered].copy()
        # # 按 program_link 去重，保留第一个出现的行 (已移除)
        # unique_df = df_selected.drop_duplicates(subset=['program_link'], keep='first')
        # 填充 NaN 值为空字符串 ''
        df_filled = df_selected.fillna('') # 使用填充后的DataFrame
        tasks_to_submit = df_filled.to_dict('records') # 将填充后的DataFrame转换为字典列表
        print(f"准备处理 {len(tasks_to_submit)} 个项目链接（未去重）。")
    except Exception as e:
        print(f"处理DataFrame时出错: {e}")
        return
        
    if not tasks_to_submit:
        print("没有找到有效的项目链接来处理。")
        return

    # 创建线程锁用于保护文件写入
    file_lock = threading.Lock()
    
    # 创建任务重试队列
    retry_queue = queue.Queue()
    
    # 记录处理结果统计
    completed_tasks = set() # 追踪已完成的任务ID
    retry_tracking = {} # 用于追踪每个任务的重试次数 {url: {'attempt': count, 'data': csv_data}}
    
    # 首次提交所有任务
    initial_futures = {}
    
    # 统计结果
    success_count = 0
    error_count = 0
    
    # 使用ThreadPoolExecutor进行并发处理
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 首次提交所有任务
        for task_data in tasks_to_submit:
            url = task_data['program_link']
            if url: # 确保URL非空
                future = executor.submit(crawl_program_details, url, task_data, file_lock)
                initial_futures[future] = task_data
                retry_tracking[url] = {'attempt': 1, 'data': task_data}
        
        # 处理初始任务完成情况
        for future in concurrent.futures.as_completed(initial_futures):
            task_data = initial_futures[future]
            url = task_data['program_link']
            
            try:
                result = future.result()
                if result is None:
                    # 任务失败需要重试
                    retry_queue.put((url, task_data))
                    print(f"任务 {url} 加入重试队列，当前队列大小: {retry_queue.qsize()}")
                else:
                    # 任务成功完成
                    completed_tasks.add(url)
                    success_count += 1 if 'error' not in result else 0
                    error_count += 1 if 'error' in result else 0
                    print(f"任务 {url} 处理完成，{'成功' if 'error' not in result else '失败但已记录'}. 成功: {success_count}, 错误: {error_count}, 待重试: {retry_queue.qsize()}")
            except Exception as e:
                print(f"处理任务 {url} 结果时出错: {e}")
                retry_queue.put((url, task_data))
                print(f"由于异常，任务 {url} 加入重试队列")
        
        # 处理重试队列中的任务
        while not retry_queue.empty():
            # 批量获取所有当前待重试的任务
            current_retries = []
            try:
                while not retry_queue.empty():
                    current_retries.append(retry_queue.get_nowait())
            except queue.Empty:
                pass
            
            if not current_retries:
                break
                
            print(f"开始处理 {len(current_retries)} 个待重试任务...")
            
            # 提交所有当前待重试的任务
            retry_futures = {}
            for url, task_data in current_retries:
                if url in retry_tracking:
                    # 使用全局计数作为重试数据
                    future = executor.submit(
                        crawl_program_details, 
                        url, 
                        task_data, 
                        file_lock,
                        {'attempt': retry_tracking[url]['attempt']}
                    )
                    retry_futures[future] = (url, task_data)
                    # 更新重试次数
                    retry_tracking[url]['attempt'] += 1
            
            # 处理重试任务的结果
            for future in concurrent.futures.as_completed(retry_futures):
                url, task_data = retry_futures[future]
                try:
                    result = future.result()
                    if result is None and retry_tracking[url]['attempt'] <= 5:
                        # 如果还需要重试且未达到最大重试次数，再次加入队列
                        retry_queue.put((url, task_data))
                        print(f"重试任务 {url} (尝试 {retry_tracking[url]['attempt']}) 再次加入重试队列")
                    else:
                        # 任务完成或达到最大重试次数
                        completed_tasks.add(url)
                        if result is not None:
                            success_count += 1 if 'error' not in result else 0
                            error_count += 1 if 'error' in result else 0
                        else:
                            error_count += 1
                        print(f"重试任务 {url} {'成功' if result and 'error' not in result else '失败但已记录'} (尝试 {retry_tracking[url]['attempt']}). 成功: {success_count}, 错误: {error_count}")
                except Exception as e:
                    print(f"处理重试任务 {url} 结果时出错: {e}")
                    if retry_tracking[url]['attempt'] <= 5:
                        retry_queue.put((url, task_data))
                        print(f"由于异常，重试任务 {url} 再次加入重试队列")
                    else:
                        print(f"重试任务 {url} 已达到最大重试次数，不再重试")
                        error_count += 1
            
            # 如果队列不为空，等待一会再处理下一批
            if not retry_queue.empty():
                time.sleep(1)
    
    print("\n所有爬取和合并任务已完成。")
    print(f"处理总结: 成功 {success_count} 个, 错误 {error_count} 个.")
    print(f"共完成 {len(completed_tasks)} 个任务，CSV文件共 {len(tasks_to_submit)} 行数据。")
    
    # 检查未完成的任务
    if len(completed_tasks) < len(tasks_to_submit):
        print("警告: 有些任务可能未被处理")
        unprocessed = [task['program_link'] for task in tasks_to_submit 
                    if task['program_link'] and task['program_link'] not in completed_tasks]
        print(f"未处理的任务数: {len(unprocessed)}")
        if unprocessed:
            print(f"前5个未处理的URL: {unprocessed[:5]}")

if __name__ == "__main__":
    main()