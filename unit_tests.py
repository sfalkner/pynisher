#! /bin/python
import time
import multiprocessing
import unittest
import os
import sys
import signal
import logging

import pynisher

all_tests=1


# TODO: get rid of numpy just to create some data of fixed size!
#       add tests for cpu usage
#       add test for num_processes
#       add test with crash_unexpectedly to see what happens if the function call dies!

def simulate_work(size_in_mb, wall_time_in_s, num_processes):
    # allocate memory (size_in_mb) with an array
    # note the actual size in memory of this process is a little bit larger
    A = [42.]*((1024*size_in_mb)//8);

    # try to spawn new processes
    if (num_processes > 0):
        # data parallelism
        multiprocessing.Pool(num_processes)

    # sleep for specified duration
    time.sleep(wall_time_in_s+1)
    return(size_in_mb, wall_time_in_s, num_processes);


def crash_unexpectedly(signum):
    print("going to receive signal {}.".format(signum))
    pid = os.getpid()
    time.sleep(1)
    os.kill(pid, signum)
    time.sleep(1)

# needs some improvements    
def cpu_usage():
    import random
    while True:
        x = random.random()
        x = x*x


class test_limit_resources_module(unittest.TestCase):

    @unittest.skipIf(not all_tests, "skipping successful tests")
    def test_success(self):
        
        print("Testing unbounded function call which have to run through!")
        local_mem_in_mb = None
        local_wall_time_in_s = None
        local_cpu_time_in_s = None
        local_grace_period = None
        
        wrapped_function = pynisher.enforce_limits(mem_in_mb = local_mem_in_mb, wall_time_in_s=local_wall_time_in_s, cpu_time_in_s = local_cpu_time_in_s, grace_period_in_s = local_grace_period)(simulate_work)
        
        for mem in [1,2,4,8,16]:
            self.assertEqual((mem,0,0),wrapped_function(mem,0,0))

    @unittest.skipIf(not all_tests, "skipping out_of_memory test")
    def test_out_of_memory(self):
        print("Testing memory constraint.")
        local_mem_in_mb = 64
        local_wall_time_in_s = None
        local_cpu_time_in_s = None
        local_grace_period = None
        
        wrapped_function = pynisher.enforce_limits(mem_in_mb = local_mem_in_mb, wall_time_in_s=local_wall_time_in_s, cpu_time_in_s = local_cpu_time_in_s, grace_period_in_s = local_grace_period)(simulate_work)
    
        for mem in [256,512,1024]:
            self.assertIsNone(wrapped_function(mem,0,0))
    
    @unittest.skipIf(not all_tests, "skipping time_out test")
    def test_time_out(self):
        print("Testing wall clock time constraint.")
        local_mem_in_mb = None
        local_wall_time_in_s = 1
        local_cpu_time_in_s = None
        local_grace_period = None
        
        wrapped_function = pynisher.enforce_limits(mem_in_mb = local_mem_in_mb, wall_time_in_s=local_wall_time_in_s, cpu_time_in_s = local_cpu_time_in_s, grace_period_in_s = local_grace_period)(simulate_work)
    
        for mem in range(1,10):
            self.assertIsNone(wrapped_function(mem,10,0))

    @unittest.skipIf(not all_tests, "skipping too many processes test")
    def test_num_processes(self):
        print("Testing number of processes constraint.")
        local_mem_in_mb = None
        local_num_processes = 1
        local_wall_time_in_s = None
        local_grace_period = None
        
        wrapped_function = pynisher.enforce_limits(mem_in_mb = local_mem_in_mb, wall_time_in_s=local_wall_time_in_s,num_processes = local_num_processes, grace_period_in_s = local_grace_period)(simulate_work)
        
        for processes in [2,15,50,100,250]:
            self.assertIsNone(wrapped_function(0,0, processes))

    @unittest.skipIf(not all_tests, "skipping unexpected signal test")
    def test_crash_unexpectedly(self):
        print("Testing an unexpected signal simulating a crash.")
        wrapped_function = pynisher.enforce_limits()(crash_unexpectedly)
        self.assertIsNone(wrapped_function(signal.SIGQUIT))
        
    @unittest.skipIf(not all_tests, "skipping unexpected signal test")
    def test_high_cpu_percentage(self):
        print("Testing cpu time constraint.")
        mem_in_mb = None
        wall_time_in_s = None
        cpu_time_in_s = 1
        grace_period = None
        wrapped_function = pynisher.enforce_limits(cpu_time_in_s = cpu_time_in_s, grace_period_in_s = grace_period)(cpu_usage)
        self.assertEqual(None,wrapped_function())


#logger = multiprocessing.log_to_stderr()
#logger.setLevel(logging.INFO)

unittest.main()

#wrapped_function = pynisher.enforce_limits(wall_time_in_s = 10, num_processes = 1)(simulate_work)       
#print(wrapped_function(0,0, 5))

