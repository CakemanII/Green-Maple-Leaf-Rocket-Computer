from typing import TypedDict
import threading
import time
import sys

class Queue:
    def __init__(self, operations_per_second: float, queue_processor: callable, queue_name: str = "(Unnamed)"):
        self._queue: list[any] = []
        self._queue_name = queue_name
        self._queue_processor = queue_processor
        self._active = False
        
        self._thread: threading.Thread | None = None
        
        # Calculate the time interval between each process
        self._process_interval = 1.0 / operations_per_second

    def _main(self):
        """
        Main loop for processing data in the queue at a fixed rate.
        """
        start_process_time: float = 0.0
        while self._active:
            sys.stdout.flush()
            sys.stdout.flush()
            start_process_time = time.time()
            if len(self._queue) > 0:
                # Process the first item in the queue
                queue_object = self._queue.pop(0)
                sys.stdout.flush()
                self._queue_processor(queue_object)
                sys.stdout.flush()
            else:
                # No data to process, just wait for the next interval
                pass

            # Wait for the next processing interval
            time_remaining = self._process_interval - (time.time() - start_process_time)
            if time_remaining > 0:
                time.sleep(time_remaining)
    
    # region Queue Control Methods
    def _start_queue(self):
        """
        Start the data queue processing.
        """
        # Ensure we are not already running
        if self._thread is not None and self._thread.is_alive():
            print(f"Queue {self._queue_name} Already running")
            sys.stdout.flush()
            return

        # Set the queue to active BEFORE starting the thread to avoid race condition
        self._active = True

        # Run the main loop in a separate thread
        print(f"Queue {self._queue_name} Starting queue")
        sys.stdout.flush()
        self._thread = threading.Thread(target=self._main, daemon=True)
        self._thread.start()

    def _stop_queue(self):
        """
        Stop the data queue processing.
        """
        self._active = False
        if self._thread is not None and self._thread.is_alive():
            self._thread.join()
            self._thread = None
    # endregion

    def add_to_queue(self, queue_object: any):
        self._queue.append(queue_object)

    def set_queue_active(self, active: bool):
        """
        Set the data queue to active or inactive.
        When active, the main loop will process data from the queue at a fixed rate.
        """
        # Activate the queue
        if active and not self._active:
            print(f"Queue {self._queue_name} Activating queue")
            sys.stdout.flush()
            self._start_queue()

        # Deactivate the queue
        elif not active and self._active:
            print(f"Queue {self._queue_name} Deactivating queue")
            sys.stdout.flush()
            self._stop_queue()
    