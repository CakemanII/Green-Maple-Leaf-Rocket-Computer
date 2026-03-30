from typing import TypedDict
import threading
import time
import sys

class Queue:
    def __init__(self, operations_per_second: float, queue_processor: callable, queue_name: str = "(Unnamed)", print_length_of_queue: bool = False, enable_replacing_queue_objects: bool = False):
        self._queue: list[any] = []
        self._queue_name = queue_name
        self._queue_processor = queue_processor
        self._active = False
        self._print_length_of_queue = print_length_of_queue
        self._enable_replacing_queue_objects = enable_replacing_queue_objects
        
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
                queue_object = self._queue.pop(0)[1]
                sys.stdout.flush()
                self._queue_processor(queue_object)
                sys.stdout.flush()
            else:
                # No data to process, just wait for the next interval
                pass

            # Optionally print the length of the queue for debugging
            if self._print_length_of_queue:
                print(f"Queue {self._queue_name} Remaining Length: {len(self._queue)}")
                sys.stdout.flush()

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

    def add_to_queue(self, queue_object: tuple[str, any]):
        # Check the queue
        if self._enable_replacing_queue_objects:
            # If an object with the same label already exists, replace it instead of adding a new one
            for i, existing_object in enumerate(self._queue):
                if i == 0: continue  # Skip the currently processing object
                if existing_object[0] == queue_object[0]:  # Assuming the first element is a label or identifier
                    self._queue[i] = queue_object  # Replace the existing object
                    return

        # Add to queue as normal
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
    