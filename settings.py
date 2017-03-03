import logging
import os

LOGFILE = '/tmp/health.log'
logging.basicConfig(filename=LOGFILE, level=logging.INFO,format='%(asctime)s %(message)s')
WEBAPP_PATH = os.path.split(os.path.realpath(__file__))[0]

DEBUG = False
