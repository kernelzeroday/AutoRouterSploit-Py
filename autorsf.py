import time
import pexpect
import threading
from queue import Queue
import sys
import logging
import uuid
import itertools
from colorama import Fore, Style


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RouterSploitWrapper:
    def __init__(self, num_threads=5, target_source='stdin'):
        self.num_threads = num_threads
        self.task_queue = Queue()
        self.target_source = target_source
        self.thread_colors = itertools.cycle([Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.MAGENTA, Fore.CYAN])

    def load_targets(self):
        if self.target_source == 'stdin':
            return [line.strip() for line in sys.stdin]
        else:
            return []

    def add_task(self, target):
        self.task_queue.put(target)

    def worker(self, thread_id):
        thread_logger = logging.getLogger(f'Thread-{thread_id}')
        color = next(self.thread_colors)
        while True:
            try:
                target = self.task_queue.get()
                process_uuid = str(uuid.uuid4())
                thread_logger.info(f"{color}{process_uuid}: Starting exploit on target: {target}{Style.RESET_ALL}")
                self.run_exploit(target, thread_logger, process_uuid, color)
                self.task_queue.task_done()
            except Exception as e:
                thread_logger.error(f"{color}{process_uuid}: Exception in thread: {e}{Style.RESET_ALL}")

    def run_exploit(self, target, thread_logger, process_uuid, color):
        child = pexpect.spawn('rsf.py', encoding='utf-8', timeout=None)

        commands = ['use scanners/autopwn', f'set target {target}', 'run']  # Add any other commands you need

        for cmd in commands:
            thread_logger.info(f"{color}{process_uuid}: Sending command: {cmd}{Style.RESET_ALL}")
            child.sendline(cmd)
            time.sleep(1)  # Small delay to allow command processing, adjust as needed

        # Stream output without matching
        try:
            while True:
                line = child.readline()
                if line:
                    thread_logger.info(f"{color}{process_uuid}: {line.strip()}{Style.RESET_ALL}")
                else:
                    break
        except pexpect.EOF:
            thread_logger.info(f"{color}{process_uuid}: End of file reached.{Style.RESET_ALL}")
        except Exception as e:
            thread_logger.error(f"{color}{process_uuid}: Exception while reading output: {e}{Style.RESET_ALL}")

        child.close()

    def start(self):
        threads = []
        for i in range(self.num_threads):
            t = threading.Thread(target=self.worker, args=(i,))
            t.daemon = True
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

# Usage
wrapper = RouterSploitWrapper()
targets = wrapper.load_targets()
for target in targets:
    wrapper.add_task(target)
wrapper.start()
