import sys

from runners import chat_loader

from runners import test_runner
from runners import graph_runner, bench_runner, meena_runner

# to modify default debugging behavior check below

cmd = sys.argv.pop()

print('cmd: ', cmd)

if cmd == 'load':
    chat_loader.run()

elif cmd == 'graph':
    graph_runner.run()

elif cmd == 'qa':
    test_runner.run()

elif cmd == 'bench':
    bench_runner.run()

elif cmd == 'meena':
    meena_runner.run()

# default for debugging
else:
    meena_runner.run()
    # chat_loader.run()
    # graph_runner.run()

# test_runner.run()
