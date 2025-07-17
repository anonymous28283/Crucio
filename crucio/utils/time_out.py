import multiprocessing

multiprocessing.set_start_method("fork")

import time
import functools
import traceback


def _target_wrapper(func, args, kwargs, queue):
    try:
        result = func(*args, **kwargs)
        queue.put(("ok", result))
    except Exception as e:
        queue.put(("err", traceback.format_exc()))


def timeout(seconds, timeout_return=None, raise_exception=False):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            queue = multiprocessing.Queue()
            process = multiprocessing.Process(target=_target_wrapper, args=(func, args, kwargs, queue))
            process.start()
            try:
                status, result = queue.get(timeout=seconds)
                process.terminate()
                process.join()
                if status == "ok":
                    return result
                elif status == "err":
                    if raise_exception:
                        raise RuntimeError("Function raised exception:\n" + result)
                    else:
                        return timeout_return
            except multiprocessing.queues.Empty:
                process.terminate()
                process.join()
                return timeout_return
        return wrapper
    return decorator
