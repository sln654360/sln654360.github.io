import requests
import os

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

# 解析来源，提取ID -> migutoken
source_tokens = {}
lines = source_content.splitlines()
i = 0
while i < len(lines):
    if lines[i].startswith('#EXTINF:'):
        if i + 1 < len(lines) and 'mursor.ottiptv.cc/migu/' in lines[i + 1]:
            url = lines[i + 1]
            if '?migutoken=' in url:
                parts = url.split('/migu/')
                if len(parts) > 1:
                    id_part = parts[1].split('.m3u8')[0]
                    token = url.split('?migutoken=')[1]
                    source_tokens[id_part] = token
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

# 替换目标文件的migutoken
updated_lines = []
lines = target_content.splitlines()
i = 0
has_changes = False
while i < len(lines):
    line = lines[i]
    updated_lines.append(line)
    if line.startswith('#EXTINF:'):
        if i + 1 < len(lines) and 'mursor.ottiptv.cc/migu/' in lines[i + 1]:
            url = lines[i + 1]
            parts = url.split('/migu/')
            if len(parts) > 1:
                id_part = parts[1].split('.m3u8')[0]
                if id_part in source_tokens:
                    current_token = url.split('?migutoken=')[1] if '?migutoken=' in url else ''
                    new_token = source_tokens[id_part]
                    if current_token != new_token:
                        base_url = url.split('?migutoken=')[0]
                        updated_lines[-1] = line  # 保留#EXTINF行
                        updated_lines.append(f"{base_url}?migutoken={new_token}")
                        has_changes = True
                    else:
                        updated_lines.append(url)  # 保留原URL
                    i += 2  # 跳过URL行
                    continue
            updated_lines.append(url)  # 未匹配或无token，保留原URL
            i += 2
        else:
            i += 1
    else:
        i += 1

# 如果有变化，写回文件
if has_changes:
    with open(target_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(updated_lines) + '\n')
    print("Updated migutoken successfully.")
else:
    print("No token changes detected, skipping update.")
