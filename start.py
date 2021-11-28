#!/usr/bin/env python3

import argparse
from subprocess import Popen, DEVNULL
from time import sleep
from threading import TIMEOUT_MAX


desc = """Main script
It launches the whole system spawning subprocesses :
    - The local HTTP server serving the browser's userscript and the auth token
    - The checker script that uses the token to query Novasport's API in order to check and book available
      sport sessions
    - A browser instance with novasport opened and the userscript installed
"""

URL_NOVASPORT = "https://login.novasport.be"
URL_USERSCRIPT = "http://localhost:8080/NovaSportAutoCheck.user.js"

parser = argparse.ArgumentParser(description=desc)

parser.add_argument("-p", "--port", type=int, default=8080, help="The port the local HTTP server will listen on")
parser.add_argument("-m", "--mail", default="YOURMAIL@mail.com", help="Userscript : the mail address used for NovaSport account")
parser.add_argument("--tokeninterval", type=int, default=30, help="Userscript : the interval (minutes) between each refresh and POST to the local HTTP server")
parser.add_argument("-c", "--config", default="config.json", help="The JSON config file for the checker containing target sport sessions and execution parameters")
parser.add_argument("--iterinterval", type=int, default=None, help="Give a fixed interval between checking iterations, instead of random considering max in config")
parser.add_argument("-nb", "--nobrowser", type=bool, default=False, help="Don't open browser pages (firefox) with the usercript and the novasport main page it is run on")

args_cli = parser.parse_args()

port = str(args_cli.port)
mail = args_cli.mail
token = str(args_cli.tokeninterval)
config_path = args_cli.config
iteration = None if args_cli.iterinterval is None else str(args_cli.iterinterval)
no_browser = args_cli.nobrowser


try:
    print("Starting server ...")
    p_server = Popen(["./server.py", "--port", port, "--mail", mail, "--interval", token], stdout=DEVNULL)
    sleep(0.1)
    try:
        if not no_browser:
            print("Opening webpages in browser firefox ...")
            p_firefox = Popen(["firefox", URL_NOVASPORT, URL_USERSCRIPT], stdout=DEVNULL, stderr=DEVNULL)
            sleep(0.1)
    except FileNotFoundError as e:
        print("Error opening firefox, it may not be installed", e)
    print("Starting NovaSportChecker process ...")
    checker_cmd = ["./ns_checker.py", "--config", config_path, "--port", port] + ([] if iteration is None else ["--interval", iteration])
    p_checker = Popen(checker_cmd)
    while True:
        sleep(TIMEOUT_MAX)
except KeyboardInterrupt:
    print("Killing server on pid", p_server.pid)
    p_server.kill()
    print("Killing NovaSport checker on pid", p_checker.pid)
    p_checker.kill()
