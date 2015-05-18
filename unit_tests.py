#! /bin/python
import time
import numpy as np
import multiprocessing
import unittest
import os
import signal
import logging

import pynisher

all_tests=True


# TODO: get rid of numpy just to create some data of fixed size!
# 		add tests for cpu usage
#		add test for num_processes
#		add test with crash_unexpectedly to see what happens if the function call dies!

def simulate_work(size_in_mb, wall_time_in_s, num_processes = 0):
    # allocate memory (size_in_mb) with an array
    # note the actual size in memory of this process is a little bit larger 
    s = np.float64().itemsize    
    A = np.ones(int((size_in_mb*1024*1024)/s),dtype=np.float64);

    # try to spawn new processes
    if (num_processes > 0):
        multiprocessing.Pool(num_processes)

    # sleep for specified duration
    time.sleep(wall_time_in_s)
    return((size_in_mb, wall_time_in_s, num_processes));


def crash_unexpectedly(signum):
    pid = os.getpid()
    time.sleep(1)
    os.kill(pid, signum)
    time.sleep(1)
    


class test_limit_resources_module(unittest.TestCase):

    @unittest.skipIf(not all_tests, "skipping successful tests")
    def test_success(self):
        
        local_mem_in_mb = 256
        local_time_in_s = 2
        local_grace_period = 0
        
        wrapped_function = pynisher.enforce_limits(mem_in_mb = local_mem_in_mb, wall_time_in_s=local_time_in_s, grace_period_in_s = local_grace_period)(simulate_work)
        
        for mem in [1,2,4,8,16]:
            self.assertEqual((mem,0,0),wrapped_function(mem,0,0))

    @unittest.skipIf(not all_tests, "skipping out_of_memory test")
    def test_out_of_memory(self):

        local_mem_in_mb = 64
        local_wall_time_in_s = 2
        local_cpu_time_in_s = None
        local_grace_period = 0
        
        wrapped_function = pynisher.enforce_limits(mem_in_mb = local_mem_in_mb, wall_time_in_s=local_wall_time_in_s, cpu_time_in_s = local_cpu_time_in_s, grace_period_in_s = local_grace_period)(simulate_work)
    
        for mem in [256,512,1024]:
            print("\nmem: {}\n".format(mem))
            self.assertIsNone(wrapped_function(mem,0,0))
    
    @unittest.skipIf(not all_tests, "skipping time_out test")
    def test_time_out(self):

        local_mem_in_mb = -1
        local_time_in_s = 1
        local_grace_period = 2
        
        wrapped_function = pynisher.enforce_limits(mem_in_mb = local_mem_in_mb, wall_time_in_s=local_time_in_s, grace_period_in_s = local_grace_period)(simulate_work)
    
        for mem in [64,128,256,512]:
            self.assertIsNone(wrapped_function(mem,2,0))

    @unittest.skipIf(not all_tests, "skipping term signal test")
    def test_term_signal(self):

        local_mem_in_mb = -1
        local_time_in_s = 1
        local_grace_period = 1
        
        wrapped_function = pynisher.enforce_limits(mem_in_mb = local_mem_in_mb, wall_time_in_s=local_time_in_s, grace_period_in_s = local_grace_period)(simulate_work)
    
        for mem in [1,2,3,4]:
            self.assertIsNone(wrapped_function(mem,3,0))

#logger = multiprocessing.log_to_stderr()
#logger.setLevel(logging.DEBUG)

unittest.main()
