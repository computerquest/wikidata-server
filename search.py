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


def groom_frontier(used, frontier):
    badIndexes = []
    for i in range(0, len(frontier)):
        path = frontier[i][1]

        if frontier[i][0] in used:
            badIndexes.append(i)
            continue

        inFrontier = False

        for node in path:
            if node in used:
                inFrontier = True
                break

        if inFrontier:
            badIndexes.append(i)

    badIndexes.reverse()

    for x in badIndexes:
        del frontier[x]


def dfs_start(root_id, target_id, historyA={}, historyB={}, paths=[]):
    frontierA = [[root_id, []]]
    frontierB = [[target_id, []]]
    comp = []

    already_used = []  # this is to get rid of using the same nodes repeatedly
    used_count = {}

    for i in range(0, 10000000000):
        current = frontierA.pop(0)
        comp = dfs(current[0], current[1], frontierA,
                   historyA, historyB, already_used)
        if comp[0] == True:
            new_path = comp[1]+historyB[current[0]][::-1]
            # already_used.extend(new_path[1:-1])

            for x in new_path[1:-1]:
                if x not in used_count.keys():
                    used_count[x] = 1
                else:
                    used_count[x] = used_count[x]+1

                if used_count[x] >= 5:
                    already_used.append(x)

            paths.append(comp[1]+historyB[current[0]][::-1])
            groom_frontier(already_used, frontierA)
            groom_frontier(already_used, frontierB)

        current = frontierB.pop(0)
        comp = dfs(current[0], current[1], frontierB,
                   historyB, historyA, already_used)
        if comp[0] == True:
            new_path = historyA[comp[2]]+comp[1][::-1]
            # already_used.extend(new_path[1:-1])

            for x in new_path[1:-1]:
                if x not in used_count.keys():
                    used_count[x] = 1
                else:
                    used_count[x] = used_count[x]+1

                if used_count[x] >= 5:
                    already_used.append(x)

            paths.append(historyA[comp[2]]+comp[1][::-1])
            groom_frontier(already_used, frontierA)
            groom_frontier(already_used, frontierB)

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

    return threads[key]['paths']
    # return [x for x_sublist in threads[key]['paths'] for x in x_sublist]


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
