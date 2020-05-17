from utility import get_children
import copy
from threading import Lock, Thread
import time

threads = {}

attach_detach = Lock()


def expand(node, path, frontier, history, opposing_history, used):
    if node in used:
        return False
    if node in opposing_history:
        return True

    if node in history:
        return False

    try:
        children = get_children(node)
    except:
        print('Non viable node caught')
        return False

    history[node] = copy.deepcopy(path)
    z = copy.deepcopy(path)
    z.append(node)
    frontier.extend([[x, z]
                     for x in children])

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
            if len(current[1]) > 9:
                break
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
            if len(current[1]) > 9:
                break
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

    active[0] = False
    frontierA.clear()
    frontierB.clear()

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
            target=dfs_start, args=(first, second, frontierA, frontierB, historyA, historyB, paths, active, already_used, used_count), name=first+second, daemon=True), 'used_count': used_count, 'already_used': already_used, 'frontierA': frontierA, 'frontierB': frontierB, 'historyA': historyA, 'historyB': historyB, 'paths': paths, 'count': 1, 'active': active, 'start': time.time()}
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
    print('searching', key, threads.keys())
    if key not in threads:
        print('searching2', key, threads.keys())
        raise ValueError('Search not found')

    return [copy.deepcopy(threads[key]['paths']), len(threads[key]['historyA'])+len(threads[key]['historyB']), len(threads[key]['frontierA'])+len(threads[key]['frontierB'])]
    # return [x for x_sublist in threads[key]['paths'] for x in x_sublist]


def detach_search(first='', second='', together='', kill=False):
    print('detach wating for ', first, second)
    attach_detach.acquire()

    key = first+second if first > second else second+first
    if together != '':
        key = together

    if key not in threads:
        key = ''

    if key is '':
        attach_detach.release()
        return

    thread = threads[key]
    new_val = thread['count'] - 1

    if new_val <= 0 or kill:
        thread['active'][0] = False
        new_val = 0

    thread['count'] = new_val

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
