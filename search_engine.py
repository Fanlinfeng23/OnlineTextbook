import os
import math
import pickle
from collections import defaultdict
from pathlib import Path

import jieba
from bs4 import BeautifulSoup


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_HTMLS_DIR = os.getenv("HTMLS_DIR", str(BASE_DIR / "htmls"))
DEFAULT_STOPWORDS_PATH = os.getenv("STOPWORDS_PATH", str(BASE_DIR / "data" / "stopwords.txt"))
DEFAULT_INDEX_PATH = os.getenv("INDEX_PATH", str(BASE_DIR / "bm25_index.pkl"))

_STOPWORDS_CACHE: dict[str, set[str]] = {}
_INDEX_CACHE: dict[str, dict] = {}


# ---------------------- 工具函数（复用之前的解析和预处理逻辑） ----------------------
def load_stopwords(stopwords_path: str | None = None):
    """加载停用词表，带简单缓存"""
    path = stopwords_path or DEFAULT_STOPWORDS_PATH
    if path in _STOPWORDS_CACHE:
        return _STOPWORDS_CACHE[path]

    try:
        with open(path, "r", encoding="utf-8") as f:
            stopwords = set(f.read().splitlines())
    except FileNotFoundError as exc:
        raise ValueError(f"停用词文件不存在：{path}") from exc

    _STOPWORDS_CACHE[path] = stopwords
    return stopwords


def tokenize(text, stopwords):
    """中文分词并过滤停用词"""
    if not text:
        return []
    words = jieba.cut(text, cut_all=False)  # 精确分词
    return [word for word in words if word.strip() and word not in stopwords]


# ---------------------- 索引构建与保存（复用并完善） ----------------------
def build_bm25_index(
    htmls_dir: str | os.PathLike[str] = DEFAULT_HTMLS_DIR,
    stopwords_path: str | None = None,
    start: int = 1,
    end: int = 107,
    save_path: str | os.PathLike[str] = DEFAULT_INDEX_PATH,
):
    """构建BM25索引并保存为pkl文件"""
    stopwords = load_stopwords(stopwords_path)
    inverted_index = defaultdict(dict)  # {word: {doc_id: 加权词频}}
    doc_lengths = {}  # {doc_id: 原始长度}
    word_df = defaultdict(int)  # {word: 文档频率}
    total_docs = 0  # 有效文档数

    htmls_dir = Path(htmls_dir)

    for doc_id in range(start, end + 1):
        file_path = htmls_dir / f"{doc_id}.html"
        if not file_path.exists():
            print(f"跳过不存在的文件：{file_path}")
            continue

        # 解析HTML提取title和p标签
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f.read(), "lxml")
        except Exception:
            with open(file_path, "r", encoding="gbk", errors="ignore") as f:
                soup = BeautifulSoup(f.read(), "lxml")

        title = soup.title.get_text(strip=True) if soup.title else ""
        p_texts = [p.get_text(strip=True) for p in soup.find_all('p') if p.get_text(strip=True)]
        p_text = " ".join(p_texts)

        # 计算加权词频（title权重20，p权重1）
        title_words = tokenize(title, stopwords)
        p_words = tokenize(p_text, stopwords)

        weighted_tf = defaultdict(int)
        for word in title_words:
            weighted_tf[word] += 20  # title权重
        for word in p_words:
            weighted_tf[word] += 1   # p标签权重

        if not weighted_tf:
            continue  # 无有效词，跳过

        # 更新索引
        doc_lengths[doc_id] = len(title_words) + len(p_words)  # 原始长度（不含权重）
        total_docs += 1
        for word, tf in weighted_tf.items():
            inverted_index[word][doc_id] = tf
            word_df[word] += 1  # 文档频率（去重）

        print(f"已处理文档 {doc_id}/{end}")

    # 计算平均文档长度
    avg_len = sum(doc_lengths.values()) / total_docs if total_docs else 0

    # 保存索引数据（过程性文件）
    index_data = {
        "inverted_index": dict(inverted_index),
        "word_df": dict(word_df),
        "doc_lengths": doc_lengths,
        "total_docs": total_docs,
        "avg_doc_length": avg_len
    }
    save_path = Path(save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)

    with open(save_path, "wb") as f:
        pickle.dump(index_data, f)
    print(f"索引已保存至 {save_path}，共包含 {total_docs} 个文档")
    return index_data


# ---------------------- 检索功能实现 ----------------------
def bm25_score(query_words, doc_id, index_data, k1=1.2, b=0.75):
    """计算单个文档与查询的BM25分数"""
    inverted_index = index_data["inverted_index"]
    word_df = index_data["word_df"]
    doc_lengths = index_data["doc_lengths"]
    total_docs = index_data["total_docs"]
    avg_len = index_data["avg_doc_length"]

    score = 0.0
    doc_len = doc_lengths.get(doc_id, 0)
    if doc_len == 0:
        return 0.0

    for word in query_words:
        # 跳过不在索引中的词
        if word not in inverted_index:
            continue
        # 词在当前文档中的加权词频
        tf = inverted_index[word].get(doc_id, 0)
        # 词的文档频率
        df = word_df[word]
        # 计算IDF（逆文档频率）
        idf = math.log((total_docs - df + 0.5) / (df + 0.5) + 1)
        # 计算BM25中的TF部分
        tf_part = (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * doc_len / avg_len))
        # 累加分数
        score += idf * tf_part
    return score


def retrieve(
    query: str,
    index_path: str | None = None,
    stopwords_path: str | None = None,
    top_n: int = 10,
):
    """检索函数：返回匹配的HTML编号（文档ID）及分数"""
    index_path = index_path or DEFAULT_INDEX_PATH
    stopwords = load_stopwords(stopwords_path)

    index_data = _INDEX_CACHE.get(index_path)
    if not index_data:
        try:
            with open(index_path, "rb") as f:
                index_data = pickle.load(f)
        except FileNotFoundError as exc:
            raise ValueError(f"索引文件不存在：{index_path}") from exc
        _INDEX_CACHE[index_path] = index_data

    # 处理查询：分词、过滤停用词
    query_words = tokenize(query, stopwords)
    if not query_words:
        return []  # 无有效查询词

    # 获取所有可能相关的文档（包含任一查询词的文档）
    candidate_docs = set()
    for word in query_words:
        if word in index_data["inverted_index"]:
            candidate_docs.update(index_data["inverted_index"][word].keys())
    if not candidate_docs:
        return []  # 无匹配文档

    # 计算每个候选文档的BM25分数
    doc_scores = []
    for doc_id in candidate_docs:
        score = bm25_score(query_words, doc_id, index_data)
        if score > 0:
            doc_scores.append((doc_id, score))

    # 按分数降序排序，返回前N个
    doc_scores.sort(key=lambda x: x[1], reverse=True)
    return doc_scores[:top_n]


# ---------------------- 主函数：构建索引并演示检索 ----------------------
if __name__ == "__main__":
    htmls_dir = DEFAULT_HTMLS_DIR
    stopwords_path = DEFAULT_STOPWORDS_PATH
    index_path = DEFAULT_INDEX_PATH

    if not Path(index_path).exists():
        build_bm25_index(htmls_dir=htmls_dir, stopwords_path=stopwords_path, save_path=index_path)

    while True:
        query = input("\n请输入检索词（输入q退出）：")
        if query.lower() == "q":
            break
        results = retrieve(query, index_path=index_path, stopwords_path=stopwords_path, top_n=5)
        if not results:
            print("未找到匹配的文档")
        else:
            print("检索结果（前5名）：")
            for i, (doc_id, score) in enumerate(results, 1):
                print(f"{i}. HTML编号：{doc_id}，BM25分数：{score:.4f}")