import os


def parse_txt_to_target(input_txt_path):
    """解析txt生成HTML，优化缩进格式"""
    if not os.path.exists("htmls"):
        os.makedirs("htmls")

    output_count = 0
    current_str = ""  # 缓存当前HTML内容
    conti = 0  # 记录section数量，控制标签闭合

    with open(input_txt_path, 'r', encoding='utf-8') as f:
        lines = [line.rstrip('\n') for line in f.readlines()]  # 去除每行末尾换行

    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue  # 跳过空行

        # 处理#标记：生成新HTML
        if '#' in line:
            # 闭合上一个HTML（如果存在）
            if output_count > 0:
                # 闭合最后一个section的标签
                current_str += '''    </p>
        </div>
    </div>'''
                # 拼接推荐模块和HTML尾部（严格缩进）
                current_str += '''
    <div class="section related-words">
        <h3>相关汉字</h3>
        <div class="related-container">
            {% for item in related_items %}
            <div class="related-item">
                <a href="{{ item.url }}">{{ item.text }}</a>
                <p>{{ item.desc }}</p>
            </div>
            {% endfor %}
        </div>
    </div>
</div>
</body>
</html>'''
                # 写入文件
                with open(f"htmls\\{output_count}.html", 'w', encoding='utf-8') as out_f:
                    out_f.write(current_str)

            # 初始化新区块（当前#对应的HTML）
            output_count += 1
            title = line.strip().lstrip('#').strip()  # 提取标题（去除#和空格）
            # HTML头部（严格缩进：外层4空格，内层再4空格，以此类推）
            current_str = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: "Microsoft YaHei", sans-serif;
            line-height: 1.6;
            background: url('img/background.jpg') no-repeat fixed center;
            background-size: cover;
            color: #333;
        }}
        .top-bar {{
            position: fixed;
            top: 0;
            width: 100%;
            padding: 12px 20px;
            background-color: rgba(255, 237, 216, 0.8);
            border-bottom: 2px solid #ffedd8;
            z-index: 9000;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
        }}
        .main-container {{
            padding: 120px 20px 30px;
            max-width: 1200px;
            margin: 0 auto;
        }}
        .character-display {{
            position: relative;
            text-align: center;
            padding: 60px 0;
            background: #fff7e8;
            border-radius: 12px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            margin-bottom: 12px;
        }}
        .character {{
            font-size: 200px;
            color: #504b47;
            cursor: pointer;
            display: inline-block;
            transition: all 0.3s;
        }}
        .character:hover {{
            transform: translateY(-5px);
            text-shadow: 0 0 8px rgba(0, 0, 0, 0.3);
        }}
        .related-container {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }}
        .related-item {{
            background: #fff7e8;
            padding: 15px;
            border-radius: 6px;
            text-align: center;
            transition: transform 0.3s;
        }}
        .related-item:hover {{
            transform: translateY(-3px);
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }}
        a, a:visited {{
            color: #c8a172;
            text-decoration: none;
            font-weight: bold;
        }}
        @media (max-width: 768px) {{
            .character {{
                font-size: 150px;
            }}
        }}
    </style>
</head>
<body>
    <div class="top-bar">
        <span>求是学术</span>
        <span>二年级</span>
    </div>
    <div class="main-container">
        <section class="character-display">
            <div class="character">{title}</div>
        </section>'''.format(title=title)  # 用format填充标题，避免拼接错误
            conti = 0  # 重置section计数器
            continue

        # 处理【】：生成带缩进的section
        if '【' in line and '】' in line:
            # 闭合上一个section（如果存在）
            if conti > 0:
                current_str += '''    </p>
                </div>
            </div>'''
            conti += 1

            # 拆分内容
            before_left = line.split('【')[0].strip()
            middle = line.split('【')[1].split('】')[0].strip()  # 标题
            after_right = line.split('】')[1].strip()

            # 【前的内容（通常为空，若有则添加）
            if before_left:
                current_str += f"{before_left.replace('\n', '<br>')}<br>"

            # 新section开始（先添加外层div和标题）
            current_str += f'''
            <div class="section">
                <h3>{middle}</h3>'''

            # 当标题为'形'时，插入图片（放在标题下方，内容上方，缩进对齐）
            if middle == '形':
                current_str += f'''
                <div style="text-align: center; margin: 15px 0;">
                    <img src="{output_count}.png" style="max-width: 60%; height: auto; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                </div>'''

            # 继续添加内容容器（reading和p标签）
            current_str += f'''
                <div class="reading">
                    <p>'''

            # 【】后的内容（添加到p标签内）
            if after_right:
                current_str += f"{after_right.replace('\n', '<br>')}<br>"

            continue

        # 普通内容：保持在p标签内，缩进正确
        current_str += f"{line.replace('\n', '<br>')}<br>"

    # 处理最后一个HTML的闭合
    if output_count > 0:
        # 闭合最后一个section
        current_str += '''    </p>
        </div>
    </div>'''
        # 拼接推荐模块和尾部
        current_str += '''
    <div class="section related-words">
        <h3>相关汉字</h3>
        <div class="related-container">
            {% for item in related_items %}
            <div class="related-item">
                <a href="{{ item.url }}">{{ item.text }}</a>
                <p>{{ item.desc }}</p>
            </div>
            {% endfor %}
        </div>
    </div>
</div>
</body>
</html>'''
        # 写入最后一个文件
        with open(f"htmls\\{output_count}.html", 'w', encoding='utf-8') as out_f:
            out_f.write(current_str)

    print(f"处理完成，共生成{output_count}个HTML文件（htmls文件夹），缩进已规范")


if __name__ == "__main__":
    parse_txt_to_target("F:\\1.txt")