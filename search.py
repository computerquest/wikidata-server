from utility import get_children
import copy
import threading

threads = {}


def expand(node, path, frontier, history, opposing_history, used):
    if node in used:
        return False
    if node in opposing_history:
        return True

    if node in history:
        return False

    history[node] = copy.deepcopy(path)
    z = copy.deepcopy(path)
    z.append(node)
    frontier.extend([[x, z]
                     for x in get_children(node)])
    return False


def dfs(root_id, path, frontier, history, opposing_history, used):
    if expand(root_id, path, frontier, history, opposing_history, used):
        return [True, path+[root_id], root_id]

    return [False]


def dfs_start(root_id, target_id, historyA={}, historyB={}, paths=[]):
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


def launch_search(first, second):
    if (first+second) not in threads and (second+first) not in threads:
        historyA = {}
        historyB = {}
        paths = []  # , historyA, historyB, paths
        threads[first+second] = {'thread': threading.Thread(
            target=dfs_start, args=(first, second, historyA, historyB, paths), name=first+second, daemon=True), 'historyA': historyA, 'historyB': historyB, 'paths': paths}
        threads[first+second]['thread'].start()

        # threads[first+second]['thread'].join()


def get_search_progress(first, second):
    key = ''
    if (first+second) in threads:
        key = (first+second)
    elif (second+first) in threads:
        key = second+first
    else:
        raise 'Search not found'

    return list(threads[key]['historyA'].keys())+list(threads[key]['historyB'].keys()), threads[key]['paths']


def kill_search(first, second):
    key = ''
    if (first+second) in threads:
        key = (first+second)
    elif (second+first) in threads:
        key = second+first
    else:
        raise 'Search not found'

    threads[key]['thread'].kill()


if __name__ == '__main__':
    print(launch_search('wd:Q76', 'wd:Q13133'))
