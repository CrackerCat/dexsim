"""
超时处理
"""
import sys
import threading
import time


class KThread(threading.Thread):
    """A subclass of threading.Thread, with a kill() method.

    Come from:
    Kill a thread in Python:
    http://mail.python.org/pipermail/python-list/2004-May/260937.html
    """

    def __init__(self, *args, **kwargs):
        threading.Thread.__init__(self, *args, **kwargs)
        self.killed = False
        self.__run_backup = None

    def start(self):
        """
        Start the thread.
        """
        self.__run_backup = self.run
        self.run = self.__run      # Force the Thread to install our trace.
        threading.Thread.start(self)

    def __run(self):
        """
        Hacked run function, which installs the trace.
        """
        sys.settrace(self.globaltrace)
        self.__run_backup()
        self.run = self.__run_backup

    def globaltrace(self, frame, why, arg):
        """
        全局
        """
        if why == 'call':
            return self.localtrace
        return None

    def localtrace(self, frame, why, arg):
        """
        本地
        """
        if self.killed:
            if why == 'line':
                raise SystemExit()
        return self.localtrace

    def kill(self):
        """
        是否已杀死
        """
        self.killed = True


class TIMEOUT_EXCEPTION(Exception):
    """
    超时异常
    """
    pass


def timeout(seconds):
    """
    超时装饰器，指定超时时间

    若被装饰的方法在指定的时间内未返回，则抛出Timeout异常
    """
    def timeout_decorator(func):
        """
        超时装饰器
        """
        def _new_func(oldfunc, result, oldfunc_args, oldfunc_kwargs):
            result.append(oldfunc(*oldfunc_args, **oldfunc_kwargs))

        def _(*args, **kwargs):
            result = []
            new_kwargs = {
                # create new args for _new_func, because we want to get the
                # func return val to result list
                'oldfunc': func,
                'result': result,
                'oldfunc_args': args,
                'oldfunc_kwargs': kwargs
            }

            thd = KThread(target=_new_func, args=(), kwargs=new_kwargs)
            thd.start()
            thd.join(seconds)
            alive = thd.isAlive()
            thd.kill()  # kill the child thread

            if alive:
                raise TIMEOUT_EXCEPTION(
                    'function run too long, timeout %d seconds.' % seconds)
            else:
                if result:
                    return result[0]
                return result

        _.__name__ = func.__name__
        _.__doc__ = func.__doc__
        return _

    return timeout_decorator


@timeout(5)
def test_timeout(seconds, text):
    """
    测试用例
    """
    print('start', seconds, text)
    time.sleep(seconds)
    print('finish', seconds, text)
    return seconds


if __name__ == '__main__':
    for sec in range(1, 10):
        try:
            print('*' * 20)
            print(test_timeout(sec, 'TIMEOUT!'))
        except TIMEOUT_EXCEPTION as e:
            print(e)
