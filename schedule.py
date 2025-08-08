"""Minimal schedule stub used for tests."""

_jobs = []

class Job:
    def __init__(self, interval):
        self.interval = interval
        self.unit = 'seconds'
        self.func = None
        self.args = ()
        self.kwargs = {}

    def seconds(self):
        self.unit = 'seconds'
        return self

    def minutes(self):
        self.unit = 'minutes'
        return self

    def do(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs
        _jobs.append(self)
        return self


def every(interval):
    return Job(interval)


def run_pending():
    for job in list(_jobs):
        job.func(*job.args, **job.kwargs)
        _jobs.remove(job)
