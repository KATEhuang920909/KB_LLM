# -*- coding: utf-8 -*-
# @Time    : 2020/11/9 16:54
# @Author  : huangkai21

"""
update es total sub question
"""
# from ir.search_file_name import Search
from nlp4es8.ir.index_hnsw import Index
from nlp4es8.ir.config import Config
import os
from tqdm import tqdm


# from utils.args import FLAGS


class Es_Update():
    def __init__(self, filename):
        self.file_name_idx = self.update_file_name(filename)

    def update_file_name(self, index_name):
        # 同步ES库

        config = Config()

        index_file_name = Index(config.embedding_path, index_name)

        file_path = [os.path.join(config.dir_path, file)
                     for file in os.listdir(config.dir_path)]
        file_name = {i: {'document': "".join(k.split(".")[0].split("__")[-3:]), 'idx': i}
                     for i, k in enumerate(file_path)}
        file_name_idx = {"".join(k.split(".")[0].split("__")[-3:]): k for i, k in enumerate(file_path)}
        config.es.indices.delete("filename", ignore=[400, 404])

        create_info = index_file_name.create_index(config)
        print(create_info)
        if create_info == "创建成功":
            index_file_name.bulk_index(file_name, bulk_size=1000, config=config)
        return file_name_idx

    def update_content(self, file_path, index_name):
        # 同步ES库
        config = Config()
        index_file_content = Index(config.embedding_path, index_name)
        questions = index_file_content.data_convert_v3(file_path)
        update_info = index_file_content.create_index(config)
        print(update_info)
        if update_info == "创建成功":
            print(questions[100])
            print("index_name", index_name)
            index_file_content.bulk_index(questions, bulk_size=1000, config=config)
        return questions


if __name__ == '__main__':
    es_update = Es_Update()
    file_name_idx = es_update.update_file_name()
