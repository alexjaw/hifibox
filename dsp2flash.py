#!/usr/bin/python
# -*- coding: utf-8 -*-
import argparse
import logging
import time
import hifi

DM1_DATA = 'data/dm1_data'
PARAM_DATA = 'data/param_data'
PROGRAM_DATA = 'data/program_data'

logging.basicConfig()
logger = logging.getLogger('dsp2flash')


def extract_hex(line):
    return line.replace("0x", "").replace(",", "").replace(" ", "")

def get_data(fname):
    with open(fname, 'r') as f:
        data = f.read().split('\n')
    hex_only = []
    for item in data:
        if '0x' in item:
            hex_only.append(extract_hex(item))
    return hex_only

def flash(fname, bytes=0):
    num_of_bytes = 0
    data = get_data(fname)
    for line in data:
        logger.info('data: {}'.format(repr(line)))
        num_of_bytes += 4
    if num_of_bytes != bytes:
        logger.error('Mismatch number of bytes. Requested {}. Found {}'.format(bytes, num_of_bytes))
        raise
    cmd = 'extflash write config 0' + ' ' + str(bytes) + ' ' + '0'
    logger.debug(cmd)
    r = hifi.send(com, cmd)
    if 'erasing' not in r.lower():
        logger.error('Flashing failed at initial cmd: {}'.format(cmd))
        logger.error(r)
        return

    # Wait for flash to complete erase
    flash_max_erase_time = 10
    t0 = time.time()
    while True:
        if time.time() - t0 > flash_max_erase_time:
            logger.error('Flashing failed at erasing - timeout.')
            logger.error(r)
            return
        try:
            r = hifi.check_read_buffer(com, timeout=flash_max_erase_time, sleeptime=0.1, eol='Continue\n\r\n')
            if 'continue' in r.lower():
                print('Erasing finished')
                break
        except Exception as e:
            pass

    # Time to send data to flash
    # Would like to have option to send in larger chunks than 4 bytes
    # Each line from dsp data is 4 bytes, but we could send multiples of 4
    w = 0  # total words transfered, 4 bytes
    b = 0  # total bytes transfered
    t0 = time.time()
    t1 = time.time()
    word_size = 4  #bytes
    transfer_size = 1 * word_size  # todo: to be used later
    transfer_data = ''             # here we save multiples of words
    for word in data:
        transfer_data += word
        if len(transfer_data)/2 == transfer_size:  # Each word has 8 chars, i.e. 2 chars per byte
            r = hifi.send(com, transfer_data, binary=True)
            if b == (bytes - transfer_size):
                if 'crc' not in r.lower():
                    logger.error('Did not receive crc. r = {}'.format(repr(r)))
                    try:
                        r = hifi.check_read_buffer(com, timeout=5, sleeptime=0.1, eol='200 OK\n\r\n')
                    except Exception as e:
                        pass
                break  # last byte is with crc check

            if 'continue' not in r.lower():
                logger.error('Did not receive Continue. r = {}'.format(repr(r)))
                if 'error' not in r.lower():
                    try:
                        r = hifi.check_read_buffer(com, timeout=5, sleeptime=0.1, eol='Continue\n\r\n')
                    except Exception as e:
                        pass
                logger.error('Flashing failed at byte/word {}/{}'.format(b, w))
                logger.error(r)
                break
            transfer_data = ''
        w += 1
        b += 4
        if b == (bytes - transfer_size):
            print('CRC verification started')
        if b%256 == 0:
            t2 = t1
            t1 = time.time()
            dt = t1 - t2
            fulltime = t1 - t0
            print('Saved {} bytes in time {} s, dt {} s'.format(b, fulltime, dt))

    # last response checks crc and returns 200 if crc is ok
    if '200 ok' in r.lower():
        logger.info('CRC OK')
        print('CRC OK')
    else:
        logger.error('CRC mismatch!')


if __name__ == '__main__':
    # Handle arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--flash",
                        help="Execute command and exit")
    parser.add_argument("-fn", "--filename",
                        help="Path to file")
    parser.add_argument("-nb", "--num_of_bytes",
                        help="Number of bytes to send")
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


    if args.flash:
        logger.info("cmd: {}".format(args.flash))

    com = hifi.get_com()

    try:
        if args.filename and args.num_of_bytes:
            flash(args.filename, int(args.num_of_bytes))
            #hifi.print_resp(hifi.send(com, args.flash))
        else:
            pass
    except KeyboardInterrupt:
        print 'Finished'

    com.close()
    exit(0)