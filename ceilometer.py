# -*- coding: utf-8 -*-

import numpy as np
import re


def hex5_to_int(s):
    # two's complement
    b = int(s, base=16)
    if b & 0x80000:
        b = b - 0x100000
    return b


feet_per_meter=3.28084

def parse_ceilometer_chunk(chunk):
    """
    parses chunks of data that follows the format as described on p63 here:
        http://cedadocs.ceda.ac.uk/1240/1/CL31_User%27s_Guide_M210482EN-F.pdf

    Parameters
    ----------
    chunk : a list of lines as read from the serial port.
    - The lines should start with a \x01 char, and end with a \x04 char.


    Returns
    -------
    output : a dict full of parsed values. z-units are converted to metres.

    """
    if type(chunk) is list:
        lines = chunk
    else:
        lines = chunk.split('\n')

    #-------------------------------------

    header = lines[0]
    if header[0] != "\x01":
        raise Exception('wrong header - expected \\x01')
    output = {}
    output['softwarelevel'] = header[4:7]
    output['with_sky_condition_data'] = (header[7] == "2")
    samplerange = header[8]
    if samplerange == "1":
        dz, N = 10, 770
    elif samplerange == "2":
        dz, N = 20, 385
    elif samplerange == "3":
        dz, N = 5, 1500
    elif samplerange == "4":
        dz, N = 5, 770
    elif samplerange == "5":
        dz, N = None, None
    z = np.arange(0, dz * N, dz) #This is already in m.
    output['z']=z

    #--------------------------------------
    line2= lines[1].rstrip()
    output['status'] = line2[21:]
    status = int(output['status'],base=16)
    if (status & 0x80):
        #units are metres
        multiplier = 1
    else:
        #units are feet
        multiplier = 1/feet_per_meter

    output['detection_status'] = line2[0]
    output['warning_alarm'] = line2[1]
    output['cloud_base'] = np.array(line2[3:20].replace('/////','nan').split(' ')).astype(float)*multiplier


    if not output['warning_alarm'] == '0':
        print('Warning/Alarm',output['warning_alarm'],output['status'])
    if output['detection_status']=='4':
        #full obscuration
        output['vertical_visibility'] = cloud_base[0]
        output['highest_signal_detected'] = cloud_base[1]
        output['cloud_base']= np.array([np.nan,np.nan,np.nan])
    else:
        output['vertical_visibility'] = None
        output['highest_signal_detected'] = None

    #--------------------------------------
    line3 = lines[2].rstrip()
    #TODO:
    numbers3 = np.array(re.split('\s+',re.sub('/+','nan',line3[2:]))).astype(float)
    output['cloud_heights'] = numbers3[1::2]*10*multiplier
    output['cloud_octas'] = numbers3[0::2]
    output['cloud_octas'][np.isnan(output['cloud_heights'])]=np.nan
    # if (output['cloud_octas'][0]>8)|(output['cloud_octas']<-1):
    #     #not sure what cloud octa = 9 means on page 65
    #     output['cloud_octas'][:]=np.nan
    #---------------------------------
    line4 = lines[3].rstrip()
    #TODO
    #-----------------------------------
    if dz:
        datatxt = lines[4].rstrip()
    chksum = lines[5].rstrip()
    data = np.array([hex5_to_int(datatxt[i : i + 5]) for i in range(0, len(datatxt), 5)])
    data = data * 1.0
    output['profile']=data
    return output


def read_next_chunk(reader):
    """
    Keeps reading lines from a file-like reader object until it has a chunk
    that starts with a \x01 char and ends with a line that starts with \x03.

    Parameters
    ----------
    reader : a reader object (not sure that is the correct type description - TODO)

    Returns
    -------
    lines : the data chunk as a list of lines.

    """
    has_found_header = False
    while True:
        line = reader.readline()
        if line[0] == "\x01":
            lines=[]
            has_found_header = True
        if has_found_header:
            lines.append(line)
        if line[0] == "\x03":
            return lines

