# -*- coding: utf-8 -*-
# @Time    : 2020/11/9 16:54
# @Author  : huangkai21

"""
update es total sub question
"""
# from ir.search_file_name import Search
from nlp4es8.ir.index_traditional import Index
from nlp4es8.ir.es_config import Config
import os
from tqdm import tqdm


# from utils.args import FLAGS


class Es_Update():
    def create_index(self,index_name):
        pass
    def update_content(self, file_path, index_name):
        # 同步ES库
        config = Config()
        index_file_content = Index(config.embedding_path, index_name)
        questions = index_file_content.data_convert_v3(file_path)

        print(update_info)
        if update_info == "创建成功":
            print(questions[100])
            print("index_name", index_name)
            index_file_content.bulk_index(questions, bulk_size=1000, config=config)
        return questions


# if __name__ == '__main__':
#     update_info = index_file_content.create_index(config)
#     es_update = Es_Update()
#     for i in range(9):
#         file_name_idx = es_update.update_content(f"../../data/kbqa{i}.txt","KBQA")
