from crucio.data_types import Grammar
from crucio.utils.key_listen import register_key, stop_listening, start_listening
from crucio.utils.statistics import showStatistics
from crucio.utils.frame import print_main_thread_stack


def on_f():
    print_main_thread_stack()


def on_s():
    showStatistics()


def on_i():
    print('Status:')
    print('Infer progress:',RuntimeInfo.current,'/',RuntimeInfo.total,'=',
          f'{int(RuntimeInfo.current/RuntimeInfo.total*100)}%')

def on_g():
    if RuntimeInfo.grammar is not None:
        from consts import SEP
        print(SEP)
        print(RuntimeInfo.grammar)
        print('Nt=',len(RuntimeInfo.grammar.getNts()))
        print(SEP)

def quit_program():
    print("exiting...")
    stop_listening()


class RuntimeInfo:
    total: int = 0
    current: int = 0
    grammar:Grammar = None


def initial_monitor():
    register_key('f', on_f)
    register_key('s', on_s)
    register_key('i', on_i)
    register_key('g', on_g)
    register_key('q', quit_program)

    start_listening()
