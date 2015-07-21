import pynisher
import time

# using it as a decorator for every call to this function
@pynisher.enforce_limits(wall_time_in_s=2)
def my_function (t):
	time.sleep(t)
	return(t)

for t in range(5):
	print(my_function(t))




def my_other_function(t):
	time.sleep(t)
	return(t)

# explicitly create a new function without wrapping the original everytime
my_wrapped_function = pynisher.enforce_limits(wall_time_in_s=3)(my_other_function)

for t in range(5):
	print(my_wrapped_function(t))
