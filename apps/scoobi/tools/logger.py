import logging
import coloredlogs  # type: ignore


logger = logging.getLogger()
logging.getLogger("imported_module").setLevel(logging.WARNING)

# install a handler on the root logger with level debug
# coloredlogs.install(level='DEBUG')
# pass a specific logger object
# coloredlogs.install(level='DEBUG', logger=logger)
coloredlogs.install(
    level='INFO', logger=logger,
    # fmt='%(asctime)s.%(msecs)03d %(filename)s:%(lineno)d %(levelname)s %(message)s'
    fmt='---[%(filename)s:%(lineno)d %(levelname)s] %(message)s \n'
)

# logging.debug('message with level debug')
# logging.info('message with level info')
# logging.warning('message with level warning')
# logging.error('message with level error')
# logging.critical('message with level critical')
