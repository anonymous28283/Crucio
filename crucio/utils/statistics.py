import time

from crucio.consts import SEP
global_dict = {}
timings = {}
averages = {}

def resetTiming():
    timings.clear()


def timer(timer_name):
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            execution_time = end_time - start_time
            if timer_name not in timings:
                timings[timer_name] = 0
            timings[timer_name] += execution_time
            return result

        return wrapper

    return decorator


def timing(name):
    return (time.time(), name)


import time


class RecordTime:
    def __init__(self, name):
        self.name = name

    def __enter__(self):
        self.tag = timing(self.name)

    def __exit__(self, exc_type, exc_val, exc_tb):
        record(self.tag)


def record(x):
    start, name = x
    if name not in timings:
        timings[name] = 0
    timings[name] += time.time() - start
    return (time.time(), name)


counts = {}


def counting(x, n=1):
    if x not in counts:
        counts[x] = 0
    counts[x] += n


def counter(counter_name):
    def decorator(func):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            if counter_name not in counts:
                counts[counter_name] = 0
            counts[counter_name] += 1
            return result

        return wrapper

    return decorator


def average(name, value):
    if name not in averages:
        averages[name] = []
    averages[name].append(value)


hits = {}
misses = {}


def hitRecorder(name, count=1):
    if name not in hits:
        hits[name] = 0
    hits[name] += count


def missRecorder(name, count=1):
    if name not in misses:
        misses[name] = 0
    misses[name] += count


def getHitRate(name):
    return hits.get(name, 0) / (hits.get(name, 0) + misses.get(name, 0))


def showStatistics():
    print(SEP)
    print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())))
    for k in sorted(timings.keys(),key=timings.get):
        print('%s: %fs' % (str(k).ljust(25), timings[k]))
    print('\ncounter:')
    for k, v in counts.items():
        print('%s: %d' % (str(k).ljust(25), v))
    print('\nAverages:')
    for k,v in averages.items():
        avg = sum(v) / len(v) if v else 0
        print(f"{k:<25}: {avg:.2f} (count: {len(v)})")

    print('\nHit Rate:')
    for k in set(hits.keys()).union(misses.keys()):
        hitCount = hits.get(k, 0)
        missCount = misses.get(k, 0)
        total = hitCount + missCount
        hitRate = (hitCount / total * 100) if total > 0 else 100
        print(f"{k:<25}: {hitRate:.2f}% (hits: {hitCount}, misses: {missCount})")
    print(SEP)


if __name__ == '__main__':
    average('a', 1)
    average('b', 2)
    showStatistics()
