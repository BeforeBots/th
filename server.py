import http.server
import socketserver
import argparse
import os
import json


class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.path = 'index.html'
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        datalen = int(self.headers['Content-Length'])
        pre_post_data = self.rfile.read(datalen)
        jsonprepost = json.loads(pre_post_data, cls=json.JSONDecoder)
        resp = self.run_shell_command(jsonprepost)
        self.send_response(200)
        self.end_headers()
        final_resp = resp.encode("utf-8")
        self.wfile.write(final_resp)

    def run_shell_command(self, res):
        stream = os.popen(res)
        output = stream.read()
        return output


def run(host="localhost", port=8000):
    handler_object = MyHttpRequestHandler
    my_server = socketserver.TCPServer((host, port), handler_object)
    print(f"Server started at port -> {port}")
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
