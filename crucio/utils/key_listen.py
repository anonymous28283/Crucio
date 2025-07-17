import sys
import termios
import tty
import select
import threading

class KeyListener:
    def __init__(self):
        self.handlers = {}
        self.running = False
        self.thread = None
        self.lock = threading.Lock()

    def register_key(self, key, func):
        with self.lock:
            self.handlers[key] = func

    def _read_key(self):

        fd = sys.stdin.fileno()
        import termios
        attrs = termios.tcgetattr(fd)
        attrs[3] |= termios.ECHO  # 3 = lflags
        termios.tcsetattr(fd, termios.TCSADRAIN, attrs)
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setcbreak(fd)
            if select.select([sys.stdin], [], [], 0.1)[0]:
                ch = sys.stdin.read(1)
                if ch == '\x1b' and select.select([sys.stdin], [], [], 0.01)[0]:
                    seq = sys.stdin.read(2)
                    return f'ESC_{seq}'
                return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return None
    def _listen_loop(self):
        while self.running:
            key = self._read_key()
            if key:
                with self.lock:
                    func = self.handlers.get(key)
                if func:
                    try:
                        func()
                    except Exception as e:
                        print(f"[error] process key {repr(key)} error: {e}")

    def start(self):
        if self.thread and self.thread.is_alive():
            return
        self.running = True
        self.thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False

    def wait(self):
        if self.thread and self.thread.is_alive():
            self.thread.join()

_listener = KeyListener()

def register_key(key, func):
    _listener.register_key(key, func)

def start_listening():
    _listener.start()

def stop_listening():
    _listener.stop()

def wait_for_listener():
    _listener.wait()