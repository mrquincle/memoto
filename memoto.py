#!/usr/bin/python

############################################################################
#
#  Author:  Anne van Rossum
#  License: LGPLv3, Apache, MIT, BSD, your choice
#  Copyrights: me
#
############################################################################

import sys
import time
import array

import usb.core
import usb.util

import threading
import os
import string

##########################  ENG CONFIG  #########################

dev = None
dev_type = None

output_path = "."

##########################  UTILITIES   #########################

def print_strings(filename):
    fd = open(filename, "rb")
    fdata = fd.read()
    fd.close()
    data = bytearray(fdata)
    cnt = 0
    fcnt = 0;
    print "Size of data: ", len(data)
    while cnt < len(data):
        #print ''.join('{:02x}'.format(x) for x in data[cnt:cnt+7])
        if data[cnt+4] == 4:
            print "Found directory: ",
        else:
            print "Found file: ",
        end = cnt+11*12
        sret = ''.join([chr(x) for x in data[cnt+8:end]])
        p = len(sret) - sret.count('\0')
        print sret

        if data[cnt+4] != 4:
            size = data[cnt] + data[cnt+1] * 256
            print "Size is: ", size, "bytes"

        cnt = end
        fcnt += 1
    print "Found in total", fcnt, "files/directories"

def strings(filename):
    result = []
    fd = open(filename, "rb")
    fdata = fd.read()
    fd.close()
    data = bytearray(fdata)
    cnt = 0
    while cnt < len(data):
        end = cnt+11*12
        sret = ''.join([chr(x) for x in data[cnt+8:end]])
        p = len(sret) - sret.count('\0')
        result.append(sret[0:p])
        cnt = end

    return result

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
    global dev
    global dev_type

    dev = usb.core.find(idVendor=0xf0f0, idProduct=0x1337)

    if dev is None:
        dev = usb.core.find(idVendor=0x525, idProduct=0xa4a1)
        if dev is None:
            raise ValueError('Memoto device not found')
        else:
        	   print "Found (ethernet-accessible) Memoto device"
        	   print "You don't need to use this script anymore. Connect through it via ethernet now!"
        	   exit()
    else:
        print "Found Memoto device"
        dev_type = "Memoto"

    # On Linux we need to detach usb HID first
    if dev.is_kernel_driver_active(0):
        print "Detach kernel driver"
        dev.detach_kernel_driver(0)
        dev.detach_kernel_driver(1)

    # Set configuration does NOT claim the interface, we need this
    print "Claim interface"
    usb.util.claim_interface(dev, 0)

# asumes path ends with /
def get_file(path, fname):
    # this bulk IN message returns the path of the file to be retrieved (in binary)
    # it needs to be running in the background, the ctrl_transfer message will cause it to receive
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
    ret = dev.ctrl_transfer(bmRequestType, bRequest, 0, wIndex, fullname)

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

def upload_file(path, fname):
    #filetype="FILE_REQ"
    #threading.Thread(target, args=[filetype, fname]).start()

    #time.sleep(3)
    #print "Send obtain file request"
    #send_cmd(0xc00402)

    fullname = path + fname
    print "Send upload file request", fullname
    bmRequestType = 0x40
    bRequest = 0x10
    wIndex = 0x00
    ret = dev.ctrl_transfer(bmRequestType, bRequest, 0, wIndex, fullname)

    opath = output_path + path
    fullname = opath + fname

    filetype = "JPEG"
    threading.Thread(target=bulk_out, args=[filetype, fullname]).start()

def get_list(path):
    tmpfile="list.txt"
    try:
        os.remove(tmpfile)
    except OSError:
        pass

    filetype="GET_LIST"
    threading.Thread(target=bulk, args=[filetype, path]).start()

    time.sleep(0.2)

    print "Send file list request", path
    bmRequestType = 0x40
    bRequest = 0x09
    wIndex = 0x00
    ret = dev.ctrl_transfer(bmRequestType, bRequest, 0, wIndex, path)

def just_list(path):
    tmpfile="list.txt"
    try:
        os.remove(tmpfile)
    except OSError:
        pass

    filetype="LIST"
    threading.Thread(target=bulk, args=[filetype, path]).start()

    time.sleep(0.2)

    print "Send file list request", path
    bmRequestType = 0x40
    bRequest = 0x09
    wIndex = 0x00
    ret = dev.ctrl_transfer(bmRequestType, bRequest, 0, wIndex, path)


def send_cmd(cmd, carg=""):
    if "Memoto" != dev_type:
        return

    else:
    #try:
        if cmd == 0x400505: #1702
            bmRequestType = 0x40
            bRequest = 0x05
            wIndex = 0x05
            msg = [ 0x00, 0x00, 0x00, 0x00]
            ret = dev.ctrl_transfer(bmRequestType, bRequest, 0, wIndex, msg)

        if cmd == 0xc020:
            bmRequestType = 0xc0
            bRequest = 0x20
            wIndex = 0x04
            length = 0x10
            ret = dev.ctrl_transfer(bmRequestType, bRequest, 0, wIndex, length);
            #print ret
        # resulted in 0x28 and other stuff

        if cmd == 1685:
            newlen = 0x28 # should be from return value from 0xc020
            bmRequestType = 0xc0
            bRequest = 0x20
            wIndex = 0x04
            length = newlen
            ret = dev.ctrl_transfer(bmRequestType, bRequest, 0, wIndex, length);
           # print ret
        # resulted in WINUSB

        if cmd == 0xc00401:
            bmRequestType = 0xc0
            bRequest = 0x04
            wIndex = 0x01
            length = (0x04 << 8) + 0x20
            ret = dev.ctrl_transfer(bmRequestType, bRequest, 0, wIndex, length);

        if cmd == 0xc00402:
            bmRequestType = 0xc0
            bRequest = 0x04
            wIndex = 0x02
            length = (0x04 << 8) + 0x20
            ret = dev.ctrl_transfer(bmRequestType, bRequest, 0, wIndex, length);
            sret = "".join([chr(x) for x in ret])
            print "Version:", sret

        if cmd == 0xc00403:
            bmRequestType = 0xc0
            bRequest = 0x04
            wIndex = 0x03
            length = (0x04 << 8) + 0x20
            ret = dev.ctrl_transfer(bmRequestType, bRequest, 0, wIndex, length);

        if cmd == 0xc00404:
            bmRequestType = 0xc0
            bRequest = 0x04
            wIndex = 0x04
            length = (0x04 << 8) + 0x20
            ret = dev.ctrl_transfer(bmRequestType, bRequest, 0, wIndex, length);

        if cmd == 0x400504:
            bmRequestType = 0x40
            bRequest = 0x05
            wIndex = 0x04
            #msg = [ 0x92, 0x87, 0xa2, 0x54]
            msg = [ 0x90, 0x40, 0xa3, 0x54]
            ret = dev.ctrl_transfer(bmRequestType, bRequest, 0, wIndex, msg);
            #print ret, '==', len(msg)

    #except:
    #    print 'command ', cmd, ' failed'
    #    pass

def get_files(path, files):
        cnt = 0;
        for f in files:
            trpath = path + "/"
            print "Get file", trpath, f
            get_file(trpath, f)
            print "Wait 5 seconds"
            time.sleep(5)
            cnt += 1

def bulk(filetype, filename):
    try:
        carg = 0x48;
        length = carg << 8;
        # only after a long time the bulk transport will fail (required for large chunks, such as in images)
        timeout_sec = 30
        ret = dev.read(0x81, length, timeout_sec * 1000)
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
            fd = open(tmpfile, "ab") # append
            fd.write(data)
            fd.close()
            print "Size of data: ", len(ret)
            if len(ret) == 8316: # 8380 - 64
                bulk(filetype,filename)
            elif filetype == "GET_LIST":
                print "Now obtain list"
                bulk("LIST_OBTAIN", filename)
            elif len(ret) == 132: # 132+64=196
               # bulk(filetype+"_END",filename)
               print "Empty folder"
            else:
                bulk(filetype+"_END",filename)
        elif filetype == "LIST_END":
            tmpfile="list.txt"
            print "Obtained list of strings:"
            print_strings(tmpfile)
        elif filetype == "LIST_OBTAIN":
            tmpfile="list.txt"
            fstr = strings(tmpfile)
            get_files(filename, fstr)
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
        print 'One of the bulk commands failed. Timeout is often caused by sending one dev.read too many'
        pass

# doesn't work yet. how does the Memoto know enough bytes have been received!?
def bulk_out(filetype, filename):
    maxsize = 512
    print "Need to write data in chunks of 512 bytes"
    #data = bytearray(ret)
    print "Open file locally", filename
    fd = open(filename, "r") # read
    data = fd.read()
    fd.close()
    #print data
    lbuf = bytearray(4)
    lbuf[3] = 0 #len(data)
    lbuf[2] = 0
    lbuf[1] = 0
    lbuf[0] = len(data)
    if len(data) > 256:
        print "OOPS, needs to be implemented"
    #lbuf = bytearray(len(data))
    #sret = ''.join([chr(x) for x in lbuf])
    #print sret
    print "Write size of the data to be sent"
    ret = dev.write(0x02, lbuf, len(lbuf))
    #time.sleep(0.1)


    print "Write data itself"
    ret = dev.write(0x02, data, len(data))
    #ret = dev.write(0x02, data, len(data))
    #ret = dev.write(0x02, data, len(data))

    #try:
    #    carg = 0x48
    #    length = carg << 8
    #    length = 5
    #    print "Read something"
    #    ret = dev.read(0x81, length, 1000)
    #except:
    #    print "Reading unsuccessful"
    #    pass
    # can I write something empty?
    lbuf = bytearray(0)
    ret = dev.write(0x02, lbuf, 0)

    # I missed apparently one 13376 item (with overhead), and all items are 64 overhead
    # < bulk |tr -s "  " " " | cut -f7 -d' ' | wc -l
    # 1111 (items in total)
    # first item has 4 bytes, so we have to extract that too
    # < bulk |tr -s "  " " " | cut -f7 -d' ' | paste -sd+ | xargs -I {} echo {}"-1111*64-4+(13376-64)" | bc
    # echo printf("%i",0x01155800)
    # 18176000

def imitate_windows():
    print "GET DESCRIPTOR Request dev"
    DESC_TYPE_dev = 0x01
    cfg = usb.control.get_descriptor(dev, 0x12, DESC_TYPE_dev, 0)
    #print cfg

    print "GET DESCRIPTOR Request CONFIGURATION"
    DESC_TYPE_CONFIG = 0x02
    cfg = usb.control.get_descriptor(dev, 0x09, DESC_TYPE_CONFIG, 0)
    #print cfg

    print "GET DESCRIPTOR Request CONFIGURATION"
    DESC_TYPE_CONFIG = 0x02
    cfg = usb.control.get_descriptor(dev, 0x20, DESC_TYPE_CONFIG, 0)
    #print cfg

    # then a request for 80: 6 3
    print "GET DESCRIPTOR Request STRING"
    product = usb.util.get_string(dev, dev.iProduct)

    # check for serial, 80: 6 1
    print "GET DESCRIPTOR Request STRING"
    serial = usb.util.get_string(dev, dev.iSerialNumber)

    print "SET CONFIGURATION Request"
    config = usb.control.get_configuration(dev)

    # check for serial, 80: 6 1
    print "GET DESCRIPTOR Request STRING"
    serial = usb.util.get_string(dev, dev.iSerialNumber)
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
    product = usb.util.get_string(dev, dev.iProduct)
    #print 'Product: ', str(product)

    # then a request for config
    #print "GET DESCRIPTOR Request dev"
    #cfg = usb.util.find_descriptor(dev, bConfigurationValue=6)
    #config = dev.get_active_configuration()
    #print 'Product: ', str(config)

    # then a request for config
    print "GET DESCRIPTOR Request dev"
    DESC_TYPE_dev = 0x01
    cfg = usb.control.get_descriptor(dev, 0x12, DESC_TYPE_dev, 0)
    #print cfg

    print "GET DESCRIPTOR Request CONFIGURATION"
    DESC_TYPE_CONFIG = 0x02
    cfg = usb.control.get_descriptor(dev, 0x09, DESC_TYPE_CONFIG, 0)
    #print cfg

    print "GET DESCRIPTOR Request CONFIGURATION"
    DESC_TYPE_CONFIG = 0x02
    cfg = usb.control.get_descriptor(dev, 0x20, DESC_TYPE_CONFIG, 0)
    #print cfg

    # status request
    print "GET STATUS REQUEST"
    status = usb.control.get_status(dev);
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
    elif command == "upload":

        path = values[0]
        fname = values[1]

        upload_file(path, fname)
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
