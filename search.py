from utility import get_children
import copy
from threading import Lock, Thread

threads = {}

attach_detach = Lock()


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


def dfs_start(root_id, target_id, frontierA=[], frontierB=[], historyA={}, historyB={}, paths=[], active=[True], already_used=[], used_count={}):
    if frontierA == []:
        frontierA = [[root_id, []]]

    if frontierB == []:
        frontierB = [[target_id, []]]

    comp = []

    # already_used = []  # this is to get rid of using the same nodes repeatedly
    #used_count = {}

    while active[0] and (len(frontierB) != 0 or len(frontierA) != 0):
        if len(frontierA) != 0:
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

        if len(frontierB) != 0:
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
    attach_detach.acquire()

    key = first+second if first > second else second+first
    if key not in threads:
        key = ''

    if key == '':
        print('starting thread for', first, second)
        key = first+second if first > second else second+first
        historyA = {}
        historyB = {}
        frontierA = [[first, []]]
        frontierB = [[second, []]]
        paths = []
        active = [True]
        already_used = []
        used_count = {}
        threads[key] = {'thread': Thread(
            target=dfs_start, args=(first, second, frontierA, frontierB, historyA, historyB, paths, active, already_used, used_count), name=first+second, daemon=True), 'used_count': used_count, 'already_used': already_used, 'frontierA': frontierA, 'frontierB': frontierB, 'historyA': historyA, 'historyB': historyB, 'paths': paths, 'count': 1, 'active': active}
        threads[key]['thread'].start()

        # threads[first+second]['thread'].join()
    else:
        print('search already done', first, second)
        threads[key]['count'] = threads[key]['count']+1

        if not threads[key]['active'][0]:
            print('restarting', first, second)
            threads[key]['active'][0] = True
            threads[key]['thread'] = Thread(
                target=dfs_start, args=(first, second, threads[key]['frontierA'], threads[key]['frontierB'], threads[key]['historyA'], threads[key]['historyB'], threads[key]['paths'], threads[key]['active'], threads[key]['already_used'], threads[key]['used_count']), name=first+second, daemon=True)
            threads[key]['thread'].start()

    attach_detach.release()


def get_search_progress(first, second):
    key = first+second if first > second else second+first
    if key not in threads:
        raise 'Search not found'

    return [threads[key]['paths'], len(threads[key]['historyA'])+len(threads[key]['historyB']), len(threads[key]['frontierA'])+len(threads[key]['frontierB'])]
    # return [x for x_sublist in threads[key]['paths'] for x in x_sublist]


def detach_search(first, second):
    print('detach wating for ', first, second)
    attach_detach.acquire()

    key = first+second if first > second else second+first
    if key not in threads:
        key = ''

    if key is '':
        attach_detach.release()
        return

    new_val = threads[key]['count'] - 1
    threads[key]['count'] = new_val

    if new_val <= 0:
        threads[key]['active'][0] = False

    print('count for ', key, 'at',
          threads[key]['count'], threads[key]['active'][0])

    attach_detach.release()
    print('detach release', first, second)


def kill_search(first, second):
    key = first+second if first > second else second+first
    if key not in threads:
        raise 'Search not found'

    threads[key]['thread'].kill()


if __name__ == '__main__':
    print(launch_search('wd:Q76', 'wd:Q13133'))
