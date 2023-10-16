# Michael A. Alcorn (malcorn@redhat.com)
# [1] Zhai, C. and Lafferty, J. 2004. A study of smoothing methods for language models applied
#         to information retrieval. In ACM Transactions on Information Systems (TOIS), pp. 179-214.
#         http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.94.8019&rep=rep1&type=pdf

from math import log


class LMIR:
    def __init__(self, corpus, lamb=0.1, mu=2000, delta=0.7):
        """Use language models to score query/document pairs.

        :param corpus: 
        :param lamb: 
        :param mu: 
        :param delta: 
        """
        self.lamb = lamb
        self.mu = mu
        self.delta = delta

        # Fetch all of the necessary quantities for the document language
        # models.
        doc_token_counts = []
        doc_lens = []
        doc_p_mls = []
        all_token_counts = {}
        for doc in corpus:
            doc_len = len(doc)
            doc_lens.append(doc_len)
            token_counts = {}
            for token in doc:
                token_counts[token] = token_counts.get(token, 0) + 1
                all_token_counts[token] = all_token_counts.get(token, 0) + 1

            doc_token_counts.append(token_counts)

            p_ml = {}
            for token in token_counts:
                p_ml[token] = token_counts[token] / doc_len

            doc_p_mls.append(p_ml)

        total_tokens = sum(all_token_counts.values())
        p_C = {
            token: token_count / total_tokens
            for (token, token_count) in all_token_counts.items()
        }

        self.N = len(corpus)
        self.c = doc_token_counts
        self.doc_lens = doc_lens
        self.p_ml = doc_p_mls
        self.p_C = p_C

    def jelinek_mercer(self, query_tokens):
        """Calculate the Jelinek-Mercer scores for a given query.

        :param query_tokens: 
        :return: 
        """
        lamb = self.lamb
        p_C = self.p_C
        scores = []
        for doc_idx in range(self.N):
            p_ml = self.p_ml[doc_idx]
            score = 0
            for token in query_tokens:
                if token not in p_C:
                    continue

                score -= log((1 - lamb) * p_ml.get(token, 0) + lamb * p_C[token])

            scores.append(score)

        return scores

    def dirichlet(self, query_tokens):
        """Calculate the Dirichlet scores for a given query.

        :param query_tokens: 
        :return: 
        """
        mu = self.mu
        p_C = self.p_C

        scores = []
        for doc_idx in range(self.N):
            c = self.c[doc_idx]
            doc_len = self.doc_lens[doc_idx]
            score = 0
            for token in query_tokens:
                if token not in p_C:
                    continue

                score -= log((c.get(token, 0) + mu * p_C[token]) / (doc_len + mu))

            scores.append(score)

        return scores

    def absolute_discount(self, query_tokens):
        """Calculate the absolute discount scores for a given query.

        :param query_tokens: 
        :return: 
        """
        delta = self.delta
        p_C = self.p_C

        scores = []
        for doc_idx in range(self.N):
            c = self.c[doc_idx]
            doc_len = self.doc_lens[doc_idx]
            d_u = len(c)
            score = 0
            for token in query_tokens:
                if token not in p_C:
                    continue

                score -= log(
                    max(c.get(token, 0) - delta, 0) / doc_len
                    + delta * d_u / doc_len * p_C[token]
                )

            scores.append(score)

        return scores


if __name__ == "__main__":

    import os
    import numpy as np
    import json
    import argparse
    from tqdm import tqdm
    import jieba

    parser = argparse.ArgumentParser(description="Help info.")
    parser.add_argument('--s', type=str, default='data/others/stopword.txt', help='Stopword path.')
    parser.add_argument('--input', type=str, help='input path of the dataset directory.')
    parser.add_argument('--data_type', type=str, help='Write path.')
    parser.add_argument('--output', type=str, default='baseline_stage2', help='Write path.')
    args = parser.parse_args()

    input_candidate_path = os.path.join(args.input, 'candidates_stage2')
    input_query_path = os.path.join(args.input,  'query_stage2.json')

    with open(args.s, 'r', encoding='utf-8') as g:
        words = g.readlines()
    stopwords = [i.strip() for i in words]
    stopwords.extend(['.', '（', '）', '-'])

    with open(input_query_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    print('begin...')
    result0 = {}

    for line in tqdm(lines):
        corpus = []
        query = str(eval(line)['ridx'])  # query's code
        # model init
        # result[query] = []
        files = os.listdir(os.path.join(input_candidate_path, query))
        for file_ in files:
            file_json = json.load(
                open(os.path.join(input_candidate_path, query, file_), 'r', encoding='utf-8'))  # candi per file
            a = jieba.cut(file_json['ajjbqk'], cut_all=False)  # 案件基本情况
            tem = " ".join(a).split()  # 字
            corpus.append([i for i in tem if not i in stopwords])
        lmir = LMIR(corpus)  # 字符级bm25

        # rank
        a = jieba.cut(eval(line)['q'], cut_all=False)  # 查询案例内容
        tem = " ".join(a).split()
        q = [i for i in tem if not i in stopwords]
        raw_rank_index = np.array(lmir.jelinek_mercer(q)).argsort().tolist()  # lc的结果
        # result[query] = [int(files[i].split('.')[0]) for i in raw_rank_index]

        result0[query] = [int(files[i].split('.')[0]) for i in raw_rank_index]
    if not os.path.exists(args.output):
        os.mkdir(args.output)
    # json.dump(result, open(os.path.join(args.output, 'dirichlet_prediction.json'), "w", encoding="utf8"), indent=2,
    #           ensure_ascii=False, sort_keys=True)
    json.dump(result0, open(os.path.join(args.output, args.data_type+'_lmir_prediction.json'), "w", encoding="utf8"), indent=2,
              ensure_ascii=False, sort_keys=True)

    print('ouput done.')
