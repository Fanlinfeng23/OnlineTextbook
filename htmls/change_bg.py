import os

# 配置：详情页HTML所在目录（根据你的实际路径修改）
HTMLS_DIR = "F:\OnlineTextbook\htmls"

# 旧路径（需要替换的内容，根据你的HTML实际写法调整）
# 常见旧路径可能是：'img/background.jpg' 或 '../img/background.jpg' 等
old_path_patterns = [
    "url('img/background.jpg')",
    'url("img/background.jpg")',
    "url('background.jpg')",  # 若直接放在HTML同目录
    'url("background.jpg")'
]

# 新路径（绝对路径，指向static下的图片）
new_path = "url('/static/img/background.jpg')"

# 遍历所有HTML文件
for filename in os.listdir(HTMLS_DIR):
    if filename.endswith(".html"):
        file_path = os.path.join(HTMLS_DIR, filename)
        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 替换所有可能的旧路径
            modified = False
            for old in old_path_patterns:
                if old in content:
                    content = content.replace(old, new_path)
                    modified = True

            # 若内容有修改，写回文件
            if modified:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"已修改：{filename}")
            else:
                print(f"无需修改：{filename}（未找到旧路径）")
        except Exception as e:
            print(f"处理{filename}失败：{str(e)}")

print("批量替换完成！")