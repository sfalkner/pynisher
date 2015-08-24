#! /bin/python
import resource
import signal
# supports spawning processes using an API
import multiprocessing
# using operating system dependent functionality
import os
import sys

import psutil

class abort_function (Exception): pass

# create the function the subprocess can execute
def subprocess_func(func, pipe, mem_in_mb, cpu_time_limit_in_s, wall_time_limit_in_s, num_procs, *args, **kwargs):
    # returning logger used by multiprocessing (a new one is created)
    logger = multiprocessing.get_logger()

    # simple signal handler to catch the signals for time limits
    def handler(signum, frame):
        # logs message with level debug on this logger 
        logger = multiprocessing.get_logger()
        logger.debug("received signal number %i. Exiting uncracefully."%signum)
        
        if (signum == signal.SIGXCPU):
            # when process reaches soft limit --> a SIGXCPU signal is sent (it normally terminats the process)
            logger.warning("CPU time exceeded, aborting!")
        elif (signum == signal.SIGALRM):
            # SIGALRM is sent to process when the specified time limit to an alarm function elapses (when real or clock time elapses)
            logger.warning("Wallclock time exceeded, aborting!")
        raise abort_function


    # catching all signals at this point turned out to interfer with the subprocess (e.g. using ROS)
    signal.signal(signal.SIGALRM, handler)
    signal.signal(signal.SIGXCPU, handler)

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

    return_value = None
    # the actual function call
    try:
        logger.debug('call to your function')
        return_value = func(*args, **kwargs)
        logger.debug('function returned %s'%str(return_value))

    except MemoryError:
        logger.warning("Function call with the arguments {}, {} has exceeded the memory limit!".format(args,kwargs))

    except OSError as e:
        if (e.errno == 11):
            logger.warning("Your function tries to spawn too many subprocesses/threads.")
        else:
            logger.debug('Something is going on here!')
            raise;

    except abort_function:
        return_value = None
        logger.warning('Your function call was aborted.')

    except:
        logger.debug('The call to your function did not return properly!\n%s\n%s', args, kwargs)
        raise;
    finally:
        try:
            pipe.send(return_value)
            pipe.close()
            # recursively kill all children
            p = psutil.Process()
            for child in p.children(recursive=True):
                child.kill()
        except:
            pass


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
            global return_value
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
                return_value = parent_conn.recv()
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
