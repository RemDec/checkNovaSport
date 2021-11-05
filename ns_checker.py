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

def matching_dates_weekday(availables, query_sessions):
    matches = {}
    for av_date in availables:
        for session in query_sessions:
            if session.split('/')[0] == date_to_weekday(av_date):
                matches[av_date] = session
    return matches

def matching_sessions_at_date(availables, query_sessions):
    matches = {}
    valid_hours = query_sessions.split('/')[1].split('|')
    is_valid_hour = lambda hour: ('*' in valid_hours) or (hour in valid_hours)
    for av_session in availables:
        start_time = av_session['startTime']
        if (av_session['isBooked'] or av_session['status'] != 'active' or
            av_session['participantsCount'] == av_session['maxParticipants'] or
            start_time in matches):
            continue
        if is_valid_hour(start_time):
            matches[start_time] = av_session['classId']
    return matches

def query_from_tpl(query_tpl, params, defaults=True):
    if defaults:
        for p, p_dflt_val in config['param_queries_default'].items():
            params.setdefault(p, p_dflt_val)
    return query_tpl % params

def get_sessions_dates(sport, params={}):
    params['sport'] = sport
    q = query_from_tpl(queries.GetNextClassDates, params)
    resp = requests.post(url_post_to(), data=q, headers=form_headers())
    try:
        resp.raise_for_status()
        return resp.json()['data']['getNextClassDates']
    except requests.exceptions.HTTPError as e:
        print(f"Error GETting the session dates for {sport} :", e)
        return []

def get_sessions_at_date(sport, session_date, params={}):
    params['sport'] = sport
    params['date'] = session_date
    q = query_from_tpl(queries.GetCampusSportClasses, params)
    resp = requests.post(url_post_to(), data=q, headers=form_headers())
    try:
        resp.raise_for_status()
        return resp.json()['data']['getCampusSportClasses']
    except requests.exceptions.HTTPError as e:
        print(f"Error GETting the possible sessions for {sport} the {session_date} :", e)
        return []

def book_session(session_id):
    params = {'classId': session_id}
    q = query_from_tpl(queries.BookCampusSportClass, params, defaults=False)
    resp = requests.post(url_post_to(), data=q, headers=form_headers())
    try:
        resp.raise_for_status()
        return resp.json()['data']['bookCampusSportClass']
    except requests.exceptions.HTTPError as e:
        print(f"Error booking with the id {session_id} :", e)

def unbook_session(session_id):
    params = {'classId': session_id}
    q = query_from_tpl(queries.UnBookCampusSportClass, params, defaults=False)
    resp = requests.post(url_post_to(), data=q, headers=form_headers())
    return json.loads(resp.text)

def iteration_check(sport_queries):
    for sport_query in sport_queries:
        sport = sport_query['sport']
        sessions_dates = get_sessions_dates(sport)
        matches = matching_dates_weekday(sessions_dates, sport_query['sessions'])
        print(f" [{sport}] Dates for which we would check sessions :", matches)
        for matching_date, query_sessions in matches.items():
            sessions_at_date = get_sessions_at_date(sport, matching_date)
            print(f" | Possible sessions the {matching_date} : ", sessions_at_date)
            sessions_matches = matching_sessions_at_date(sessions_at_date, query_sessions)
            print(f" | --> Selected sessions the {matching_date} : ", sessions_matches)
            for session_hour, session_id in sessions_matches.items():
                if sport_query['autobooking']:
                    result_booking = book_session(session_id)
                    print(f" |   +--> Result for booking at {session_hour} :", result_booking)
        print("----------")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("-c", "--config", default="config.json", help="A JSON file containing config and sport sessions parameters")
    args_cli = parser.parse_args()

    config = {}
    try:
        config = json.loads(Path(args_cli.config).read_text())
    except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
        print(f"An error was raised when trying to read config file {args_cli.config} :", e)
        sys.exit(1)
    logging.basicConfig(filename=config["logfile"], filemode='w', level=logging.DEBUG)
    cli_logger = logging.getLogger('cli')
    cli_logger.setLevel(logging.INFO)
    cli_logger.addHandler(logging.StreamHandler(sys.stdout))

    iteration_check(config['param_queries'])
