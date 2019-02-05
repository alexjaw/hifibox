#!/usr/bin/python
# -*- coding: utf-8 -*-
import argparse
import logging
import serial
import sys
import time

#cmd = 'io set out_enable 0'
log_level = logging.DEBUG  # default
EOL = '\r'
EORESP = '\n\r\n'  # End Off Respons from hifi
ACKRESP = 'ACK\n\r\n'

def get_com(port="/dev/ttyAMA0", baudrate=9600, timeout=0.1):
    return serial.Serial(port=port, baudrate=baudrate, timeout=timeout)


def request(com, cmd):
    if not isinstance(cmd, str):
        raise TypeError('cmd must be str')

    # Flush
    _ = ''
    while com.inWaiting():
        _ += com.read(com.inWaiting())
        time.sleep(0.01)
    if _:
        logger.debug('Flush: {}'.format(repr(_)))

    com.write(cmd + EOL)
    r = ''
    timeout = 7
    sleeptime = 0.01
    t0 = time.time()
    while True:
        while com.inWaiting():
            r += com.read(com.inWaiting())
            time.sleep(sleeptime)
        logger.debug('com.read: {}'.format(repr(r)))
        if EORESP in r:
            break
        elif ACKRESP in r:
            break
        if (time.time() - t0) > timeout:
            logger.error('hifi.py timeout.')
            raise Exception('timeout before end of message.')
        time.sleep(sleeptime)
    return r


def send(com, cmd):
    try:
        return request(com, cmd)
    except Exception as e:
        logger.error(e)
        return 'error'


def print_resp(resp):
    try:
        print '{}'.format(resp.strip())
    except Exception as e:
        logger.error(e)


if __name__ == '__main__':
    # Handle arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--command",
                        help="Execute command and exit")
    #parser.add_argument("-p", "--port",
    #                    help="Set serial port, e.g. /dev/ttyACM0")
    parser.add_argument("-v", "--verbosity",
                        action="count",
                        default=0,
                        help="Increase logging information, -v=INFO, -vv=DEBUG")
    args = parser.parse_args()

    log_level = logging.CRITICAL  # default
    if args.verbosity >= 2:
        log_level = logging.DEBUG
    elif args.verbosity >= 1:
        log_level = logging.INFO

    logging.basicConfig(level=log_level)
    logger = logging.getLogger('ser_cmd')
    logger.info('Setting logging level to {}'.format(repr(log_level)))

    if args.command:
        logger.info("cmd: {}".format(args.command))

    com = get_com()
    #print_resp(send(com, 'dummy command to get rid of shit'))  #must clear rx buffer

    try:
        if args.command:
            print_resp(send(com, args.command))
        else:
            print_resp(send(com, 'version'))
            print
            print "Enter command or (q)uit."

            while True:
                cmd = raw_input('> ')
                if cmd == 'q':
                    raise KeyboardInterrupt
                resp = send(com, cmd)
                print_resp(resp)
    except KeyboardInterrupt:
        print 'Finished'
    
    com.close()
    exit(0)
