import os
from pathlib import Path

from colored import bg, attr


def get_project_root() -> str:
    current_path = Path(__file__).resolve()

    while current_path != current_path.parent:
        if (current_path / 'readme.md').exists():
            return str(current_path) + '/'
        current_path = current_path.parent

    return str(current_path) + '/'


SEP = bg('yellow') + '##############################' + attr('reset')
# Project Path
projectPath = get_project_root()

# SimpleLarkGrammar Path
simpleLarkGrammar = projectPath + 'SimpleLark.lark'

def getTempPath():
    os.makedirs(projectPath+'runtime/temp',exist_ok=True)
    return projectPath+'runtime/temp'


# Benchmark Path
benchmarkPath = projectPath + 'benchmark/'

# log Path
logPath = projectPath + 'Logs/'


def getTrainPath(name, level='r1'):
    return benchmarkPath + name + '/' + name + '-' + 'train-' + level
