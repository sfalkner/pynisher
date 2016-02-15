#! /bin/python
import resource
import signal
# supports spawning processes using an API
import multiprocessing
# using operating system dependent functionality
import os
import sys

import psutil

class CpuTimeoutException (Exception): pass
class TimeoutException (Exception): pass
class MemorylimitException (Exception): pass
class SubprocessException (Exception): pass
class AnythingException (Exception): pass

# create the function the subprocess can execute
def subprocess_func(func, parent_pipe, pipe, logger, mem_in_mb, cpu_time_limit_in_s, wall_time_limit_in_s, num_procs, *args, **kwargs):

	parent_pipe.close()

	# simple signal handler to catch the signals for time limits
	def handler(signum, frame):
		# logs message with level debug on this logger 
		logger.debug("signal handler: %i"%signum)
		if (signum == signal.SIGXCPU):
			# when process reaches soft limit --> a SIGXCPU signal is sent (it normally terminats the process)
			#raise(CpuTimeoutException)
			pipe.send((None, CpuTimeoutException))
			pipe.close()
		elif (signum == signal.SIGALRM):
			# SIGALRM is sent to process when the specified time limit to an alarm function elapses (when real or clock time elapses)
			logger.debug("timeout")
			raise(TimeoutException)
		raise AnythingException


	# catching all signals at this point turned out to interfer with the subprocess (e.g. using ROS)
	signal.signal(signal.SIGALRM, handler)
	signal.signal(signal.SIGXCPU, handler)
	signal.signal(signal.SIGQUIT, handler)

	"""
	for i in [x for x in dir(signal) if x.startswith("SIG")]:
		try:
			signum = getattr(signal,i)
			print("register {}, {}".format(signum, i))
			signal.signal(signum, handler)
		except:
			print("Skipping %s"%i)
	"""

	# set the memory limit
	if mem_in_mb is not None:
		# byte --> megabyte
		mem_in_b = mem_in_mb*1024*1024
		# the maximum area (in bytes) of address space which may be taken by the process.
		resource.setrlimit(resource.RLIMIT_AS, (mem_in_b, mem_in_b))

	# for now: don't allow the function to spawn subprocesses itself.
	#resource.setrlimit(resource.RLIMIT_NPROC, (1, 1))
	# Turns out, this is quite restrictive, so we don't use this option by default
	if num_procs is not None:
		resource.setrlimit(resource.RLIMIT_NPROC, (num_procs, num_procs))


	# schedule an alarm in specified number of seconds
	if wall_time_limit_in_s is not None:
		signal.alarm(wall_time_limit_in_s)
	
	if cpu_time_limit_in_s is not None:
		resource.setrlimit(resource.RLIMIT_CPU, (cpu_time_limit_in_s,cpu_time_limit_in_s))

	# the actual function call
	try:
		logger.debug("call function")
		return_value = ((func(*args, **kwargs), 0))
		logger.debug(return_value)
	except MemoryError:
		logger.debug("1")
		return_value = (None, MemorylimitException)

	except OSError as e:
		logger.debug("2"*20)
		if (e.errno == 11):
			return_value = (None, SubprocessException)
		else:
			return_value = (None, AnyithingException)

	except CpuTimeoutException:
		logger.debug("3"*20)
		return_value = (None, CpuTimeoutException)

	except TimeoutException:
		logger.debug("4"*20)
		return_value = (None, TimeoutException)

	except AnythingException as e:
		logger.debug("5"*20)
		return_value = (None, AnythingException)
	except:
		raise
		logger.debug("Some wired exception occured!")
		
	finally:
		logger.debug("6"*20)
		if True:
			logger.debug("="*30)
			logger.debug(return_value)
			logger.debug("="*30)
			
			pipe.send(return_value)
			pipe.close()
			# recursively kill all children
			p = psutil.Process()
			for child in p.children(recursive=True):
				child.kill()


			
		#except:
		#	# this part should only fail if the parent process is alread dead, so there is not much to do anymore :)
		#	pass

"""
def enforce_limits (mem_in_mb=None, cpu_time_in_s=None, wall_time_in_s=None, num_processes=None, grace_period_in_s = None):

	logger = multiprocessing.get_logger()
	
	if mem_in_mb is not None:
		logger.debug("restricting your function to {} mb memory.".format(mem_in_mb))
	if cpu_time_in_s is not None:
		logger.debug("restricting your function to {} seconds cpu time.".format(cpu_time_in_s))
	if wall_time_in_s is not None:
		logger.debug("restricting your function to {} seconds wall time.".format(wall_time_in_s))
	if num_processes is not None:
		logger.debug("restricting your function to {} threads/processes.".format(num_processes))
	if grace_period_in_s is None:
		grace_period_in_s = 0
	
	def actual_decorator(func):
		def wrapped_function(*args, **kwargs):
			logger = multiprocessing.get_logger()
			
			# create a pipe to retrieve the return value
			parent_conn, child_conn = multiprocessing.Pipe()

			# create and start the process
			subproc = multiprocessing.Process(target=subprocess_func, name="pynisher function call", args = (func, child_conn,mem_in_mb, cpu_time_in_s, wall_time_in_s, num_processes) + args ,kwargs = kwargs)
			logger.debug("Your function is called now.")

			return_value = None

			# start the process
			subproc.start()
			child_conn.close()

			try:
				# read the return value
				if parent_conn.poll(wall_time_in_s):
					return_value = parent_conn.recv()
				else:
					subproc.terminate()
				
			except EOFError:    # Don't see that in the unit tests :(
				logger.debug("Your function call closed the pipe prematurely -> None will be returned")
				return_value = None
			except:
				raise
			finally:
				# don't leave zombies behind
				subproc.join()
				return (return_value); 
		return wrapped_function
	return actual_decorator
"""

class enforce_limits (object):
	def __init__(self, mem_in_mb=None, cpu_time_in_s=None, wall_time_in_s=None, num_processes=None, grace_period_in_s = None, logger = None):
		self.mem_in_mb = mem_in_mb
		self.cpu_time_in_s = cpu_time_in_s
		self.num_processes = num_processes
		self.wall_time_in_s = wall_time_in_s
		self.grace_period_in_s = 0 if grace_period_in_s is None else grace_period_in_s
		self.logger = logger if logger is not None else multiprocessing.get_logger()
		
		if self.mem_in_mb is not None:
			self.logger.debug("Restricting your function to {} mb memory.".format(self.mem_in_mb))
		if self.cpu_time_in_s is not None:
			self.logger.debug("Restricting your function to {} seconds cpu time.".format(self.cpu_time_in_s))
		if self.wall_time_in_s is not None:
			self.logger.debug("Restricting your function to {} seconds wall time.".format(self.wall_time_in_s))
		if self.num_processes is not None:
			self.logger.debug("Restricting your function to {} threads/processes.".format(self.num_processes))
		if self.grace_period_in_s is not None:
			self.logger.debug("Allowing a grace period of {} seconds.".format(self.grace_period_in_s))

		
	def __call__ (self, func):
		
		class function_wrapper(object):
			def __init__(self2, func):
				self2.func = func
				self2.result = None
				self2.exit_status = None
			
			def __call__(self2, *args, **kwargs):
			
				# create a pipe to retrieve the return value
				parent_conn, child_conn = multiprocessing.Pipe()

				# create and start the process
				subproc = multiprocessing.Process(target=subprocess_func, name="pynisher function call", args = (self2.func, parent_conn, child_conn, self.logger, self.mem_in_mb, self.cpu_time_in_s, self.wall_time_in_s, self.num_processes) + args ,kwargs = kwargs)
				self.logger.debug("Function called with argumen: {}, {}".format(args, kwargs))


				# start the process
				subproc.start()
				child_conn.close()

				try:
					# read the return value
					print("waiting for response")
					if (self.wall_time_in_s is not None):
						if parent_conn.poll(self.wall_time_in_s+self.grace_period_in_s):
							self2.result, self2.exit_status = parent_conn.recv()
						else:
							subproc.terminate()
							self2.exit_status = TimeoutException
							
					else:
						print("no wall time limit, so wait forever")
						self2.result, self2.exit_status = parent_conn.recv()

					print("="*30)
					print(self2.result, self2.exit_status)
					print("="*30)
				
				except EOFError:    # Don't see that in the unit tests :(
					self.logger.debug("Your function call closed the pipe prematurely -> Function was most likely stuck in some extension code that did not terminate properly.")
					
					print(vars(subproc))
					
					self2.resources = resource.getrusage(resource.RUSAGE_CHILDREN)
					print(self2.resources)
					print(resource.getrusage(resource.RUSAGE_SELF))
					
					self2.exit_status = AnythingException
				except:
					self.logger.debug("Something else went wrong, sorry.")
				finally:
					print('fw:', self2.exit_status)
					self2.exit_status = 5 if self2.exit_status is None else self2.exit_status
					# don't leave zombies behind
					subproc.join()
				return (self2.result); 
		
		
		return (function_wrapper(func))
	

