from utility import request_entity, extract_objects
import copy


def expand(node, path, frontier, history, opposing_history, used):
    if not node in used:
        return False
    if node in opposing_history:
        return True

    if node in history:
        return False

    history[node] = copy.deepcopy(path)
    z = copy.deepcopy(path)
    z.append(node)
    frontier.extend([[x, z]
                     for x in extract_objects(request_entity(node))])
    return False


def dfs(root_id, path, frontier, history, opposing_history, used):
    if expand(root_id, path, frontier, history, opposing_history, used):
        return [True, path+[root_id], root_id]

    return [False]


def dfs_start(root_id, target_id):
    paths = []
    historyA = {}
    historyB = {}
    frontierA = [[root_id, []]]
    frontierB = [[target_id, []]]
    comp = []

    already_used = []  # this is to get rid of using the same nodes repeatedly

    for i in range(0, 10000000000):
        current = frontierA.pop(0)
        comp = dfs(current[0], current[1], frontierA,
                   historyA, historyB, already_used)
        if comp[0] == True:
            new_path = comp[1]+historyB[current[0]][::-1]
            already_used.extend(new_path[1:-1])
            paths.append(comp[1]+historyB[current[0]][::-1])

        current = frontierB.pop(0)
        comp = dfs(current[0], current[1], frontierB,
                   historyB, historyA, already_used)
        if comp[0] == True:
            new_path = historyA[comp[2]]+comp[1][::-1]
            already_used.extend(new_path[1:-1])
            paths.append(historyA[comp[2]]+comp[1][::-1])

    return paths


if __name__ == '__main__':
    print(dfs_start('wd:Q76', 'wd:Q2722764'))
