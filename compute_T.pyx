# cython: boundscheck=False, wraparound=False, nonecheck=False
import numpy as np
cimport numpy as np

def build_matrix_by_lookup_c(
    int n,
    list row_map,
    list col_map,
    np.ndarray[np.uint8_t, ndim=2] matrix
) -> np.ndarray:
    cdef int i, j
    cdef int row1, row2, col1, col2

    # Allocate result array
    cdef np.ndarray[np.uint8_t, ndim=2] result = np.zeros((n, n), dtype=np.bool_)

    for i in range(n):
        for j in range(n):
            row1 = row_map[i]
            row2 = row_map[j]
            col1 = col_map[i]
            col2 = col_map[j]
            result[i, j] = matrix[row1, col2] & matrix[row2, col1]

    return result