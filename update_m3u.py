import requests
import os
import re

# 来源URL
source_url = 'https://raw.githubusercontent.com/mursor1985/LIVE/refs/heads/main/iptv.m3u'

# 目标文件路径（在repo中）
target_file = 'bptv.m3u'

# 下载来源M3U内容
try:
    source_response = requests.get(source_url)
    source_response.raise_for_status()
    source_content = source_response.text
except Exception as e:
    print(f"Error fetching source: {e}")
    exit(0)  # 如果来源失败，不更新

# 解析来源，提取ID -> (域名, migutoken)
source_tokens = {}
lines = source_content.splitlines()
i = 0
while i < len(lines):
    if lines[i].startswith('#EXTINF:'):
        if i + 1 < len(lines) and '/migu/' in lines[i + 1]:
            url = lines[i + 1]
            if '?migutoken=' in url:
                # 提取域名和ID
                match = re.match(r'https?://([^/]+)/migu/(\d+)\.m3u8\?migutoken=([0-9a-f]+)', url)
                if match:
                    domain = match.group(1)
                    id_part = match.group(2)
                    token = match.group(3)
                    source_tokens[id_part] = (domain, token)
                    print(f"Found token for ID {id_part}: domain={domain}, migutoken={token}")
        i += 2
    else:
        i += 1

if not source_tokens:
    print("No tokens found in source.")
    exit(0)

# 读取目标文件
if not os.path.exists(target_file):
    print(f"Target file {target_file} not found.")
    exit(0)

with open(target_file, 'r', encoding='utf-8') as f:
    target_content = f.read()

# 替换目标文件的域名和migutoken
updated_lines = []
lines = target_content.splitlines()
i = 0
has_changes = False
while i < len(lines):
    line = lines[i]
    updated_lines.append(line)
    if line.startswith('#EXTINF:'):
        if i + 1 < len(lines) and '/migu/' in lines[i + 1]:
            url = lines[i + 1]
            match = re.match(r'https?://([^/]+)/migu/(\d+)\.m3u8(\?migutoken=[0-9a-f]+)?', url)
            if match:
                current_domain = match.group(1)
                id_part = match.group(2)
                current_token = match.group(3).split('=')[1] if match.group(3) else ''
                if id_part in source_tokens:
                    new_domain, new_token = source_tokens[id_part]
                    if current_domain != new_domain or current_token != new_token:
                        new_url = f"https://{new_domain}/migu/{id_part}.m3u8?migutoken={new_token}"
                        updated_lines.append(new_url)
                        has_changes = True
                        print(f"Updated ID {id_part}: domain={current_domain} -> {new_domain}, migutoken={current_token} -> {new_token}")
                    else:
                        updated_lines.append(url)  # 无变化，保留原URL
                    i += 2
                    continue
            updated_lines.append(url)  # 未匹配，保留原URL
            i += 2
        else:
            i += 1
    else:
        i += 1

# 如果有变化，写回文件
if has_changes:
    with open(target_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(updated_lines) + '\n')
    print("Updated domain and migutoken successfully.")
else:
    print("No domain or token changes detected, skipping update.")
