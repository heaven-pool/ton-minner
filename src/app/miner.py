from datetime import datetime
import queue
import random
import threading
import time
import sys
import signal
from loguru import logger
import config
import model
import sender


class Worker(threading.Thread):
    def __init__(self, queue, id):
        threading.Thread.__init__(self)
        self.queue = queue
        self.id = id

    def run(self):
        while True:
            if not self.queue.empty():
                job = self.queue.get()
                logger.info(f"Worker {self.id}: {job.seed} / {job.complexity} / {job.iterations} / {job.giver_address}")
                time.sleep(random.randint(15, 20))
            else:
                logger.info(f"Worker Idle {self.id}")
            time.sleep(0.1)


class JobManager(threading.Thread):
    def __init__(self, miner, queue, job_expiration):
        threading.Thread.__init__(self)
        self.miner = miner
        self.queue = queue
        self.job_expiration = job_expiration

    def run(self):
        ts = datetime.now()
        while True:
            if (datetime.now()-ts).total_seconds() > self.job_expiration:
                while not self.queue.empty():
                    self.queue.get()
                for i in range(len(self.miner.devices)):
                    self.queue.put(sender.job(self.miner))
                ts = datetime.now()
            elif self.queue.qsize() < len(self.miner.devices):
                for i in range(self.queue.qsize(), len(self.miner.devices)):
                    self.queue.put(sender.job(self.miner))
                ts = datetime.now()
            logger.debug(f"Job in queue: {self.queue.qsize()}")
            time.sleep(1)


def create_job_manager(miner: model.MinerSchema, queue: queue.Queue, job_expiration: int):
    job_mgr = JobManager(miner, queue, job_expiration)
    job_mgr.setDaemon(True)
    job_mgr.start()
    return job_mgr


def create_worker(miner: model.MinerSchema, queue: queue.Queue):
    worker_pool = []

    for i in range(len(miner.devices)):
        worker = Worker(queue, i)
        worker.setDaemon(True)
        worker.start()
        worker_pool.append(worker)

    return worker_pool


class Graceful:
    rip = False

    def __init__(self):
        signal.signal(signal.SIGHUP, self.you_may_die)
        signal.signal(signal.SIGABRT, self.you_may_die)
        signal.signal(signal.SIGINT, self.you_may_die)
        signal.signal(signal.SIGQUIT, self.you_may_die)
        signal.signal(signal.SIGTERM, self.you_may_die)

    def you_may_die(self, *args):
        self.rip = True


if __name__ == "__main__":
    miner = config.init(sys.argv[1:])
    logger.debug(miner)

    task_queue = queue.Queue()
    job_manager = create_job_manager(miner, task_queue, 10)
    work_pools = create_worker(miner, task_queue)

    graceful = Graceful()
    while not graceful.rip:
        time.sleep(1)

    logger.info("Interrupted...")
    logger.info("Exiting...")
