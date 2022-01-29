# -*- coding: utf-8 -*-s
import platform
import uuid
from typing import List, Optional

from pydantic import BaseModel

# Miner -> create GPUWorker
# Job + GPUWorker -> JobResult


class JobSchema(BaseModel):
    job_id: int
    pool_wallet: str
    complexity: str
    seed: str
    iterations: str
    giver_address: str


class GPUWorkerSchema(BaseModel):
    job: Optional[JobSchema]
    gpu_id: int
    boost_factor: int = 16
    timeout: int = 900
    boc_name: Optional[str]
    miner_wallet: str
    computer_name: str
    computer_uuid: str

    def _cmd(self):
        cmd = f"-vv -g {self.gpu_id} -F {self.boost_factor} -t {self.timeout} -e {self.expire} "
        cmd += f"{self.pool_wallet} {self.job.seed} {self.job.complexity} {self.job.iterations} "
        cmd += f"{self.job.giver_address} {self.boc_name} "
        return cmd

    def _add_job(self, job: JobSchema):
        self.job = job


class MinerSchema(BaseModel):
    pool_url: str
    miner_wallet: str
    computer_name: str = platform.node()
    computer_uuid: str = hex(uuid.getnode())  # mac address
    devices: List[str]
    workers: Optional[GPUWorkerSchema]

    def _create_wokers(self):
        self.workers = [GPUWorkerSchema(gpu_id=device,
                                        miner_wallet=self.miner_wallet,
                                        computer_name=self.computer_name,
                                        computer_uuid=self.computer_uuid,)
                        for device in self.devices]


class JobResultSchema(BaseModel):
    job_id: int
    miner_wallet: str
    computer_name: str
    computer_uuid: str
    gpu_uuid: str
    hash_rate: int
    boc: str
