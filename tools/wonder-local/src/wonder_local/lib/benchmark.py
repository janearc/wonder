from pydantic import BaseModel, Field
import psutil
import time

class Benchmark(BaseModel):
    label: str = "Benchmark"
    input_tokens: int = -1
    output_tokens: int = 0
    token_throughput: float = 0.0
    start_time: float = 0.0
    end_time: float = 0.0
    cpu_start: psutil._common.pcputimes = Field(default=None, exclude=True)
    cpu_end: psutil._common.pcputimes = Field(default=None, exclude=True)
    proc: psutil.Process = Field(default_factory=psutil.Process, exclude=True)

    model_config = {
        "arbitrary_types_allowed": True
    }

    def start(self):
        self.start_time = time.perf_counter()
        self.cpu_start = self.proc.cpu_times()

    def stop(self):
        self.end_time = time.perf_counter()
        self.cpu_end = self.proc.cpu_times()
        elapsed = self.end_time - self.start_time
        if elapsed > 0:
            self.token_throughput = self.output_tokens / elapsed

    def report(self):
        elapsed = self.end_time - self.start_time
        cpu_time = (self.cpu_end.user + self.cpu_end.system) - (
            self.cpu_start.user + self.cpu_start.system
        )
        mem_info = self.proc.memory_info()

        print(f"\n📊 {self.label}:")
        print(f"- Elapsed wall time: {elapsed:.2f}s")
        print(f"- CPU time (user+system): {cpu_time:.2f}s")
        print(f"- Memory usage: {mem_info.rss / (1024 ** 2):.2f} MB")

        if self.output_tokens > 0:
            print(f"- Token throughput: {self.token_throughput:.2f} tokens/sec")
            print(f"- Input: {self.input_tokens} tokens, Output: {self.output_tokens} tokens")
