# -*- coding: utf-8 -*-
# @Time    : 2022/3/30 20:43
# @Author  : huangkai
# @File    : search_content.py


import sys

sys.path.append('../')
sys.path.append('../utils')

from nlp4es8.ir.config import Config


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
                    data['_source']['document'],
                    data['_source']['type']
                )
            )
        return result

        # base_logger.info("ReadTimeOutError may not be covered!")


if __name__ == '__main__':
    import pandas as pd

    index_file_content_config = Config()
    index_file_content_config.index_name = "锦江酒店2019年年度报告"
    search_name = Search(index_file_content_config)
    while True:
        query = input("please input")
        result = search_name.searchAnswer(query)
        for data in result:
            print("question:%s  question_id:%s  " % (data[0], data[1]))
