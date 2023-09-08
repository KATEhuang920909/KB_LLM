#!/usr/bin/env python
# -*- coding:utf-8 _*-
"""
"""
import pandas as pd
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from llm_predict import LLM_PREDICTOR
from data_preprocess import DataPreprocess
from config import maxlen, topk, PROMPT_TEMPLATE, threshold, dir_path, embedding_path, feature_extract_prompt, \
    excel_prefix_prompt, text_prefix_prompt, llm_path
from ir.search_file_name import Search
from ir.search_content import Search as SearchContent
from ir.config import Config
from ir.es_update import Es_Update

"""
1.抽取关键词，依据关键词检索文档；
2.将相关文档存储为向量形式；
3.依据QUERY检索固定的向量
4.将固定向量相邻的文本类型串起来，同时作为prompt的一部分；
5.chatglm2问答
"""


# 中文Wikipedia数据导入示例：
class LLM_KB():
    def __init__(self, embedding_path):#, llm_path):
        self.embeddings = HuggingFaceEmbeddings(model_name=embedding_path,
                                                model_kwargs={'device': "cpu"},
                                                encode_kwargs={'normalize_embeddings': True})
        # self.llm_predictor = LLM_PREDICTOR(llm_path)
        # print(self.embeddings.embed_query("你试试额"))
        self.es_update = Es_Update()
        index_file_name_config = Config()
        index_file_name_config.index_name = "filename"
        self.search_name = Search(index_file_name_config)

        self.index_file_content_config = Config()

        self.dp = DataPreprocess(maxlen=maxlen)

    def vector_store(self, files, vs_path, ):
        vector_store = FAISS.from_documents(files, self.embeddings)
        vector_store.save_local(vs_path)

    def vector_retrieval(self, query, vs_path):
        vector_store = FAISS.load_local(vs_path, self.embeddings)
        related_docs_with_score = vector_store.similarity_search_with_score(query, k=topk)

        return related_docs_with_score

    def get_history_text(self, doc_chunk, doc_bag):
        final_text = doc_chunk[0]["page_content"]
        metadata = doc_chunk[0].metadata
        type = metadata.split("@type")[-1]
        idx = int(metadata.split("@id")[1].split("@type")[0])
        while doc_bag[idx - 1][0].metadata.split("@type")[-1] == type:
            pre_txt = doc_bag[idx - 1][0]["page_content"]
            final_text = pre_txt + final_text
            idx -= 1
        idx = int(metadata.split("@id")[1].split("@type")[0])
        while doc_bag[idx + 1][0].metadata.split("@type")[-1] == type:
            post_txt = doc_bag[idx - 1][0]["page_content"]
            final_text += post_txt
            idx += 1
        return final_text, type

    def generate_prompt(self, related_doc, TYPE, query: str, prompt_template: str = PROMPT_TEMPLATE,
                        preprompt="") -> str:
        if TYPE == "excel":
            preprompt = "根据以下表格信息："
        elif TYPE == "text":
            preprompt = "根据以下文本信息："

        prompt = preprompt + prompt_template.replace("{question}", query).replace("{context}", related_doc)
        return prompt

    def llm_feature_extract(self, query, prompt_template=feature_extract_prompt):
        response, history = self.llm_predictor.predict(prompt_template + query)
        response = response.split("\n")
        name = response[0].split("：")[-1]
        time = response[1].split("：")[-1]
        return name, time

    def llm_chat(self, prompt):
        response, history = self.llm_predictor.predict(prompt)

        return response

    def es_result(self, key_word, query):
        final_result = [query]
        query1 = "".join(key_word)

        for unit in key_word:
            query = query.replace(unit, "")
        # 找到对应的文件
        if query1:
            result = self.search_name.searchAnswer(query1)[0][0]
            print(self.es_update.file_name_idx[result], result)
            # 对应的文件写入es
            # result = "锦江酒店2019年年度报告"
            questions = self.es_update.update_content(self.es_update.file_name_idx[result], result)

            self.index_file_content_config.index_name = result
            # query检索
            search_content = SearchContent(self.index_file_content_config)

            result2 = search_content.searchAnswer(query)
            flag = 0
            for unit in result2:
                if unit[2] in ["excel", "text"]:

                    chunk_info = self.dp.document_chunk_idx(questions, unit)
                    if unit[2] == "excel":
                        prompt = excel_prefix_prompt + \
                                 PROMPT_TEMPLATE.replace("{question}", query).replace("{context}", chunk_info)
                    elif unit[2] == "text":
                        prompt = text_prefix_prompt + \
                                 PROMPT_TEMPLATE.replace("{question}", query).replace("{context}", chunk_info)
                    flag += 1
                    print(prompt + "\n")
                    response = self.llm_chat(prompt)
                    final_result.append(response)
                if flag == 2:
                    break
        else:
            prompt = query
            final_result.append(prompt)
        return final_result


if __name__ == '__main__':
    import json

    es_update = Es_Update()
    index_file_name_config = Config()
    index_file_name_config.index_name = "filename"
    search_name = Search(index_file_name_config)

    #
    index_file_content_config = Config()
    #
    dp = DataPreprocess(maxlen=maxlen)
    # # 找出关键词：
    # key_word = []
    # llm_chain = LLM_KB(embedding_path=embedding_path)#, llm_path=llm_path)

    # # final_result = [query]
    # # query1 = "".join(key_word)
    # #
    # # for unit in key_word:
    # #     query = query.replace(unit, "")
    # # 找到对应的文件
    final_result=[]
    while True:
        query = input("please input")
        result = search_name.searchAnswer(query)[0][0]
        print(result)
    #     # 对应的文件写入es
    #     # result = "锦江酒店2019年年度报告"
        questions = es_update.update_content(es_update.file_name_idx[result], result)
        index_file_content_config.index_name = result
    #     # query检索
        search_content = SearchContent(index_file_content_config)
        query1 = "电子邮箱是什么"
        result2 = search_content.searchAnswer(query1)
        print(result2,index_file_content_config.index_name)
    #     flag = 0
    #     for unit in result2:
    #         if unit[2] in ["excel", "text"]:
    #
    #             chunk_info = dp.document_chunk_idx(questions, unit)
    #             if unit[2] == "excel":
    #                 prompt = excel_prefix_prompt + \
    #                          PROMPT_TEMPLATE.replace("{question}", query1).replace("{context}", chunk_info)
    #             elif unit[2] == "text":
    #                 prompt = text_prefix_prompt + \
    #                          PROMPT_TEMPLATE.replace("{question}", query1).replace("{context}", chunk_info)
    #             flag += 1
    #             print(prompt + "\n")
    #             # response = self.llm_chat(prompt)
    #             final_result.append(prompt)
    #         if flag == 2:
    #             break
    # print(final_result)



    # else:
    #     prompt = query1
    #     final_result.append(prompt)

    #
    # print(llm_chain.es_result("的法定代表人是谁？"))
    # with open("test_questions.json", encoding="utf8") as f:
    #     data = f.readlines()
    #     data = [json.loads(k.strip()) for k in data]
    # submit = open(r"result/submit_0809.json","w",encoding="utf8")
    # for unit in data:
    #     result = llm_chain.llm_feature_extract(unit["question"])
    #     unit["key_word"] = result
    #     submit.write(json.dumps(unit, ensure_ascii=False) + "\n")
    #
    #
    #     while True:
    #         query = input("please input")
    #         result = search_name.searchAnswer(query)
    #         print(result)
    #         # for data in result:
    #         #     print("question:%s  question_id:%s  " % (data[0], data[1]))