"""
使用大模型重构 Markdown 标题层级脚本

将扁平的一级标题（#）根据目录结构重构为多级标题（#、##、###）
"""

import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


def call_modelScope_api(content: str) -> str:
    """直接调用 ModelScope API"""
    url = "https://api-inference.modelscope.cn/v1/chat/completions"

    prompt = """你是一个专业的 Markdown 排版专家。用户提供的旅游攻略中，由于OCR提取原因，所有标题全是扁平的一级标题（#）。请仔细阅读开头的『目录·CATALOG』，然后根据目录的逻辑关系，将正文中的标题重新调整为多级结构（#、##、###）。

绝对红线：
1. 只能修改标题前面的 # 数量（# -> ##, ###）
2. 严禁增删改任何正文字符
3. 严禁修改图片链接 [](...)
4. 严禁修改任何标点符号

请直接输出重构后的 Markdown 内容，不要有任何解释。"""

    headers = {
        "Authorization": f"Bearer {os.getenv('MODELSCOPE_API_KEY')}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": os.getenv("MODEL_NAME", "moonshotai/Kimi-K2.5"),
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": content}
        ],
        "temperature": 0.3,
        "max_tokens": 8192
    }

    response = requests.post(url, headers=headers, json=payload, timeout=180)
    response.encoding = "utf-8"

    if response.status_code != 200:
        raise Exception(f"API调用失败: {response.status_code} - {response.text}")

    result = response.json()
    return result["choices"][0]["message"]["content"]


def load_markdown(file_path: str) -> str:
    """加载 Markdown 文件内容"""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")
    return path.read_text(encoding="utf-8")


def save_markdown(content: str, output_path: str) -> None:
    """保存重构后的 Markdown 文件"""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"已保存至: {output_path}")


def main():
    # 路径配置
    input_file = "data_markdown/哈尔滨旅游攻略.md"
    output_file = "data_markdown/guide_structured.md"

    print("=" * 60)
    print("Markdown 标题层级重构工具")
    print("=" * 60)

    # 1. 加载 Markdown
    print(f"\n[1/3] 读取文件: {input_file}")
    content = load_markdown(input_file)
    print(f"文件长度: {len(content)} 字符")

    # 2. 调用大模型重构
    print("\n[2/3] 调用大模型重构标题层级...")
    restructured_content = call_modelScope_api(content)
    print(f"重构完成，返回内容长度: {len(restructured_content)} 字符")

    # 3. 保存结果
    print(f"\n[3/3] 保存文件: {output_file}")
    save_markdown(restructured_content, output_file)

    print("\n" + "=" * 60)
    print("完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
