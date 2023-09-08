# -*- coding: utf-8 -*-
# @Time    : 2023/8/2 15:31
# @Author  : huangkai
# @File    : test.py

# 官方示例代码，用的OpenAI的ada的文本Embedding模型
# 1） Embeding model
# from langchain.embeddings import OpenAIEmbeddings
from langchain.embeddings.huggingface import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(model_name=r"D:\代码\pretrained_model\bert-base-chinese",
                                   model_kwargs={'device': "cpu"},
                                   encode_kwargs={'normalize_embeddings': True})
query_result = embeddings.embed_query("你好")

# 2)文本分割， 这里仅为了方便快速看流程，实际应用的会复杂一些
texts = """天道酬勤”并不是鼓励人们不劳而获，而是提醒人们要遵循自然规律，通过不断的努力和付出来追求自己的目标。\n这种努力不仅仅是指身体上的劳动，
也包括精神上的努力和思考，以及学习和适应变化的能力。\n只要一个人具备这些能力，他就有可能会获得成功。"""
from langchain.text_splitter import CharacterTextSplitter
from langchain.docstore.document import Document


class TextSpliter(CharacterTextSplitter):
    def __init__(self, separator: str = "\n\n", **kwargs):
        super().__init__(separator, **kwargs)

    def split_text(self, text: str):
        texts = text.split("\n")
        texts = [Document(page_content=text, metadata={"from": "知识库.txt"}) for text in texts]
        return texts


text_splitter = TextSpliter()
texts = text_splitter.split_text(texts)

# 3) 直接本地存储
vs_path = "./demo-vs"
from langchain.vectorstores import FAISS

vector_store = FAISS.from_documents(texts, embeddings)
vector_store.save_local(vs_path)

vector_store = FAISS.load_local(vs_path, embeddings)
related_docs_with_score = vector_store.similarity_search_with_score("天道酬勤,追求自己的目标", k=2)
for unit in related_docs_with_score:
    print(unit[0].metadata["from"])
