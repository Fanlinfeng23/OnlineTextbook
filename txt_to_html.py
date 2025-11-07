def parse_txt_to_target(input_txt_path):
    """
    解析输入txt，内容先缓存到字符串中，最后一次性写入文件
    :param input_txt_path: 输入txt文件路径
    :param predefined_content: 每次遇到#时先写入的"之前准备好的内容"
    """
    output_count = 0  # 输出文件计数器（区分多个#生成的txt）
    current_str = ""  # 当前区块的内容缓存（字符串形式）
    in_bracket = False  # 是否处于【和】之间
    bracket_str = ""  # 缓存【和】之间的内容（字符串）

    with open(input_txt_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()  # 按行读取，保留原始换行

    conti=0
    for line in lines:
        # 1. 处理#标记：结束上一个区块，写入文件；初始化新区块
        if '#' in line:
            # 如果不是第一个#，先将上一个区块的缓存写入文件
            if output_count > 0:
                current_str+='''</p>
            </div>
        </div>

        <div class="section related-words">
            <h3>相关汉字</h3>
            <div class="related-container">
                <!-- 循环渲染4个相关项，假设Flask传入的变量是related_items（列表） -->
                {% for item in related_items %}
                <div class="related-item">
                    <a href="{{ item.url }}">{{ item.text }}</a>
                    <!-- 可选：如果需要描述文字，也可以动态传入 -->
                    <p>{{ item.desc }}</p>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>
</body>

</html>'''
                with open(f"htmls\\{output_count}.html", 'w', encoding='utf-8') as out_f:
                    out_f.write(current_str)  # 一次性写入缓存的字符串

            # 递增计数器，初始化新区块的缓存
            output_count += 1
            # abc + #所在行 + bbb
            title=line.strip()
            current_str += '''<!DOCTYPE html>
<html lang="zh-CN">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>'''
            current_str += title  # 加入#所在行（去原始换行，避免重复）
            current_str += '''</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            font-family: "Microsoft YaHei", sans-serif;
            line-height: 1.6;
            background: url('img/background.jpg') no-repeat fixed center;
            background-size: cover;
            color: #333;
        }

        /* 顶部栏最上层设置 */
        .top-bar {
            position: fixed;
            top: 0;
            width: 100%;
            padding: 12px 20px;
            background-color: rgba(255, 237, 216, 0.8);
            border-bottom: 2px solid #ffedd8;
            z-index: 9000;
            /* 强制最上层 */
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
        }

        /* 主容器留出顶部空间 */
        .main-container {
            padding: 120px 20px 30px;
            /* 顶部留白 */
            max-width: 1200px;
            margin: 0 auto;
        }

        /* 汉字主展示区 */
        .character-display {
            position: relative;
            text-align: center;
            padding: 60px 0;
            background: #fff7e8;
            /* 米白色背景 */
            border-radius: 12px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            margin-bottom: 12px;
        }

        .character {
            font-size: 200px;
            color: #504b47;
            cursor: pointer;
            display: inline-block;
            transition: all 0.3s;
        }

        .character:hover {
            transform: translateY(-5px);
            text-shadow: 0 0 8px rgba(0, 0, 0, 0.3);
        }


        /* 推荐模块优化 */
        .related-container {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }

        .related-item {
            background: #fff7e8;
            padding: 15px;
            border-radius: 6px;
            text-align: center;
            transition: transform 0.3s;
        }

        .related-item:hover {
            transform: translateY(-3px);
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }

        a,
        a:visited {
            color: #c8a172;
            text-decoration: none;
            font-weight: bold;
        }


        /* 响应式优化 */
        @media (max-width: 768px) {
            .character {
                font-size: 200px;
            }
        }
    </style>
</head>

<body>
    <div class="top-bar">
        <span>求是学术</span>
        <span>二年级</span>
    </div>

    <!-- 主内容区域 -->
    <div class="main-container">
        <section class="character-display">
            <!-- 中心汉字 -->
            <div class="character">'''
            current_str+=title
            current_str+='''</div>

        </section>'''
            continue

        # 2. 处理【】（同一行内）
        if '【' in line and '】' in line:
            if conti>0:
                current_str+='''</p>
            </div>
        </div>'''
            conti+=1;
            # 拆分【前、【】中间、】后三部分
            # 示例："前缀【标题】后缀" → 拆分为"前缀"、"标题"、"后缀"
            before_left = line.split('【')[0]
            middle = line.split('【')[1].split('】')[0]
            after_right = line.split('】')[1]

            # 处理【前的内容（回车替换为<br>）
            if before_left.strip():
                current_str += before_left.replace('\n', '<br>') + '\n'

            # 加入ccc + 【】中间的内容
            current_str += '''        <div class="section">
            <h3>'''
            current_str+=middle
            # 加入ddd
            current_str += '''</h3>
            <div class="reading">
                <p>'''
            continue

        # 4. 普通内容：回车替换为<br>，加入当前缓存
        if not in_bracket:
            current_str += line.replace('\n', '<br>') + '\n'

    # 处理最后一个区块（文件结束时）
    if output_count > 0:
        with open(f"output_{output_count}.txt", 'w', encoding='utf-8') as out_f:
            out_f.write(current_str)  # 一次性写入最后一个区块的缓存

    print(f"处理完成，共生成{output_count}个输出文件（output_1.txt, ..., output_{output_count}.txt）")


# 使用示例
if __name__ == "__main__":
    input_txt = "input.txt"  # 替换为你的输入txt路径

    parse_txt_to_target(input_txt)