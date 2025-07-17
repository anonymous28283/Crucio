import os
import pickle
import threading
from datetime import datetime

from matplotlib.figure import Figure

from crucio.config import Config
from crucio.consts import SEP, projectPath
import time

loggers = []
files = {}


def flushAllFiles(intervalSeconds: int = 1):
    def flushLoop():
        while True:
            for file in list(files.values()):
                try:
                    file.flush()
                except Exception as e:
                    print(f"[Flush Error] {e}")
            time.sleep(intervalSeconds)

    t = threading.Thread(target=flushLoop, daemon=True)
    t.start()


def getFormattedTime():
    current_time = datetime.now()

    formatted_time = current_time.strftime("%m-%d_%H-%M-%S.%f")

    return formatted_time


startTime = getFormattedTime()
directory = f'{projectPath}Runtime/Logs/{startTime}/'


def getFile(path):
    if not Config.log:
        return open(os.devnull, 'w')
    if path is None:
        return None
    if path not in files:
        if not os.path.exists(directory):
            os.makedirs(directory)
        files[path] = open(directory + path, mode='a')
    return files[path]


import time


class LogTimer:
    def __init__(self, logger, title="operation"):
        self.logger = logger
        self.title = title

    def __enter__(self):
        self.logger.title(f'{self.title} start')
        self._start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        end = time.perf_counter()
        duration = end - self._start
        self.logger.print(f'{self.title} finished，cost {duration:.3f}s')
        self.logger.print()


class Logger:
    @staticmethod
    def setTag(tag):
        global directory
        directory = f'{projectPath}Runtime/Logs/{startTime}-{tag}/'

    def __init__(self, filename: str = None, parent: "Logger" = None):
        self.__filename = filename
        self.__parent = parent
        loggers.append(self)

    def getFilename(self) -> str:
        return directory + self.__filename

    def getDirectory(self):
        return directory

    def print(self, *args, **kwargs):
        print(*args, file=getFile(self.__filename), **kwargs)

    def title(self, title: str):
        self.print(SEP)
        self.print(title)
        self.print(SEP)

    def save(self, fig: Figure, name: str):
        fig.savefig(f'{self.getDirectory()}{name}.png')

    def dump(self, obj, name: str):
        path = f'{self.getDirectory()}{name}.pickle'
        with open(path, 'wb') as f:
            pickle.dump(obj, f)

    def trace(self, info=None):
        import time
        assert self.__parent is not None
        if info is not None:
            fullText = '[%s id=%d %s]\n%s' % (self.__filename, time.time_ns(),
                                              time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())), info)
        else:
            fullText = '[%s id=%d %s]' % (self.__filename, time.time_ns(),
                                          time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())))
        self.__parent.print(fullText)
        self.title(fullText)

    def fork(self, filename: str, saveAtOnce: bool = False):
        assert filename is not None
        return Logger(filename=filename, parent=self)

    def time(self):
        self.print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())))

    def timer(self, title="operation"):
        return LogTimer(self, title)


class DummyLogger(Logger):
    def __init__(self):
        super().__init__()

    def print(self, *args, **kwargs):
        pass

    def title(self, *args, **kwargs):
        pass

    def save(self, *args, **kwargs):
        pass

    def dump(self, *args, **kwargs):
        pass

    def trace(self, *args, **kwargs):
        pass

    def fork(self, *args, **kwargs):
        return self

    def time(self):
        pass

    def refresh(self):
        pass

    def getFilename(self):
        return ''

    def getDirectory(self):
        return ''


flushAllFiles(intervalSeconds=1)
terminal = Logger()
dummy = DummyLogger()
if __name__ == '__main__':
    logger = Logger()
    logger.title('title')
    logger.print('helloa')
    sub = logger.fork('sub')
    sub.trace('hello')
# sub.refresh()
