# run.py
import sys

if len(sys.argv) > 1:
  arg = eval((sys.argv)[1])
else:
  arg = 0

if arg == 1:
  from server import server
  server.port = 8521 # The default
  server.launch()
else:

  from factory import *

  restore = FactoryModel(1,3, 15, 15)
  while restore.running:
    restore.step()

