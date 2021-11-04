#!/usr/bin/env python3

from pathlib import Path
import requests
import argparse
import datetime
import logging
import json
import sys

import templates.ns_queries as queries


desc = """NovaSport checker
Will query NovaSport's API to retrieve sport sessions and do some actions based on
what behavior is defined in the configuration file for given sessions.
"""

parser = argparse.ArgumentParser(description=desc)
parser.add_argument("-c", "--config", default="config.json", help="A JSON file containing config and sport sessions parameters")
args_cli = parser.parse_args()

config = {}
try:
    config = json.loads(Path(args_cli.config).read_text())
except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
    print(f"An error was raised when trying to read config file {args_cli.config} :", e)
    sys.exit(1)


def get_token(port=8080):
    url = f"http://localhost:{port}/token"
    try:
        r = requests.get(url)
        return json.loads(r.text)['token']
    except requests.exceptions.ConnectionError as e:
        print("Cannot retrieve token from HTTP server, check it is running", e)

def form_headers():
    return {
        'Host': config['ns_api'],
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:93.0) Gecko/20100101 Firefox/93.0",
        'Accept-Language': "fr,fr-FR;q=0.8",
        'Accept-Encoding': "gzip, deflate, br",
        'Content-Type': "application/json",
        'Connection': "keep-alive",
        'Authorization': get_token(),
    }

def url_post_to():
    return f"https://{config['ns_api']}/graphql"

def date_to_weekday(d):
    # date is yyyy-mm-dd, we need Wednesday, ...
    date_obj = datetime.date(*(int(s) for s in d.split('-')))
    return date_obj.strftime("%A")


def query_from_tpl(query_tpl, params, defaults=True):
    if defaults:
        for p, p_dflt_val in config['param_queries_default'].items():
            params.setdefault(p, p_dflt_val)
    return query_tpl % params

def get_sessions_dates(sport, params={}):
    params['sport'] = sport
    q = query_from_tpl(queries.GetNextClassDates, params)
    resp = requests.post(url_post_to(), data=q, headers=form_headers())
    return json.loads(resp.text)

def get_sessions_at_date(sport, session_date, params={}):
    params['sport'] = sport
    params['date'] = session_date
    q = query_from_tpl(queries.GetCampusSportClasses, params)
    resp = requests.post(url_post_to(), data=q, headers=form_headers())
    return json.loads(resp.text)

def book_session(session_id):
    params = {'classId': session_id}
    q = query_from_tpl(queries.BookCampusSportClass, params, defaults=False)
    resp = requests.post(url_post_to(), data=q, headers=form_headers())
    return json.loads(resp.text)

def unbook_session(session_id):
    params = {'classId': session_id}
    q = query_from_tpl(queries.UnBookCampusSportClass, params, defaults=False)
    resp = requests.post(url_post_to(), data=q, headers=form_headers())
    return json.loads(resp.text)


