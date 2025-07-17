"""
压缩分布矩阵
"""
from typing import Collection, FrozenSet, Dict, Set

import numpy as np

from crucio.data_types.distribution.matrix import DistributionalMatrix


class CompressedDM:
    def __init__(self, dm: DistributionalMatrix):
        self.__mat = np.copy(dm.getMatrix())
        self.__cons = [{i} for i in dm.getContexts()]
        self.__subs = [{i} for i in dm.getSubseqs()]

    def update_dm(self, dm: DistributionalMatrix):
        rows_map = {}
        cols_map = {}
        # 更新subs
        m = 0
        for i in range(len(dm.getSubseqs())):
            if {dm.getSubseqs()[i]} not in self.__subs:
                self.__subs.append({dm.getSubseqs()[i]})
                m += 1
        # 更新cons
        n = 0
        for i in range(len(dm.getContexts())):
            if {dm.getContexts()[i]} not in self.__cons:
                self.__cons.append({dm.getContexts()[i]})
                n += 1

        # 更新__mat
        B = np.pad(self.__mat, pad_width=((0, m), (0, n)), mode='constant', constant_values=0)
        for i in range(len(self.__subs)-m,len(self.__subs)):
            for j in range(len(self.__cons)):
                B[i,j] = all(dm.getMatrix()[dm.getIndexBySubseq(sub),dm.getIndexByContext(con)]
                             for sub in self.__subs[i] for con in self.__cons[j])
        for j in range(len(self.__cons)-n,len(self.__cons)):
            for i in range(len(self.__subs)):
                B[i,j] = all(dm.getMatrix()[dm.getIndexBySubseq(sub),dm.getIndexByContext(con)]
                             for sub in self.__subs[i] for con in self.__cons[j])
        self.__mat = B
        assert self.__mat.shape[0] == len(self.subs)
        assert self.__mat.shape[1] == len(self.cons)
        return rows_map,cols_map
    @property
    def mat(self):
        return self.__mat

    def __getitem__(self, item):
        return self.__mat[item]

    def __compress_rows(self, rows) -> int:
        rows = list(rows)
        if len(rows) == 1:
            return rows[0]

        # 遍历self.__mat所有的row,进行and操作
        new_row = np.bitwise_and.reduce(self.__mat[rows], axis=0)

        # 添加一个新row到self.__mat
        self.__mat = np.vstack([self.__mat, new_row])
        return self.__mat.shape[0] - 1

    def __compress_cols(self, cols) -> int:
        cols = list(cols)
        if len(cols) == 1:
            return cols[0]

        # 遍历self.__mat所有的col,进行and操作
        new_col = np.bitwise_and.reduce(self.__mat[:, cols], axis=1)

        # 添加一个新col到self.__mat
        self.__mat = np.hstack([self.__mat, new_col[:, np.newaxis]])
        return self.__mat.shape[1] - 1

    def __trim_matrix(self, rows_map, cols_map):
        valid_rows, valid_cols = rows_map.values(), cols_map.values()
        m, n = self.__mat.shape
        invalid_rows: Set[int]
        invalid_cols: Set[int]
        invalid_rows, invalid_cols = set(range(m)).difference(valid_rows), set(range(n)).difference(valid_cols)
        # 删除无效的行
        for row in sorted(invalid_rows, reverse=True):  # 倒序删除避免索引错乱
            # 删除row
            self.__mat = np.delete(self.__mat, row, axis=0)

            # 更新rows_map中所有大于row的index减1
            for key in rows_map:
                if rows_map[key] > row:
                    rows_map[key] -= 1
        # 删除无效的列
        for col in sorted(invalid_cols, reverse=True):  # 同样倒序删除
            # 删除col
            self.__mat = np.delete(self.__mat, col, axis=1)

            # 更新cols_map中所有大于col的index减1
            for key in cols_map:
                if cols_map[key] > col:
                    cols_map[key] -= 1

    def __update_con_sub(self, rows_map, cols_map):
        m, n = self.__mat.shape
        # 遍历rows_map 聚合之前的sub
        new_subs = [set() for _ in range(m)]
        for k, v in rows_map.items():
            new_subs[v] = set().union(*[self.__subs[i] for i in k])
        # 遍历cols集合 聚合之前的col
        new_cons = [set() for _ in range(n)]
        for k, v in cols_map.items():
            new_cons[v] = set().union(*[self.__cons[i] for i in k])
        self.__cons = new_cons
        self.__subs = new_subs

    def compress(self, all_rows: Collection[FrozenSet[int]], all_cols: Collection[FrozenSet[int]]):
        rows_map: Dict[FrozenSet[int], int] = {}
        cols_map: Dict[FrozenSet[int], int] = {}
        # Step1. 遍历所有的rows
        for rows in all_rows:
            rows_map[rows] = self.__compress_rows(rows)
        # Step2. 遍历所有的cols
        for cols in all_cols:
            cols_map[cols] = self.__compress_cols(cols)
        # Step3. 删除一些无效的行
        self.__trim_matrix(rows_map, cols_map)
        # Step4. 更新cons和subs
        self.__update_con_sub(rows_map, cols_map)
        # Step5. 返回
        return rows_map, cols_map

    @property
    def cons(self):
        return self.__cons

    @property
    def subs(self):
        return self.__subs
