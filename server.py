import http.server
import socketserver
import argparse
import json


class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.path = 'index.html'
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        datalen = int(self.headers['Content-Length'])
        obj = json.loads(self.rfile.read(datalen).decode('utf-8'))
        rslt_str = json.dumps({'echothis': obj})
        rslt_bytes = rslt_str.encode('utf-8')
        self.send_response(HTTPStatus.OK)
        self.end_headers()
        self.wfile.write(rslt_bytes)


def run():
    handler_object = MyHttpRequestHandler
    PORT = 8000
    my_server = socketserver.TCPServer(("", PORT), handler_object)
    my_server.serve_forever()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Run a simple HTTP server")
    parser.add_argument(
        "-l",
        "--listen",
        default="localhost",
        help="Specify the IP address on which the server listens",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=8000,
        help="Specify the port on which the server listens",
    )
    args = parser.parse_args()
    run(addr=args.listen, port=args.port)
