# -*- coding: utf-8 -*-
# @Time    : 2022/3/30 20:43
# @Author  : huangkai
# @File    : search_content.py


import sys

sys.path.append('../')
sys.path.append('../utils')

from nlp4es8.ir.es_config import Config


# from utils.logger_config import base_logger
# from utils.args import FLAGS
# from ir.index_hnsw import Index


class Search(object):
    def __init__(self, config, index_name):
        # base_logger.info("Searching ...")
        self.config = config
        self.es = self.config.es

        self.index_name = index_name

    def searchAnswer(self, question, ):
        body = {
            "query": {
                "multi_match": {
                    "query": question,
                    "fields": ["document"],  # 在question字段中匹配查询
                    "type": "most_fields",
                }
            }
        }

        # es相关配置

        res = self.es.search(index=self.index_name, body=body, request_timeout=30)

        topn = res['hits']['hits']

        result = []
        for data in topn:
            result.append(
                (
                    data['_source']['index'],
                    data['_source']['document']
                )
            )
        return result

        # base_logger.info("ReadTimeOutError may not be covered!")


if __name__ == '__main__':
    import pandas as pd
    import json

    index_file_content_config = Config()
    index_file_content_config.index_name = "kbqa"
    search_name = Search(index_file_content_config, "kbqa")
    # while True:
    #     query = input("please input")
    #     result = search_name.searchAnswer(query)
    #     print(result[0])
    #     for data in result:
    #         print("question:%s  question_id:%s  " % (data[0], data[1]))
    predict_data = open("../../data/test.json", encoding="utf8").readlines()
    # predict_data = open("../../data/提交示例.json", encoding="utf8").readlines()
    # print(predict_data[2])
    # exit()
    submission = open("../../result/es_baseline.json", "w",encoding="utf8")
    predict_data = eval("".join([k.strip() for k in predict_data]))
    print(predict_data[0])
    # exit()
    # predict_data = [json.load(k) for k in predict_data]#[:100]
    final_result=[]
    from tqdm import tqdm
    for unit in tqdm(predict_data):
        query = unit["question"]
        result = search_name.searchAnswer(query)
        temp_final_result = result[0][1]
        unit["attribute"] = temp_final_result
        final_result.append(unit)
    submission.write(json.dumps(final_result,ensure_ascii=False))
    print(predict_data[0])
