import sys, os
import serial, time
import socketserver
import threading
import logging, logging.handlers
import queue
import gzip

SERIAL_PORT = "/dev/ttyUSB0"
BAUD_RATE = 115200
LOG_FILE = "ceilometer.log"

class GZipRotator:
    def __call__(self, source, dest):
        os.rename(source, dest)
        f_in = open(dest, 'rb')
        f_out = gzip.open("%s.gz" % dest, 'wb')
        f_out.writelines(f_in)
        f_out.close()
        f_in.close()
        os.remove(dest)


logging.basicConfig(format='%(message)s', level=logging.DEBUG)
logger = logging.getLogger('ceilometer')
handler = logging.handlers.TimedRotatingFileHandler(LOG_FILE, when='D', interval=1, backupCount=0)
handler.setLevel(0)
# handler.rotator = GZipRotator()
logger.addHandler(handler)
logger.propagate = False


class TCPHandler(socketserver.StreamRequestHandler):
    """Allow forwarding of data to all other registered clients."""

    def __init__(self, request, client_address, server):
        """Initialize the handler with a store for future date streams."""
        self.buffer = queue.Queue()
        super().__init__(request, client_address, server)

    def setup(self):
        """Register self with the clients the server has available."""
        super().setup()
        self.server.add_client(self)

    def handle(self):
        """Run a continuous message pump to broadcast all client data."""
        try:
            while True:
                try:
                    # Write stuff as soon as it gets to the buffer. Blocking.
                    self.wfile.write(self.buffer.get(True))
                except BrokenPipeError:
                    # we don't worry so much if the client disconnects
                    self.server.remove_client(self)
                    
        except (ConnectionResetError, EOFError):
            self.server.remove_client(self)

    def schedule(self, data):
        """Arrange for a data packet to be transmitted to the client."""
        self.buffer.put_nowait(data)

    def finish(self):
        """Remove the client's registration from the server before closing."""
        self.server.remove_client(self)
        super().finish()

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """Provide server support for the management of connected clients."""

    def __init__(self, server_address, request_handler_class):
        """Initialize the server and keep a set of registered clients."""
        super().__init__(server_address, request_handler_class)
        self.clients = set()

    def add_client(self, client):
        """Register a client with the internal store of clients."""
        self.clients.add(client)

    def broadcast(self, data):
        for client in tuple(self.clients):
            client.schedule(data)

    def remove_client(self, client):
        """Take a client off the register to disable broadcasts to it."""
        try:
            self.clients.remove(client)
        except KeyError:
            pass
            


server = ThreadedTCPServer(("0.0.0.0", 2001), TCPHandler)

        
def serial_listener():
    s = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=3)

    s.parity = serial.PARITY_ODD # work around pyserial issue #30
    s.parity = serial.PARITY_NONE

    out_buffer = bytearray()
    
    while True:
        ibyte = s.read()

        if len(ibyte) == 0: continue
        
        # if we get a "begin reading" byte (\x01), flush our buffers and
        # print a timestamp in the log
        if ord(ibyte) == 1:
            server.broadcast(out_buffer)
            logger.info(out_buffer[:-1].decode('ASCII'))

            out_buffer = bytearray()

            ts = time.strftime("%Y-%m-%d %H:%M:%S")
            logger.info(ts)

        out_buffer.append(ord(ibyte))
            
            
if __name__ == '__main__':
    
    # Start a thread with the server -- that thread will then start one
    # more thread for each request
    server_thread = threading.Thread(target=server.serve_forever)

    # Exit the server thread when the main thread terminates
    server_thread.daemon = True
    server_thread.start()

    serial_thread = threading.Thread(target=serial_listener)
    # serial_thread.daemon = True
    serial_thread.start()    
