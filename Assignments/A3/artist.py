costs = [
    [0, 143, 108, 118, 121, 88, 121, 57, 92],  # Home
    [143, 0, 35, 63, 108, 228, 182, 73, 162],  # A
    [108, 35, 0, 45, 86, 193, 165, 42, 129],  # B
    [118, 63, 45, 0, 46, 190, 203, 73, 105],  # C
    [121, 108, 86, 46, 0, 172, 224, 98, 71],  # D
    [88, 228, 193, 190, 172, 0, 174, 160, 108],  # E
    [121, 182, 165, 203, 224, 174, 0, 129, 212],  # F
    [57, 73, 42, 73, 98, 160, 129, 0, 117],  # G
    [92, 162, 129, 105, 71, 108, 212, 117, 0],  # H
]

p = [
    [0.0, 0.0, 0.0],  # Home
    [0.3, 0.4, 0.3],  # A
    [0.2, 0.5, 0.3],  # B
    [0.2, 0.7, 0.1],  # C
    [0.3, 0.5, 0.2],  # D
    [0.3, 0.6, 0.1],  # E
    [0.4, 0.3, 0.3],  # F
    [0.0, 0.3, 0.7],  # G
    [0.1, 0.1, 0.8],  # H
]

Home = 0
Price = 500
Cities = range(len(costs))
K = range(3)
Sales = [sum(k * p[i][k] for k in K) for i in Cities]


def art(t, i, S):
    if t == 5:
        return (-costs[i][Home], Home)
    return max(
        (-costs[i][j] + 500 * Sales[j] + art(t + 1, j, S + (j,))[0], j)
        for j in Cities
        if j not in S
    )


def art2(t, i, S, n):
    if t == 5 or n == 0:
        return (-costs[i][Home], Home)
    return max(
        (
            -costs[i][j]
            + sum(
                p[j][k] * (500 * min(k, n) + art2(t + 1, j, S + (j,), max(n - k, 0))[0])
                for k in K
            ),
            j,
        )
        for j in Cities
        if j not in S
    )


print(art2(5, 5, 500, 5))
