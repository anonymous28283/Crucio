class MatrixQuerier:
    def __init__(self, mat):
        self.mat = mat

    def query(self, rows, cols):
        for i in rows:
            for j in cols:
                if self.mat[i, j] == 0:
                    return 0
        return 1

    def query_block(self, rows_block, cols_block):
        return all(self.query(rows, cols)
                   for rows in rows_block for cols in cols_block
                   )

