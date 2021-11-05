#!/usr/bin/env python3

from http.server import BaseHTTPRequestHandler, HTTPServer
from templates import userscript, ns_queries
import logging
import argparse
import json

desc = """HTTP Server
Local HTTP server to handle authentication tokens and userscript
To be run on a machine the userscript retrieving the authentication token from the browser can query.
"""

TOKEN_FILE = 'last_token'
USERSCRIPT_FILE = 'NovaSportAutoCheck.user.js'

class Server(BaseHTTPRequestHandler):

    def _set_CORS_last_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def _set_response_200(self, content_type='application/json'):
        self.send_response(200)
        self.send_header('Content-type', content_type)
        self._set_CORS_last_headers()

    def _set_response_400(self, msg="Error"):
        self.send_response(400)
        self.send_header('Content-type', 'text/html')
        self._set_CORS_last_headers()
        self.wfile.write(msg.encode())

    def _read_token_file(self):
        try:
            with open(TOKEN_FILE, 'r') as fp:
                return fp.readline().strip()
        except FileNotFoundError:
            with open(TOKEN_FILE, 'w') as fp:
                return None

    def _GET_token(self):
        token = self._read_token_file()
        if token:
            self._set_response_200()
            self.wfile.write(json.dumps({'token': token}).encode('utf-8'))
        else:
            self._set_response_400("No token available, it should be POSTed before")

    def _POST_token(self, token):
        token = str(token.get('token', ''))
        if not token:
            self._set_response_400("Token value absent from POSTed object (key 'token')")
        with open(TOKEN_FILE, 'w') as fp:
            fp.write(token)
        self._set_response_200()
        self.wfile.write(json.dumps({'updatedToken': token}).encode('utf-8'))

    def _GET_userscript(self):
        try:
            with open(USERSCRIPT_FILE, 'rb') as fp:
                self._set_response_200()
                self.wfile.write(fp.read())
        except FileNotFoundError:
            with open(USERSCRIPT_FILE, 'w', encoding='utf-8') as fp:
                rendered = userscript.script % {'email': args_cli.mail, 'port': args_cli.port, 'interval': args_cli.interval}
                fp.write(rendered)
                self._set_response_200(content_type='application/json')
                self.wfile.write(rendered.encode())

    def do_GET(self):
        route = str(self.path)
        logging.info("GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))
        if route == "/token":
            self._GET_token()
        elif route in ["/userscript", "/userscript.user.js", "/NovaSportAutoCheck.user.js"]:
            self._GET_userscript()

    def do_POST(self):
        route = str(self.path)
        if self.headers.get('Content-Length') is None:
            self._set_response_400("Need Content-Length header")
        elif self.headers.get('Content-Type') is None or self.headers['Content-Type'] != 'application/json':
            self._set_response_400("Need Content-Type header to be application/json")
        else:
            content_length = int(self.headers['Content-Length'])
            post_data = json.loads(self.rfile.read(content_length))
            logging.info("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n", str(self.path), str(self.headers), str(post_data))
            if route == "/token":
                self._POST_token(post_data)

    def do_OPTIONS(self):
        self.send_response(200)
        self._set_CORS_last_headers()

def run(server_class=HTTPServer, handler_class=Server):
    global args_cli
    logging.basicConfig(level=logging.INFO)
    server_address = ('', args_cli.port)
    httpd = server_class(server_address, handler_class)
    logging.info(f"Starting httpd on port {args_cli.port} ...\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logging.info('Stopping httpd...\n')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument("-p", "--port", type=int, default=8080, help="The port to run on")
    parser.add_argument("-m", "--mail", default="YOURMAIL@mail.com", help="Userscript : the mail address used for NovaSport account")
    parser.add_argument("-i", "--interval", type=int, default=10, help="Userscript : the interval (s) between each token POST to this server")
    args_cli = parser.parse_args()
    run()

