# -*- coding: utf-8 -*-
"""
Created on Thu Jul  7 16:26:57 2022

@author: ag
"""


from flask import Flask
import json
import numpy as np
import socket
import ceilometer

from datetime import datetime


app = Flask(__name__)


HOST = "10.2.3.13"  # ceilometer fixed ip
PORT = 2001  # Port to listen on (non-privileged ports are > 1023)


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)


@app.route('/')
def index():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        reader = s.makefile("r")

        lines = ceilometer.read_next_chunk(reader)

        output = ceilometer.parse_ceilometer_chunk(lines)
        output['datetime'] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    return json.dumps(output, cls=NumpyEncoder)



if __name__ == '__main__':
    app.run(debug=True, port=8400, host='0.0.0.0')
