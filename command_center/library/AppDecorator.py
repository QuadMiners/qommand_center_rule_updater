#!/usr/bin/env python
# -*- coding: utf-8 -*-
import asyncio
import timeit
import functools
import logging
from datetime import datetime, timedelta

from termcolor import cprint

from command_center.library.database import DBException

logger = logging.getLogger(__name__)


def async_decorator(loop=None):
    """Wrap an async test in a run_until_complete for the event loop."""
    loop = loop or asyncio.get_event_loop()

    def _outer_async_wrapper(func):
        """Closure for capturing the configurable loop."""
        @functools.wraps(func)
        def _inner_async_wrapper(*args, **kwargs):
            print("Decorator", func)
            return loop.run_until_complete(func(*args, **kwargs))

        return _inner_async_wrapper

    return _outer_async_wrapper


class DBExceptionDecorator:
    def __init__(self, func):
        self.func = func

    def __call__(self, *args, **kwargs):
        ret = None
        try:
            ret = self.func(*args, **kwargs)
        except DBException as e:
            logger.error("Func({0}) : DBError  {1} \n {2}".format(self.func.__name__, e, e.query))
        except Exception as e:
            logger.error("Func({0}) : Exception  {1}".format(self.func.__name__, e))
        return ret


def database_exception(func):
    """
        DB 에러가날때 에러처리 구문 
    """
    def decorated(*args, **kwargs):
        ret = None
        try:
            ret = func(*args, **kwargs)
        except DBException as dbe:
            logger.error("Func({0}): DBError  {1}".format(func.__name__, dbe))
            cprint("Func : [{0}] DBError : {1}  : {2}".format(func.__name__, dbe, dbe.query), 'red')
            raise dbe
        except Exception as e:
            logger.error("Func({0}) : Exception  {1}".format(func.__name__, e))
            raise e
        return ret
    return decorated


def timed_cache(**timed_cache_kwargs):
    """
        함수로 들어온 데이터가 일정시간이 지나면 Cache 에서 사라짐
    """
    def _wrapper(f):
        maxsize = timed_cache_kwargs.pop('maxsize', 128)
        typed = timed_cache_kwargs.pop('typed', False)
        update_delta = timedelta(**timed_cache_kwargs)
        next_update = datetime.utcnow() - update_delta
        f = functools.lru_cache(maxsize=maxsize, typed=False)(f)

        @functools.wraps(f)
        def _wrapped(*args, **kwargs):
            nonlocal next_update
            now = datetime.utcnow()
            if now >= next_update:
                f.cache_clear()
                next_update = now + update_delta
            return f(*args, **kwargs)

        return _wrapped

    return _wrapper


def timecheck(func):
    """
        함수 처리 시간 체크
    """

    @functools.wraps(func)
    def new_function(*args, **kwargs):
        start_time = timeit.default_timer()
        ret = func(*args, **kwargs)
        elapsed = timeit.default_timer() - start_time
        print('Function "{name}" took {time} seconds to complete.'.format(name=func.__name__, time=elapsed))
        logger.info('Function "{name}" took {time} seconds to complete.'.format(name=func.__name__, time=elapsed))
        return ret
    return new_function