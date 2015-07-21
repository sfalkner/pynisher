The pynisher is a little module intended to limit a functions resources. It starts a new process, sets the desired limits, and executes the function inside it. In the end, it returns the function return value. If, for any reason, the function call is not successful, None is returned.

Currently, the total memory usage(*), the wall clock time, the cpu time and the number of processes can be limited.


(*) As the subprocess also includes the Python interpreter, the actual memory available to your function is less than the specified value.


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

        # a more explicit usage

        def my_other_function(t):
	        time.sleep(t)
	        return(t)

        # explicitly create a new function without wrapping the original everytime
        my_wrapped_function = pynisher.enforce_limits(wall_time_in_s=3)(my_other_function)

        for t in range(5):
	        print(my_wrapped_function(t))
