#!/usr/bin/python
# -*- coding: utf-8 -*-
import argparse
import logging
import serial
import sys
import time

#cmd = 'io set out_enable 0'
log_level = logging.DEBUG  # default
EOL = '\r\n'  #this is CRLF which is standard in HTTP to mark terminate
EOLHEX = '0d0a'
EORESP = '\r\n'  # End Off Respons from hifi
ACKRESP = 'ACK\n\r\n'

logging.basicConfig()
logger = logging.getLogger('ser_cmd')

def get_com(port="/dev/ttyAMA0", baudrate=38400, timeout=0.1):
    com = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)
    r = request(com, 'dummy cmd')
    return com

def check_read_buffer(com, timeout=1, sleeptime=0.02, eol=None):
    r = ''
    t0 = time.time()
    while True:
        while com.inWaiting():
            r += com.read(com.inWaiting())
            time.sleep(sleeptime)
        logger.debug('com.read: {}'.format(repr(r)))
        if eol is None:
            if EORESP in r:
                break
            elif ACKRESP in r:
                break
        elif eol in r:
            break
        if (time.time() - t0) > timeout:
            logger.error('hifi.py timeout.')
            logger.error('Recv: {}'.format(repr(r)))
            raise Exception('timeout before end of message.')
        time.sleep(sleeptime)
    return r

def request(com, cmd, binary=False):
    if not isinstance(cmd, str):
        raise TypeError('cmd must be str')

    # Flush
    _ = ''
    while com.inWaiting():
        _ += com.read(com.inWaiting())
        time.sleep(0.01)
    if _:
        logger.debug('Flush: {}'.format(repr(_)))

    if binary:
        # We are expecting a string representing hex numbers
        # '61626364' is actually 'abcd'
        # todo: is it possible to send and handle '61626364' directly?
        #cmd = 'io set out_enable 0'
        #cmd_hex = cmd.encode('hex')
        bytedata = bytearray.fromhex(cmd + EOLHEX)
        logger.debug(bytedata)
        com.write(bytedata)
    else:
        # print('Writing')
        # i = 0;
        # while True:
        #     print("{}".format(repr(cmd[i])))
        #     i += 1
        #     if cmd[i] == '\r':
        #         break
        cmd = cmd + EOL
        if 'dummy' not in cmd:
            print("Sending: {}".format(repr(cmd)))
        com.write(cmd)
    r = check_read_buffer(com)
    return r


def send(com, cmd, binary=False):
    try:
        return request(com, cmd, binary=binary)
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
    parser.add_argument("-b", "--binary",
                        help="Send binary byte data and exit")
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
    logger.info('Setting logging level to {}'.format(repr(log_level)))

    if args.command:
        logger.info("cmd: {}".format(args.command))

    com = get_com()
    #print_resp(send(com, 'dummy command to get rid of shit'))  #must clear rx buffer

    try:
        if args.command:
            print_resp(send(com, args.command))
        elif args.binary:
            print_resp(send(com, args.binary, binary=True))
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
