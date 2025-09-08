import requests
import os
import re

# 来源URL
source_url = 'https://raw.githubusercontent.com/mursor1985/LIVE/refs/heads/main/iptv.m3u'

# 目标文件路径（在repo中）
target_file = 'bptv.m3u'

# 支持的路径
supported_paths = ['mg', 'mcp', 'mxw']

# 下载来源M3U内容
try:
    source_response = requests.get(source_url, timeout=10)
    source_response.raise_for_status()
    source_content = source_response.text
except requests.RequestException as e:
    print(f"Error fetching source {source_url}: {e}")
    exit(1)

# 解析来源，提取 (path, ID) -> (域名, params_dict)
source_tokens = {}
lines = source_content.splitlines()
i = 0
while i < len(lines):
    if lines[i].startswith('#EXTINF:'):
        if i + 1 < len(lines):
            url = lines[i + 1]
            # 修改正则表达式，支持非数字ID
            match = re.match(r'https?://([^/]+)/(' + '|'.join(supported_paths) + r')/([^/]+)\.m3u8(?:\?(.*))?', url)
            if match:
                domain = match.group(1)
                path = match.group(2)
                id_part = match.group(3)
                query = match.group(4) or ''
                # 解析查询参数为字典
                params = {}
                for param in re.findall(r'([^&?]+)=([^&]+)', query):
                    params[param[0]] = param[1]
                source_tokens[(path, id_part)] = (domain, params)
                print(f"Found params for {path}/{id_part}: domain={domain}, params={params}")
        i += 2
    else:
        i += 1

if not source_tokens:
    print("No tokens found in source. Exiting.")
    exit(1)

# 读取目标文件
if not os.path.exists(target_file):
    print(f"Target file {target_file} not found. Exiting.")
    exit(1)

try:
    with open(target_file, 'r', encoding='utf-8') as f:
        target_content = f.read()
except Exception as e:
    print(f"Error reading target file {target_file}: {e}")
    exit(1)

# 替换目标文件的域名和参数
updated_lines = []
lines = target_content.splitlines()
i = 0
has_changes = False
while i < len(lines):
    line = lines[i]
    updated_lines.append(line)
    if line.startswith('#EXTINF:'):
        if i + 1 < len(lines):
            url = lines[i + 1]
            # 修改正则表达式，支持非数字ID
            match = re.match(r'https?://([^/]+)/(' + '|'.join(supported_paths) + r')/([^/]+)\.m3u8(?:\?(.*))?', url)
            if match:
                current_domain = match.group(1)
                path = match.group(2)
                id_part = match.group(3)
                query = match.group(4) or ''
                current_params = {}
                for param in re.findall(r'([^&?]+)=([^&]+)', query):
                    current_params[param[0]] = param[1]
                
                key = (path, id_part)
                if key in source_tokens:
                    new_domain, new_params = source_tokens[key]
                    # 比较域名和参数（忽略顺序）
                    if current_domain != new_domain or set(current_params.items()) != set(new_params.items()):
                        # 构建新查询字符串，排序键以保持一致
                        new_query = '&'.join(f"{k}={new_params[k]}" for k in sorted(new_params)) if new_params else ''
                        new_url = f"https://{new_domain}/{path}/{id_part}.m3u8"
                        if new_query:
                            new_url += f"?{new_query}"
                        updated_lines.append(new_url)
                        has_changes = True
                        print(f"Updated {path}/{id_part}: domain={current_domain} -> {new_domain}, params={current_params} -> {new_params}")
                        i += 2
                        continue
            updated_lines.append(url)  # 未匹配或无变化，保留原URL
            i += 2
        else:
            i += 1
    else:
        i += 1

# 如果有变化，写回文件
if has_changes:
    try:
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(updated_lines) + '\n')
        print("Updated domain and parameters successfully.")
    except Exception as e:
        print(f"Error writing to target file {target_file}: {e}")
        exit(1)
else:
    print("No domain or parameter changes detected, skipping update.")
