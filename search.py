from utility import request_entity, extract_objects


def expand(node, path, frontier, history, opposing_history):
    path.append(node)

    if node in opposing_history:
        return True

    if node not in history:
        history[node] = path

    frontier.extend([[x, path] for x in extract_objects(request_entity(node))])
    return False


def dfs(root_id, path, frontier, history, opposing_history):
    if expand(root_id, path, frontier, history, opposing_history):
        return [True, path, root_id]

    return [False]


def dfs_start(root_id, target_id):
    historyA = {}
    historyB = {}
    frontierA = [[root_id, []]]
    frontierB = [[target_id, []]]
    comp = []

    for i in range(0, 20):
        current = frontierA.pop()
        comp = dfs(current[0], current[1], frontierA, historyA, historyB)
        if comp[0] == True:
            return comp[1]+historyB[comp[2]]

        current = frontierB.pop()
        comp = dfs(current[0], current[1], frontierB, historyB, historyA)
        if comp[0] == True:
            return historyA[comp[2]]+comp[2]

    return []


if __name__ == '__main__':
    print(dfs_start('wd:Q76', 'wd:Q7793121'))
