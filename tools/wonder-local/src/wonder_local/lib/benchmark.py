import time
from contextlib import contextmanager

import psutil


class Benchmark:
    def __init__(
        self, label: str = "Benchmark", input_tokens: int = 0, output_tokens: int = 0
    ):
        self.label = label
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.start_time = None
        self.end_time = None
        self.cpu_start = None
        self.cpu_end = None
        self.proc = psutil.Process()

    def start(self):
        self.start_time = time.perf_counter()
        self.cpu_start = self.proc.cpu_times()

    def stop(self):
        self.end_time = time.perf_counter()
        self.cpu_end = self.proc.cpu_times()
        self.report()

    def report(self):
        elapsed = self.end_time - self.start_time
        cpu_time = (self.cpu_end.user + self.cpu_end.system) - (
            self.cpu_start.user + self.cpu_start.system
        )
        mem_info = self.proc.memory_info()

        print(f"\n\U0001F4CA {self.label}:")
        print(f"- Elapsed wall time: {elapsed:.2f}s")
        print(f"- CPU time (user+system): {cpu_time:.2f}s")
        print(f"- Memory usage: {mem_info.rss / (1024 ** 2):.2f} MB")

        if self.output_tokens > 0:
            throughput = self.output_tokens / elapsed
            print(f"- Token throughput: {throughput:.2f} tokens/sec")
            print(
                f"- Input: {self.input_tokens} tokens, Output: {self.output_tokens} tokens"
            )
