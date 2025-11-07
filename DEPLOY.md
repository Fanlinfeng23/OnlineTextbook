# Render 部署指南

本文档说明如何将在线教材检索系统部署到 [Render](https://render.com/)。

## 1. 准备工作

1. 注册或登录 Render 账号。
2. Fork / 推送本项目到自己的 Git 仓库（GitHub / GitLab）。
3. 确保下面文件已在仓库中：
   - `app.py`
   - `online_textbook/` 包（Flask 应用）
   - `requirements.txt`
   - `Procfile`
   - `render.yaml`
   - `bm25_index.pkl`
   - `htmls/` 目录（包含静态 HTML 文档）
   - `data/stopwords.txt`（停用词表，需自行准备）

> **注意**：`bm25_index.pkl` 与 `htmls/` 文件夹可能较大，提交前请确认仓库大小在 Render 免费额度内（<1GB）。

## 2. 准备停用词文件

Render 部署时会读取 `data/stopwords.txt`。如果原始路径不同，请将文件复制到仓库中的 `data/stopwords.txt`，或在 Render 控制台中设置 `STOPWORDS_PATH` 环境变量指向自定义路径。

## 3. 启用 Blueprint 部署

1. 打开 Render 控制台，选择 “New + → Blueprint”。
2. 连接包含此项目的 Git 仓库。
3. Render 会自动识别根目录下的 `render.yaml` 并展示部署计划。
4. 点击 “Apply” 创建服务。

Blueprint 模式会自动读取 `render.yaml` 中的配置：

```yaml
services:
  - type: web
    name: online-textbook
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app
    envVars:
      - key: HTMLS_DIR
        value: htmls
      - key: STOPWORDS_PATH
        value: data/stopwords.txt
      - key: INDEX_PATH
        value: bm25_index.pkl
```

如需修改端口或并发，请手动调整对应的环境变量或命令。

## 4. 手动创建 Web Service（可选）

如果不使用 Blueprint，可手动创建：

1. 点击 “New + → Web Service”。
2. 选择 Git 仓库及部署分支。
3. 语言选择 `Python`。
4. Build Command：`pip install -r requirements.txt`
5. Start Command：`gunicorn app:app`
6. 在 “Environment” 中添加变量：
   - `HTMLS_DIR=htmls`
   - `STOPWORDS_PATH=data/stopwords.txt`
   - `INDEX_PATH=bm25_index.pkl`

部署完成后，Render 会分配一个公共 URL，访问即可看到检索页面。

## 5. 常见问题

### 5.1 找不到停用词文件或索引文件

- 确认 `data/stopwords.txt`、`bm25_index.pkl` 已随代码上传。
- 如路径不同，请修改 `render.yaml` 或 Render 控制台中的环境变量。
- 日志中出现 “停用词文件不存在/索引文件不存在” 时，可通过 Render Shell 或远程构建索引脚本。

### 5.2 索引构建

- 如需更新索引，可在本地运行：

  ```bash
  python -m search_engine
  ```

  或在 Render Shell 中执行同样命令，确保新生成的 `bm25_index.pkl` 已提交到仓库。

## 6. 本地运行

```bash
python -m venv .venv
source .venv/bin/activate  # Windows 使用 .venv\Scripts\activate
pip install -r requirements.txt
export FLASK_DEBUG=1
python app.py
```

默认监听 `http://127.0.0.1:5000`。

---

部署完成后，访问 Render 分配的域名即可进行在线检索。若需自定义域名，可在 Render 控制台绑定自己的域名并配置 HTTPS。

