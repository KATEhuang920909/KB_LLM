# -*- coding: utf-8 -*-
# Time : 2020/8/12 17:49
# Author : huangkai21
# FileName: filter.py
# mail : 18707125049@163.com
import sys

sys.path.append('../')
sys.path.append('../utils')

from utils.logger_config import base_logger
import numpy as np
import joblib
from utils.args import FLAGS
from utils.data_helper import GetFeatures


class Filter(object):

    def __init__(self):
        base_logger.info('==========================加载过滤器========================')
        self.filter_model = joblib.load(FLAGS.filter_model_path)
        self.gf = GetFeatures()

    def get_filter_result(self, df):
        base_logger.info('==================开始过滤数据并获取bert句向量矩阵==========')
        bert_corpus = df['question'].values.tolist()
        feature_matrix = self.gf.get_bert_matrix(bert_corpus)
        # print(feature_matrix.shape)
        pred = self.filter_model.predict(feature_matrix)

        df['filter_pred'] = np.where(pred > 0.5, True, False)
        df.to_csv(r'drop_vec_result.csv', index=False)
        result = df[df.filter_pred == True]
        filter_pred = df['filter_pred'].values.tolist()
        del df['filter_pred'], result['filter_pred']
        feature_matrix = feature_matrix[filter_pred]

        filter_num = df.shape[0] - result.shape[0]
        result = result.reset_index(drop=True)

        base_logger.info('模型过滤：%s条, 剩余%s条' % (filter_num, result.shape[0]))
        return result, feature_matrix


if __name__ == "__main__":
    filter = Filter()
    import pandas as pd

    df = pd.read_csv("../ir/vec_result.csv", encoding="utf-8")

    filter.get_filter_result(df)
