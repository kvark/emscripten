#!/usr/bin/env python2
# This Python file uses the following encoding: utf-8

import os, sys, subprocess, multiprocessing, threading, time
from runner import test_modes, PYTHON, path_from_root

# run slower ones first, to optimize total time
optimal_order = ['asm3i', 'asm1i', 'asm2nn', 'asm3', 'asm2', 'asm2g', 'asm2f', 'asm1', 'default']
assert set(optimal_order) == set(test_modes), 'need to update the list of slowest modes'

# set up a background thread to report progress
class Watcher(threading.Thread):
  stop = False

  def run(self):
    last = -1
    while not Watcher.stop:
      total = 0
      for mode in optimal_order:
        if os.path.exists(mode + '.err'):
          total += os.stat(mode + '.err').st_size
      if total != last:
        last = total
        print >> sys.stderr, '[parallel_test_copy.py watcher] total output: %d' % total
      time.sleep(1)

# run tests for one mode
def run_mode(args):
  mode = args[0]
  if len(args) > 1:
    # If args has multiple elements, then only the selected tests from that suite are run e.g. args=['asm1', 'test_hello_world', 'test_i64'] runs only tests asm1.test_hello_world and asm1.test_i64.
    for i in range(1, len(args)):
      if args[i].startswith('test_'):
        args[i] = mode + '.' + args[i]
    args = args[1:]
    print '<< running %s >>' % str(args)
  else:
    # If args has only one argument, e.g. args=['default'] or args=['asm1'], all tests are run in one suite.
    print '<< running %s >>' % mode

  proc = subprocess.Popen([PYTHON, path_from_root('tests', 'runner.py')] + args, stdout=open(mode + '.out', 'w'), stderr=open(mode + '.err', 'w'))
  proc.communicate()
  print '<< %s finished >>' % mode

def main():
  # clean up previous output
  for mode in optimal_order:
    if os.path.exists(mode + '.err'):
      os.unlink(mode + '.err')

  watcher = Watcher()
  watcher.start()

  # run all modes
  cores = int(os.environ.get('EMCC_CORES') or multiprocessing.cpu_count())
  pool = multiprocessing.Pool(processes=cores)
  args = [[x] + sys.argv[1:] for x in optimal_order]
  filenames = pool.map(run_mode, args, chunksize=1)

  # quit watcher
  Watcher.stop = True

  # emit all outputs
  for mode in optimal_order:
    print >> sys.stderr, '=== %s ===' % mode
    if os.path.exists(mode + '.err'):
      print >> sys.stderr, open(mode + '.err').read()
    print >> sys.stderr

if __name__ == '__main__':
  sys.exit(main())
