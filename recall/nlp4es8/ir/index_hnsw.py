#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys

sys.path.append('../')
sys.path.append('../utils')

import warnings
import os
from tqdm import tqdm
import json

warnings.filterwarnings("ignore")

# from ir.config import Config
from elasticsearch import helpers
import pandas as pd
# from utils.args import FLAGS
# from utils.data_helper import Data
# from utils.logger_config import base_logger
from langchain.embeddings.huggingface import HuggingFaceEmbeddings

import gc


class Index(object):
    def __init__(self, embedding_path, index_name):
        # base_logger.info("Indexing ...")
        # self.embeddings = HuggingFaceEmbeddings(model_name=embedding_path,
        #                                         model_kwargs={'device': "cpu"},
        #                                         encode_kwargs={'normalize_embeddings': True})
        self.index_name = index_name

    # @staticmethod
    def data_convert(self, ):
        # base_logger.info("convert sql data into single doc")

        questions = {}
        embeddings = {}
        # 获取原始数据
        corpus = pd.read_csv('../data/corpus.tsv', sep='\t', header=None)
        # corpus = corpus[:100000]
        print(corpus.head())
        # embedding 数据
        with open("../data/doc_embedding") as f:
            for line in f:
                sp_line = line.strip('\n').split("\t")
                index, embedding = sp_line
                embedding = embedding.split(',')
                embedding = [float(k) for k in embedding]
                embeddings[int(index)] = embedding

        # print(int(index))
        print(embeddings[1])
        for key, value in corpus.iterrows():
            if not (value[1] or value[2].strip()):
                continue
            # print(value[0])
            questions[value[0]] = {'document': value[1], 'embedding': embeddings[value[0]]}

        return questions

    def data_convert_v2(self, dir_path):
        questions = {}

        import numpy as np
        files = [os.path.join(dir_path, file) for file in os.listdir(dir_path)]
        for i, file in tqdm(enumerate(files)):
            with open(file, encoding="utf8") as f:
                docs = f.readlines()
                docs = [json.loads(k.strip())["inside"] for k in docs]
        Embeddings = self.embeddings.embed_documents(docs[:100])
        for i, emb in enumerate(Embeddings[:100]):
            # print(value[0])
            questions[i] = {'document': docs[i], 'embedding': emb}
        return questions

    def data_convert_v3(self, file):
        question = {}
        with open(file, encoding="utf8") as f:
            docs = f.readlines()

        for i, content in enumerate(docs):
            question[i] = {'index': i, 'document': content}
        return question

    # @staticmethod
    def create_index(self, config):
        # base_logger.info("creating %s index ..." % config.index_name)
        request_body = {
            # 设置索引主分片数，每个主分片的副本数，默认分别是5和1

            "mappings": {

                "properties": {
                    "index": {
                        "type": "long",
                        "index": "false"},
                    "document": {
                        "type": "text",
                        # "analyzer": "index_ansj",
                        # "search_analyzer": "query_ansj",
                        "index": "true"
                    }
                }
            }
        }

        # print(config.index_name)
        # 若存在index，先删除index
        if config.es.indices.exists(index=self.index_name):
            print(f'{self.index_name}索引存在')
            return "索引存在"
        else:
            res = config.es.indices.create(index=self.index_name, body=request_body)
            # base_logger.info(res)
            print("Indices are created successfully")
            return "创建成功"

    # @staticmethod
    def bulk_index(self, questions, bulk_size, config):
        # base_logger.info("Bulk index for question")
        count = 1
        actions = []
        # print("questions:",questions)
        for index, values in questions.items():
            if count == 100:
                print(values)
            action = {
                "_index": self.index_name,
                "_id": index,
                "_source": values
            }
            actions.append(action)
            count += 1
            if count % 10000 == 0:
                print(count)
            if len(actions) % bulk_size == 0:
                helpers.bulk(config.es, actions)
                actions = []

        if len(actions) > 0:
            helpers.bulk(config.es, actions)
            print("Bulk index: %s" % str(count))

# if __name__ == '__main__':
#     config = Config(FLAGS.env)
#     index = Index()
#     # index.create_index(config)
#     questions = index.data_convert()
#     print(questions[3])
#
#     index.bulk_index(questions, bulk_size=10000, config=config)
