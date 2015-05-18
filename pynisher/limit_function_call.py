#! /bin/python
import resource
import signal
import multiprocessing
import os

class abort_function (Exception): pass


# create the function the subprocess can execute
def subprocess_func(func, pipe, mem_in_mb, cpu_time_limit_in_s, wall_time_limit_in_s, num_procs, *args, **kwargs):

    logger = multiprocessing.get_logger()
    os.setpgrp()

    # simple signal handler to catch the signals for time limits
    def handler(signum, frame):
        logger.debug("received signal number %i. Exiting uncracefully."%signum)
        
        if (signum == signal.SIGXCPU):
            logger.debug("CPU time exceeded, aborting!")
        elif (signum == signal.SIGALRM):
            logger.debug("Wallclock time exceeded, aborting!")
            
        raise abort_function
    
    signal.signal(signal.SIGALRM, handler)
    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGXCPU, handler)


    # set the memory limit
    if mem_in_mb is not None:
        mem_in_b = mem_in_mb*1024*1024
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
        # one could also limit the actual CPU time, but that does not help if the process hangs, e.g., in a dead-lock
        resource.setrlimit(resource.RLIMIT_CPU, (cpu_time_limit_in_s,cpu_time_limit_in_s))

    return_value=None;

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
            logger.warning('Something is going on here!')
            raise;

    except abort_function:
        logger.warning('Your function call was aborted. It probably took too long.')

    except:
        logger.debug('The call to your function did not return properly!\n%s\n%s', args, kwargs)
        raise;

    finally:
        pipe.send(return_value)
        pipe.close()

def enforce_limits (mem_in_mb=None, cpu_time_in_s=None, wall_time_in_s=None, num_processes=None, grace_period_in_s = 1):
    logger = multiprocessing.get_logger()
    
    if mem_in_mb is not None:
        logger.debug("restricting your function to {} mb memory.".format(mem_in_mb))
    if cpu_time_in_s is not None:
        logger.debug("restricting your function to {} seconds cpu time.".format(cpu_time_in_s))
    if wall_time_in_s is not None:
        logger.debug("restricting your function to {} seconds wall time.".format(wall_time_in_s))
    if num_processes is not None:
        logger.debug("restricting your function to {} threads/processes.".format(num_processes))


    
    def actual_decorator(func):

        def wrapped_function(*args, **kwargs):

            logger = multiprocessing.get_logger()
			
            # create a pipe to retrieve the return value
            parent_conn, child_conn = multiprocessing.Pipe()

            # create and start the process
            subproc = multiprocessing.Process(target=subprocess_func, name="Call to your function", args = (func, child_conn,mem_in_mb, cpu_time_in_s, wall_time_in_s, num_processes) + args ,kwargs = kwargs)
            logger.debug("Your function is called now.")
            subproc.start()
            
            if wall_time_in_s is not None:
                # politely wait for it to finish
                subproc.join(wall_time_in_s + grace_period_in_s)

                # if it is still alive, send sigterm
                if subproc.is_alive():
                    logger.debug("Your function took to long, killing it now.")
                    #subproc.terminate()
                    try:
                        os.killpg(os.getpgid(subproc.pid),15)
                    except:
                        logger.warning("Killing the function call failed. It probably finished already.")
                    finally:
                        subproc.join()
                        return(None)
            else:
                subproc.join()
            logger.debug("Your function has returned now with exit code %i."%subproc.exitcode)

            # if something went wrong, 
            if subproc.exitcode != 0:
                return(None)

            # return the function value from the pipe
            return (parent_conn.recv());

        return wrapped_function

    return actual_decorator

