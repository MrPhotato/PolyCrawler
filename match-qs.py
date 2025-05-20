import json
import difflib

# 加载QS排名数据
with open('qs_rankings.json', 'r', encoding='utf-8') as f:
    qs_rankings = json.load(f)

# 加载SIM项目数据
with open('crawler/SIM_programs.json', 'r', encoding='utf-8') as f:
    sim_programs = json.load(f)

# 创建结果列表和去重的大学集合
matching_results = []
processed_universities = set()

# 从QS排名中获取所有大学名称
qs_universities = list(qs_rankings.keys())

# 遍历SIM项目
for program in sim_programs:
    # 确保university字段存在
    if 'university' in program and program['university']:
        original_university = program['university']
        
        # 如果这所大学已经处理过，跳过它
        if original_university in processed_universities:
            continue
        
        processed_universities.add(original_university)
        
        # 使用difflib进行模糊匹配，提高匹配阈值到0.75
        matches = difflib.get_close_matches(original_university, qs_universities, n=3, cutoff=0.75)
        
        match_result = {
            "original_university": original_university,
            "matched_university": None,
            "qs_rank": None,
            "matching_score": None
        }
        
        # 如果找到匹配项
        if matches:
            matched_university = matches[0]
            # 计算匹配分数
            matching_score = difflib.SequenceMatcher(None, original_university, matched_university).ratio()
            
            # 特殊处理：修正一些已知的错误匹配
            if original_university == "University of London" and matched_university == "University of Lodz":
                # 尝试匹配更精确的名称
                london_matches = [u for u in qs_universities if "London" in u]
                if london_matches:
                    # 找到包含London的最佳匹配
                    best_match = None
                    best_score = 0
                    for uni in london_matches:
                        score = difflib.SequenceMatcher(None, original_university, uni).ratio()
                        if score > best_score:
                            best_score = score
                            best_match = uni
                    
                    if best_match and best_score > 0.6:
                        matched_university = best_match
                        matching_score = best_score
            
            match_result["matched_university"] = matched_university
            match_result["qs_rank"] = qs_rankings[matched_university]
            match_result["matching_score"] = round(matching_score, 4)
        
        matching_results.append(match_result)

# 按照原始大学名称排序结果
matching_results.sort(key=lambda x: x["original_university"])

# 将结果写入新的JSON文件
with open('university_matches.json', 'w', encoding='utf-8') as f:
    json.dump(matching_results, f, ensure_ascii=False, indent=4)

# 统计
total_universities = len(matching_results)
matched_universities = sum(1 for result in matching_results if result["matched_university"] is not None)
match_rate = round(matched_universities / total_universities * 100, 2) if total_universities > 0 else 0

print(f"匹配结果已保存到 university_matches.json")
print(f"总共处理 {total_universities} 所不同大学，成功匹配 {matched_universities} 所，匹配率 {match_rate}%")
