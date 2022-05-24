from itertools import combinations, permutations
from typing import Iterable
from collections import defaultdict
from time import time

Z = range(9)
outbreak_probs = [0.2 for j in Z]
# The state is a 9-tuple where each element is
# -1 = outbreak, 0 = normal, 1 = protected
# NextStates returns a list of tuples with a probability
# in position 0 and a state as a tuple in position 1
def NextStates(State, OutbreakProb):
    ans = []
    # Z0 are the normal zones
    Z0 = [j for j in Z if State[j] == 0]
    n = len(Z0)
    for i in range(n + 1):
        for tlist in combinations(Z0, i):
            p = 1.0
            slist = list(State)
            for j in range(n):
                if Z0[j] in tlist:
                    p *= OutbreakProb[Z0[j]]
                    slist[Z0[j]] = -1
                else:
                    p *= 1 - OutbreakProb[Z0[j]]
            ans.append((p, tuple(slist)))
    return ans


comm12_order = [4, 8, 6, 5, 3, 0, 7, 2, 1]


def replace_at_index(state, idx, val):
    return state[:idx] + (val,) + state[idx + 1 :]


def target_in_order(next_state, target_order):
    for idx in target_order:
        if applied_target := target_state(next_state, idx):
            return applied_target

    return next_state


def target_state(next_state, target_idx):
    # If we can target a zone in this state, target it
    if next_state[target_idx] == 0:
        return replace_at_index(next_state, target_idx, 1)


def flatten(iterable):
    for i in iterable:
        if isinstance(i, Iterable):
            yield from flatten(i)
        else:
            yield i


# Over each of the new states, what is the expected
# In a given state, what is the best action (and what is the maximum val associated with this)

Zones = [
    [0, 2, 7],
    [14],
    [9, 15],
    [3, 6, 15],
    [6, 7, 10, 14, 15],
    [1, 4, 6],
    [5, 7, 12],
    [6, 11],
    [4, 8, 10, 13],
]

state_facilities_map = {}

for i in range(10):
    for indices in combinations(Z, i):
        state = tuple(1 if i in indices else -1 for i in Z)
        state_facilities_map[state] = len(set(flatten([Zones[i] for i in indices])))


def value_function(state, prob, target_order):
    if 0 not in state:
        return state_facilities_map[state] * prob

    return sum(
        value_function(
            target_in_order(next_state, target_order), prob * next_prob, target_order
        )
        for next_prob, next_state in NextStates(state, outbreak_probs)
    )


state_value_map = defaultdict(int)


def value_function_memo(state, prob, target_order):
    if 0 not in state:
        return state_facilities_map[state] * prob

    if value := state_value_map[state]:
        return value

    total = 0.0
    for next_prob, next_state in NextStates(state, outbreak_probs):
        value = value_function_memo(
            target_in_order(next_state, target_order),
            prob * next_prob,
            target_order,
        )
        total += value

    state_value_map[state] = total
    return total


# max_val = 0.0
# for idx, order in enumerate(permutations(Z, 9)):
#     if idx % 10000 == 0:
#         print(f"here - {idx}")
#     value = value_function_memo((0, 0, 0, 0, 0, 0, 0, 0, 0), 1.0, order)
#     if value >= max_val:
#         max_val = value

# print(max_val)

value = value_function_memo((0, 0, 0, 0, 1, 0, 0, 0, 0), 1.0, comm12_order)

print(value)

Facilities = [
    "Wedding Chapel",
    "Post Office",
    "Bank",
    "Town Hall",
    "Ambulance",
    "Government Office",
    "Hotel",
    "Medical Centre",
    "Bus Depot",
    "Library",
    "Convenience Store",
    "Hospital",
    "Fire Station",
    "Police Station",
    "Supermarket",
    "School",
]
