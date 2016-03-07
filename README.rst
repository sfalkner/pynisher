The pynisher is a little module intended to limit a functions resources.
It starts a new process, sets the desired limits, and executes the
function inside it. In the end, it returns the function return value.
If, for any reason, the function call is not successful, None is returned.

Currently, the total memory usage(*), wall and cpu time, and the number of subprocesses can be limited.


(*) As the subprocess also includes the Python interpreter, the actual memory available to your function is less than the specified value.

To show the basic usage, consider the following script

.. code-block:: python

        import pynisher
        import time

        # using it as a decorator for every call to this function
        @pynisher.enforce_limits(wall_time_in_s=2)
        def my_function (t):
        	time.sleep(t)
        	return(t)

        for t in range(5):
        	print(my_function(t))

The full list of argments to enforce_limits reads: 

.. code-block:: python

		pynisher.enforce_limits(mem_in_mb=None, cpu_time_in_s=None,\
					wall_time_in_s=None, num_processes=None,\
					grace_period_in_s = None, logger = None)

The first four are actual constraints on the memory, the CPU time, the wall time, and the
number of subprocesses of the function. All values should be integers or None, which means
no restriction.

The grace period allows the function to properly end. More technically, the subprocess receives
a SIGXCPU/SIGALARM signal if the CPU/wall clock limit is reached. After the grace period a
SIGKILL is send terminating the process immediately. Without a grace period, pynisher might
not be able to correctly determine the cause of the shutdown, as the subprocess might die without
any notice (more on that below).

The logger is used to display additional information about the status of the pynisher module
(mostly debug level). This might come in handy while debugging.

If you need to know what happend to the function call or why it was aborted,
you can use the object returned from pynisher.enforce_limits. Consider this
slight variation of the above example:

.. code-block:: python

		import pynisher
		import time

		def my_function (t):
			time.sleep(t)
			return(t)

		for t in range(5):
			obj = pynisher.enforce_limits(wall_time_in_s=2)(my_function)
			result = obj(t)
			print(result, obj.result, obj.exit_status, obj.wall_clock_time)
		
		# see all the available information
		print(vars(f))

The object ```obj``` can be used as the original function. After calling it, it contains
the actual result, but also an indicator of what happend. The ```exit_status``` attribute
is either zero (function returned properly) or one of the following exceptions:

.. code-block:: python

		pynisher.CpuTimeoutException	# CPU time limit was reached
		pynisher.TimeoutException	# Wall clock time limit exceeded
		pynisher.MemorylimitException	# function hit the memory constraint
		pynisher.SubprocessException	# function tried to spawn too many subprocesses
		pynisher.AnythingException	# Something else went wrong, e.g., your function received a signal and just died.

Here, the above issue about the grace period becomes interesting. Without it, it is likely that
a AnythingException is returned where a Cpu-/TimeoutException would be appropriate.
