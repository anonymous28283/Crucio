import time
from abc import abstractmethod
import subprocess
import tempfile

import lark

from crucio.oracle import StringOracle
from crucio.utils.statistics import counter, timer

import os

os.environ['CLASSPATH'] = './:/opt/homebrew/opt/antlr/antlr-4.13.2-complete.jar'


class CachedStringOracle(StringOracle):
    def __init__(self):
        self.calls = 0
        self.call_time = 0
        self.cache = {}

    def parse(self, sentence: str) -> bool:
        if sentence in self.cache:
            return self.cache[sentence]
        self.calls += 1
        start = time.time()
        ans = self._parse(sentence)
        self.call_time += time.time() - start
        self.cache[sentence] = ans
        return ans

    @abstractmethod
    def _parse(self, sentence: str) -> bool:
        pass

    def record(self, oracle: "CachedStringOracle"):
        self.calls += oracle.calls
        self.call_time += oracle.call_time


class ExternalOracle(CachedStringOracle):
    def __init__(self, command):
        """
        `command` is a string representing the oracle command, i.e. `command` = "readpng"
        in the oracle call:
            $ readpng <MY_FILE>
        """
        super().__init__()
        self.command = command

    def _parse(self, sentence: str) -> bool:
        return self.__parse_internal(sentence)

    def __parse_internal(self, string):
        """
        Does the work of calling the subprocess.
        """
        # print(string)
        FNULL = open(os.devnull, 'w')
        f = tempfile.NamedTemporaryFile()
        f.write(bytes(string, 'utf-8'))
        f_name = f.name
        f.flush()
        try:
            # With check = True, throws a CalledProcessError if the exit code is non-zero
            command = ''
            op1 = self.command
            if self.command.endswith('.sh'):
                command = 'bash'
            elif self.command.endswith('.py'):
                command = 'python3'
            elif self.command.startswith('java'):
                command = 'java'
                op1 = self.command.split(' ')[1]
            commands = [command, op1, f_name]
            if commands[0] == '':
                commands = commands[1:]
            subprocess.run(commands, stdout=FNULL, stderr=FNULL, check=True, timeout=10)
            f.close()
            FNULL.close()
            return True
        except subprocess.CalledProcessError as e:
            f.close()
            FNULL.close()
            return False
        except subprocess.TimeoutExpired as e:
            print(f"Caused timeout: {string}")
            f.close()
            FNULL.close()
            return False


class LarkOracle(CachedStringOracle):
    @timer('LarkOracle build')
    def __init__(self, *args, **kwargs) -> None:
        super().__init__()
        self.__parser = lark.Lark(*args, **kwargs)

    @counter('LarkOracle')
    @timer('LarkOracle')
    def _parse(self, sentence) -> bool:
        try:
            self.__parser.parse(sentence)
            return True
        except:
            return False
