import sys
import threading
import traceback


def print_main_thread_stack():
    current_frames = sys._current_frames()

    for thread in threading.enumerate():
        if thread.name == "MainThread":
            main_thread_id = thread.ident
            break
    else:
        print("can not find main thread")
        return

    main_frame = current_frames.get(main_thread_id)
    if main_frame is None:
        print("can not find main frame。")
        return

    print("Main thread frame:")
    stack_lines = traceback.format_stack(main_frame)
    print("".join(stack_lines))


if __name__ == '__main__':
    print_main_thread_stack()
