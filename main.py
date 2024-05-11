import os
import json
import logging
import mimetypes
import socket
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from threading import Thread
from urllib.parse import urlparse, unquote_plus


BASE_DIR = Path(__file__).parent
BUFFER_SIZE = 1024
HTTP_PORT = 3000
HTTP_HOST = '0.0.0.0'
SOCKET_HOST = '127.0.0.1'
SOCKET_PORT = 5000
STORAGE_DIR = Path(BASE_DIR/'storage')
JSON_FILE = 'data.json'


class MyFramework(BaseHTTPRequestHandler):

    def do_POST(self):
        data = self.rfile.read(int(self.headers.get('Content-Length')))

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.sendto(data, (SOCKET_HOST, SOCKET_PORT))
        client_socket.close()

        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()
        
    def do_GET(self):
        url = urlparse(self.path)
        match url.path:
            case '/':
                self.send_html("index.html")
            case '/message':
                self.send_html("message.html")
            case '/contact':
                self.send_html("contact.html")
            case _:
                file_path = BASE_DIR.joinpath(url.path[1:])
                if file_path.exists():
                    self.send_static(str(file_path))
                else:
                    self.send_html("error.html", 404)
                
    def send_static(self, static_filename, status_code=200):
        self.send_response(status_code)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header('Content-type', mt[0])
        else:
            self.send_header('Content-type', 'text/plain')
        self.end_headers()

        with open(static_filename, 'rb') as f:
            self.wfile.write(f.read())

    def send_html(self, html_filename, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        with open(html_filename, 'rb') as f:
            self.wfile.write(f.read())


def save_data_from_form(data):
    parse_data = unquote_plus(data.decode())
    try:
        parse_dict = {key: value for key, value in [el.split('=') for el in parse_data.split('&')]}
        cur_dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        path_to_json = Path.joinpath(STORAGE_DIR, JSON_FILE)
        json_data = {}
        if not STORAGE_DIR.exists():
            os.mkdir('storage')
            with open(path_to_json, 'w', encoding='utf-8') as fh:
                json.dump({cur_dt:parse_dict}, fh, ensure_ascii=False, indent=4)
        if path_to_json.exists():
            with open(path_to_json, 'r', encoding='utf-8') as fh2:
                load_data = json.load(fh2)
                json_data.update(load_data)
        with open(path_to_json, 'w', encoding='utf-8') as fh3:
            json_data.update({cur_dt:parse_dict})
            json.dump(json_data, fh3, ensure_ascii=False, indent=4)

    except ValueError as err:
        logging.error(err)
    except OSError as err:
        logging.error(err)


def run_socket_server(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((host, port))
    logging.info("Starting socket server")
    try:
        while True:
            msg, address = server_socket.recvfrom(BUFFER_SIZE)
            logging.info(f"Socket received {address}: {msg}")
            save_data_from_form(msg)
    except KeyboardInterrupt:
        pass
    finally:
        server_socket.close()

def run_http_server(host, port):
    address = (host, port)
    http_server = HTTPServer(address, MyFramework)
    logging.info("Starting http server")
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        http_server.server_close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(threadName)s %(message)s')
    server = Thread(target=run_http_server, args=(HTTP_HOST, HTTP_PORT))
    server.start()
    server_socket = Thread(target=run_socket_server, args=(SOCKET_HOST, SOCKET_PORT))
    server_socket.start()
