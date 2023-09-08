#!/usr/bin/env python
# -*- coding:utf-8 _*-
"""
"""
import pandas as pd
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from langchain.schema import Document
from langchain.vectorstores import FAISS
from tqdm import tqdm

"""
1.抽取关键词，依据关键词检索文档；
2.将相关文档存储为向量形式；
3.依据QUERY检索固定的向量
4.将固定向量相邻的文本类型串起来，同时作为prompt的一部分；
5.chatglm2问答
"""


# 中文Wikipedia数据导入示例：
embedding_model_name = r'D:\代码\pretrained_model\bert-base-chinese'
embeddings = HuggingFaceEmbeddings(model_name=embedding_model_name,
                                   model_kwargs={'device': "gpu"})

query_result = embeddings.embed_query("你好")

docs = []
rows = []
import glob
lol_df = glob.glob("2010/2010/*.txt")
# print(lol_df)
idx = 0
for row in lol_df:
    # print(row)
    for row in open(row,"r").read().split("\n"):
        if len(row) < 512:
            rows.append(row)
rows = list(set(rows))
for row in rows:
        metadata = {"source": f'doc_id_{idx}'}
        idx += 1
        # print(row)

        # text = row["left"]
        if isinstance(row, str):
            docs.append(Document(page_content=row, metadata=metadata))

vector_store = FAISS.from_documents(docs, embeddings)
# 保存向量文件，支撑二次复用，向量计算的过程实在是太久了。下回直接读取向量文件就不需要二次
vector_store.save_local('cache/lol/')
vector_store.similarity_search(
    "利用输入输出进行训练数据集相似度判断，如果输入和输出和训练数据集差距较大划分为异常输入输出。")