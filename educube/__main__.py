from educube.client import main

import logging
logger = logging.getLogger(__name__)

root = logging.getLogger()

print('These are the attached loggers')
for key, val in root.manager.loggerDict.items():
    print(key, val)

main()
