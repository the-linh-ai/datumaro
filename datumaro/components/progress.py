# Copyright (C) 2021 Intel Corporation
#
# SPDX-License-Identifier: MIT

# Copyright (C) 2021 Intel Corporation
#
# SPDX-License-Identifier: MIT

from contextlib import contextmanager
from functools import wraps
from typing import Optional
import threading

class ProgressBar:
    _thread_locals = threading.local()

    def __init__(self, total: int = 100, name: str = None,
            parent: Optional['ProgressBar'] = None):
        self._current = 0
        self._total = total
        self._name = name
        self._status = ''
        self._parent = parent

    def close(self):
        self.__exit__(None, None, None)

    def __enter__(self) -> 'ProgressBar':
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        pass

    @classmethod
    def current(cls) -> 'ProgressBar':
        return cls._thread_locals.current

    @contextmanager
    def as_current(self):
        previous = getattr(self._thread_locals, 'current', None)
        self._thread_locals.current = self
        try:
            yield
        finally:
            self._thread_locals.current = previous

def reports_progress(func):
    """
    A function decorator that allows to report current progress from
    the function:

        @reports_progress
        def compute():
            ...
    """

    @wraps(func)
    def wrapped_func(*args, **kwargs):
        with ProgressBar().as_current():
            return func(*args, **kwargs)

    return wrapped_func


@contextmanager
def progress_reporting(total: int = 100, name: Optional[str] = None,
        inherit: bool = True):
    """
    A context manager that initializes progress reporting context:

        with progress_reporting() as pbar:
            ...
    """

    old_pbar = ProgressBar().current()

    if inherit:
        pbar = old_pbar
    if not pbar:
        pbar = ProgressBar(total=total, name=name)

    with pbar.as_current():
        yield pbar



@reports_progress
def compute1():
    pass

@reports_progress
def compute2():
    pass

@reports_progress
def compute3():
    pass

@reports_progress
def compute4():
    pass

# Reports overall progress to the parent context
@reports_progress
def huge_compute1():
    report_progress(percent=10, message='step 1')

    compute1() # the function can report some progress

    report_progress(percent=70, message='step 2')

    compute2()

    # introduces a new progress bar bound to the parent
    # it will make at most 20% from the parent pbar
    with progress_reporting(total=20, name='step 3', inherit=True):
        # all the progress from is reported to the new pbar
        # it also translates % updates to the parent pbar transparently
        compute3()

    # introduces a new independent progress bar for own needs
    with progress_reporting(name='extra', inherit=False) as pbar:
        # all the progress from is reported to the new pbar
        compute4()
        do_stuff(pbar)

# Doesn't report overall progress to the parent context directly
def huge_compute2():
    compute1() # the function can report some progress. Which part it can fill?
    compute2() # the function can report some progress. Which part it can fill?

    # Potential solution 1:
    # - make a preprocessing step, analyze the number of inner calls decorated
    # Unfortunately, it is fragile, complex and unreliable

    # introduces a new progress bar bound to the parent, if it exists
    # it will make at most 50% from the parent pbar
    with progress_reporting(total=50, inherit=True):
        # all the progress from is reported to the new pbar
        # it also translates % updates to the parent pbar transparently
        huge_compute1()
