#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys

# sys.path.append('../')
# sys.path.append("../utils")

from elasticsearch import Elasticsearch
# from utils.logger_config import base_logger


class Config(object):
    def __init__(self, ):
        # print("config...")

        # self.model_type = "bert-service"  # "bert" or "lstm_raw" or "lstm_magic" or "bilstm_magic"
        # logger.info("Model_type:%s  Env_choose:%s" % (self.model_type, env))

        # 读取配置文件
        # env_list = get_option_values('es_server')
        # if env not in env_list:
        #     raise Exception('请输入正确的环境（int/test/prd中的一种）')

        # 获取host地址
        # host = get_config_values('es_server', env)
        # host_list = host.split(',')
        host_list = ["127.0.0.1"]
        # base_logger.info('connect es server in: %s' % (host_list))
        host_list = [{'host': h, 'port': 9200} for h in host_list]
        self.embedding_path = r"D:\代码\pretrained_model\bert-base-chinese"
        # self.dir_path = r"D:\compet\SMP 2023 ChatGLM金融大模型挑战赛\alltxt"
        self.dir_path = r"D:\代码\SMP_ChatGLM\alltxt"
        # # 开发环境的ES
        self.es = Elasticsearch(
            host_list,
            sniff_on_start=False,
            sniff_on_connection_fail=False,
            sniffer_timeout=0,

        )

        # self.index_name = "my-approx-knn-index"
        # self.index_name = "robotkdb_all"
        # self.index_name = "knn_test2"
        # self.doc_type = "all_question"
        self.top_n = 10

# if __name__ == '__main__':
# Config = Config(env='int')
