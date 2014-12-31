#!/usr/bin/python

############################################################################
#
#  Author:  Anne van Rossum
#  License: LGPLv3, Apache, MIT, BSD, your choice
#  Copyrights: me
#
############################################################################

import sys
#import platform
import time
#import socket
#import re
#import json
#import urllib2
#import base64
import array

import usb.core
import usb.util

import threading
import os
import string

##########################  ENG CONFIG  #########################

# The code...

# Protocol command bytes
IMAGE    = 0x01

DEVICE = None
DEVICE_TYPE = None

output_path = "."

##########################  UTILITIES   #########################

# From https://stackoverflow.com/questions/17195924/python-equivalent-of-unix-strings-utility
def strings(filename, min=4):
    with open(filename, "rb") as f:
        result = ""
        for c in f.read():
            if c in string.printable:
                result += c
                continue
            if len(result) >= min:
                yield result
            result = ""

##########################  MAIN CODE   #########################

def usage():
    print "Usage: memoto.py command arguments"
    print ""
    print "   commands:"
    print '     file path filename   - get file with given filename'
    print '     file "test"          - get a specific test file (does not exist for your memoto)'
    print '     files path           - get all files in a given directory'
    print '     files "test"         - get all files in test directory'
    print '     list path            - list files in a given directory'
    print '     list "test"          - list files in test directory'
    print ""


def setup_usb():
    # Tested only with the Cheeky Dream Thunder
    # and original USB Launcher
    global DEVICE 
    global DEVICE_TYPE

    DEVICE = usb.core.find(idVendor=0xf0f0, idProduct=0x1337)

    if DEVICE is None:
        raise ValueError('Memoto device not found')
    else:
        print "Found Memoto device"
        DEVICE_TYPE = "Memoto"

    # On Linux we need to detach usb HID first
    if DEVICE.is_kernel_driver_active(0):
        print "Detach kernel driver"
        DEVICE.detach_kernel_driver(0)
        DEVICE.detach_kernel_driver(1)

    # Set configuration does NOT claim the interface, we need this
    print "Claim interface"
    usb.util.claim_interface(DEVICE, 0) 

# asumes path ends with /
def get_file(path, fname):
    filetype="FILE_REQ"
    threading.Thread(target=bulk, args=[filetype, fname]).start()

    time.sleep(3)
    #print "Send obtain file request"
    #send_cmd(0xc00402)
    
    fullname = path + fname
    print "Send file request", fullname
    bmRequestType = 0x40
    bRequest = 0x02 
    wIndex = 0x00
    ret = DEVICE.ctrl_transfer(bmRequestType, bRequest, 0, wIndex, fullname)
 
    opath = output_path + path
    fullname = opath + fname
    try:
        os.makedirs(opath)
    except OSError:
        pass

    try:
        os.remove(fullname)
    except OSError:
        pass
    
    filetype = "JPEG"
    threading.Thread(target=bulk, args=[filetype, fullname]).start()
    
def get_list(path):
    filetype="GET_LIST"
    threading.Thread(target=bulk, args=[filetype, path]).start()

    time.sleep(3)
    print "Send obtain file request"
    send_cmd(0xc00402)
    
    print "Send file list request", path
    bmRequestType = 0x40
    bRequest = 0x09
    wIndex = 0x00
    ret = DEVICE.ctrl_transfer(bmRequestType, bRequest, 0, wIndex, path)

def just_list(path):
    filetype="LIST"
    threading.Thread(target=bulk, args=[filetype, path]).start()

    time.sleep(3)
    print "Send obtain file request"
    send_cmd(0xc00402)
    
    print "Send file list request", path
    bmRequestType = 0x40
    bRequest = 0x09
    wIndex = 0x00
    ret = DEVICE.ctrl_transfer(bmRequestType, bRequest, 0, wIndex, path)


def send_cmd(cmd, carg=""):
    if "Memoto" != DEVICE_TYPE:
        return

    else:
    #try:
        if cmd == 0x400505: #1702
            bmRequestType = 0x40
            bRequest = 0x05
            wIndex = 0x05
            msg = [ 0x00, 0x00, 0x00, 0x00]
            ret = DEVICE.ctrl_transfer(bmRequestType, bRequest, 0, wIndex, msg)

        if cmd == 0xc020:
            bmRequestType = 0xc0
            bRequest = 0x20
            wIndex = 0x04
            length = 0x10
            ret = DEVICE.ctrl_transfer(bmRequestType, bRequest, 0, wIndex, length);
            #print ret
        # resulted in 0x28 and other stuff

        if cmd == 1685:
            newlen = 0x28 # should be from return value from 0xc020
            bmRequestType = 0xc0
            bRequest = 0x20
            wIndex = 0x04
            length = newlen
            ret = DEVICE.ctrl_transfer(bmRequestType, bRequest, 0, wIndex, length);
           # print ret
        # resulted in WINUSB

        if cmd == 0xc00401:
            bmRequestType = 0xc0
            bRequest = 0x04
            wIndex = 0x01
            length = (0x04 << 8) + 0x20
            ret = DEVICE.ctrl_transfer(bmRequestType, bRequest, 0, wIndex, length);

        if cmd == 0xc00402:
            bmRequestType = 0xc0
            bRequest = 0x04
            wIndex = 0x02
            length = (0x04 << 8) + 0x20
            ret = DEVICE.ctrl_transfer(bmRequestType, bRequest, 0, wIndex, length);
            sret = "".join([chr(x) for x in ret])
            print "Version:", sret

        if cmd == 0xc00403:
            bmRequestType = 0xc0
            bRequest = 0x04
            wIndex = 0x03
            length = (0x04 << 8) + 0x20
            ret = DEVICE.ctrl_transfer(bmRequestType, bRequest, 0, wIndex, length);

        if cmd == 0xc00404:
            bmRequestType = 0xc0
            bRequest = 0x04
            wIndex = 0x04
            length = (0x04 << 8) + 0x20
            ret = DEVICE.ctrl_transfer(bmRequestType, bRequest, 0, wIndex, length);

        if cmd == 0x400504:
            bmRequestType = 0x40
            bRequest = 0x05
            wIndex = 0x04
            #msg = [ 0x92, 0x87, 0xa2, 0x54]
            msg = [ 0x90, 0x40, 0xa3, 0x54]
            ret = DEVICE.ctrl_transfer(bmRequestType, bRequest, 0, wIndex, msg);
            #print ret, '==', len(msg)

    #except:
    #    print 'command ', cmd, ' failed'
    #    pass

def get_files(path, files):
        cnt = 0;
        for f in files:
                print 'Search for "event" in filename'
                start=f.find("event")
                s = f[start:]
                trpath = path + "/"
                exclude = s.find("snap")
                if exclude != -1:
                        continue
                get_file(trpath, s)
                time.sleep(30)
                cnt += 1
                #if cnt == 4:
                #        return

def bulk(filetype, filename):
    try:
        carg = 0x48;
        length = carg << 8; 
        # only after a long time the bulk transport will fail (required for large chunks, such as in images)
        timeout_sec = 30
        ret = DEVICE.read(0x81, length, timeout_sec * 1000) 
        if filetype == "JPEG":
            #print "Store chunk of length ", len(ret), " in ", filename
            data = bytearray(ret)
            fd = open(filename, "ab") # append
            fd.write(data)
            fd.close()
            if len(ret) == 16384:
                bulk(filetype, filename)
            #else:
            #    bulk("IGNORE", filename);
        elif filetype == "LIST" or filetype == "GET_LIST":
            data = bytearray(ret)
            tmpfile="list.txt"
            fd = open(tmpfile, "wb") # overwrite previous
            fd.write(data)
            fd.close()
            if filetype == "GET_LIST":
                bulk("LIST_OBTAIN", filename)
            else:
                fstr = strings(tmpfile)
                print "Directory listing of ", filename
                for s in fstr:     
                    print s
        elif filetype == "LIST_OBTAIN":
            tmpfile="list.txt"
            fstr = strings(tmpfile)
            get_files(filename, list(fstr))
        elif filetype == "ACK":
            print "Received ack on request"
        elif filetype == "FILE_REQ":
             sret = ''.join([chr(x) for x in ret])
             # only print first 128 characters of file name
             print "Should return filename: ", sret[0:128]
        elif filetype == "IGNORE":
            print "Ignore this message for now"
        else:
            print "Other?", filetype
            #print "Bulk return: ", sret
    except:
        print 'One of the bulk commands failed. Timeout is often caused by sending one DEVICE.read too many'
        pass

def imitate_windows():
    print "GET DESCRIPTOR Request DEVICE"
    DESC_TYPE_DEVICE = 0x01
    cfg = usb.control.get_descriptor(DEVICE, 0x12, DESC_TYPE_DEVICE, 0)
    #print cfg

    print "GET DESCRIPTOR Request CONFIGURATION"
    DESC_TYPE_CONFIG = 0x02
    cfg = usb.control.get_descriptor(DEVICE, 0x09, DESC_TYPE_CONFIG, 0)
    #print cfg

    print "GET DESCRIPTOR Request CONFIGURATION"
    DESC_TYPE_CONFIG = 0x02
    cfg = usb.control.get_descriptor(DEVICE, 0x20, DESC_TYPE_CONFIG, 0)
    #print cfg

    # then a request for 80: 6 3
    print "GET DESCRIPTOR Request STRING"
    product = usb.util.get_string(DEVICE, DEVICE.iProduct)
    
    # check for serial, 80: 6 1
    print "GET DESCRIPTOR Request STRING"
    serial = usb.util.get_string(DEVICE, DEVICE.iSerialNumber)
    
    print "SET CONFIGURATION Request"
    config = usb.control.get_configuration(DEVICE)

    # check for serial, 80: 6 1
    print "GET DESCRIPTOR Request STRING"
    serial = usb.util.get_string(DEVICE, DEVICE.iSerialNumber)
    #print 'Serial: ', str(serial)
   
    # two urb control in messages
    print "URB_CONTROL in"
    send_cmd(0xc020)
    time.sleep(1)
    print "URB_CONTROL in"
    send_cmd(1685)
    time.sleep(1)

    # then a request for 80: 6 3
    print "GET DESCRIPTOR Request STRING"
    product = usb.util.get_string(DEVICE, DEVICE.iProduct)
    #print 'Product: ', str(product)

    # then a request for config
    #print "GET DESCRIPTOR Request DEVICE"
    #cfg = usb.util.find_descriptor(DEVICE, bConfigurationValue=6)
    #config = DEVICE.get_active_configuration()
    #print 'Product: ', str(config)

    # then a request for config
    print "GET DESCRIPTOR Request DEVICE"
    DESC_TYPE_DEVICE = 0x01
    cfg = usb.control.get_descriptor(DEVICE, 0x12, DESC_TYPE_DEVICE, 0)
    #print cfg

    print "GET DESCRIPTOR Request CONFIGURATION"
    DESC_TYPE_CONFIG = 0x02
    cfg = usb.control.get_descriptor(DEVICE, 0x09, DESC_TYPE_CONFIG, 0)
    #print cfg

    print "GET DESCRIPTOR Request CONFIGURATION"
    DESC_TYPE_CONFIG = 0x02
    cfg = usb.control.get_descriptor(DEVICE, 0x20, DESC_TYPE_CONFIG, 0)
    #print cfg

    # status request
    print "GET STATUS REQUEST"
    status = usb.control.get_status(DEVICE);
    #print 'Status: ', str(status)

def wake_up():
    filetype="ACK"
    filename=""
    threading.Thread(target=bulk, args=[filetype, filename]).start()

    time.sleep(0.9);
    print "URB_CONTROL out"
    send_cmd(0x400505)

    time.sleep(0.1);
    print "URB_BULK in"
    threading.Thread(target=bulk, args=[filetype, filename]).start()

    #time.sleep(60)
    time.sleep(5)
    print "URB_CONTROL in"
    send_cmd(0xc00401)
    #time.sleep(0.5)
    print "URB_CONTROL in"
    send_cmd(0xc00402)
    #time.sleep(0.5)
    print "URB_CONTROL in"
    send_cmd(0xc00403)
    #time.sleep(0.5)
    print "URB_CONTROL in"
    send_cmd(0xc00404)
    #time.sleep(0.5)
    print "URB_CONTROL out"
    send_cmd(0x400504)

# usb.bmRequestType == 0x40 || usb.bmRequestType == 0xc0
def run_command(command, values):
    command = command.lower()
    if command == "list":
        #imitate_windows()
        #wake_up() 

        if values[0]== "test":
                fullpath="/mnt/storage/140802_16"
        else:
                fullpath = values[0]
        just_list(fullpath)

    elif command == "files":
        #imitate_windows()
        #wake_up()

        if values[0]== "test":
                fullpath="/mnt/storage/140802_16"
        else:
                fullpath = values[0]
        get_list(fullpath)
    elif command == "file":

        imitate_windows()
        wake_up()

        if values[0] == "test":
            path="/mnt/storage"
            core="140804_02"
            key2="0332"
            extension=".jpg"
            key="45010053454d3038479025016f3f7071" 
            fname = "event_" + core + key2 + "_" + key + extension
            path = path + "/" + core + "/"
        else:
            path = values[0]
            fname = values[1]

        get_file(path, fname)
  
    else:
        print "Error: Unknown command: '%s'" % command

    time.sleep(1)


def main(args):

    if len(args) < 2:
        usage()
        sys.exit(1)

    setup_usb()

    command = args[1]
    values = []
    if len(args) > 2:
        values = args[2:]

    run_command(command, values)

    print "Thank you for using this script"

if __name__ == '__main__':
    main(sys.argv)
