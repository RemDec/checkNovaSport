#!/usr/bin/env python3

from pathlib import Path
from time import sleep
from random import randint
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

NEWLINE = '\n'
MIN_INTERVAL = 10

# --- Utilities ---

def setup_logging():
    global config
    logging.basicConfig(filename=config["logfile"], filemode='w', level=logging.DEBUG)
    cli_logger = logging.getLogger('cli')
    cli_logger.setLevel(logging.INFO)
    cli_logger.addHandler(logging.StreamHandler(sys.stdout))

def log_all(msg, level=logging.INFO):
    logging.log(level, msg)
    logging.getLogger('cli').log(level, msg)

def date_to_weekday(d):
    # date is yyyy-mm-dd, we need Wednesday, ...
    date_obj = datetime.date(*(int(s) for s in d.split('-')))
    return date_obj.strftime("%A")

def close_to_new_hour(threshold):
    now = datetime.datetime.now()
    elapsed_sec = 60 * now.minute + now.second
    time_to_wait = max(0, 3600 - elapsed_sec)
    if (time_to_wait <= threshold):
        return (True, time_to_wait)
    return (False, -1)


# --- Autocheck process ---

def get_token(port=8080):
    url = f"http://localhost:{port}/token"
    try:
        r = requests.get(url)
        return json.loads(r.text)['token']
    except requests.exceptions.ConnectionError as e:
        log_all(f"Cannot retrieve token from HTTP server, check it is running : {e}", logging.ERROR)

def form_headers():
    global config, interval
    return {
        'Host': config['ns_api'],
        'User-Agent': config['user_agents'][interval % len(config['user_agents'])],
        'Accept-Language': "fr,fr-FR;q=0.8",
        'Accept-Encoding': "gzip, deflate, br",
        'Content-Type': "application/json",
        'Connection': "keep-alive",
        'Authorization': get_token(),
    }

def url_post_to():
    global config
    return f"https://{config['ns_api']}/graphql"

def matching_dates_weekday(availables, query_sessions):
    # available dates are numeric 'yyyy-mm-dd' and we want to find matches (no matters the
    # hour) with 'DayFullName/[hours]' in config, where DayFullName is like 'Wednesday'
    matches = {}
    for av_date in availables:
        for session in query_sessions:
            if session.split('/')[0] == date_to_weekday(av_date):
                matches[av_date] = session
    return matches

def matching_sessions_at_date(availables, query_sessions):
    # available are dict for a session at a given hour and we want to find matches with
    # hours the same day for 'DayFullName/[hours]' in config
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
    # apply variables values to template queries
    global config
    if defaults:
        for p, p_dflt_val in config['param_queries_default'].items():
            params.setdefault(p, p_dflt_val)
    return query_tpl % params

def get_sessions_dates(sport, params={}):
    # from NS retrieve all planned sessions dates (yyyy-mm-dd) of a given sport
    params['sport'] = sport
    q = query_from_tpl(queries.GetNextClassDates, params)
    resp = requests.post(url_post_to(), data=q, headers=form_headers())
    try:
        resp.raise_for_status()
        return resp.json()['data']['getNextClassDates']
    except requests.exceptions.HTTPError as e:
        log_all(f"Error GETting the session dates for {sport} : {e}", logging.ERROR)
        return []

def get_sessions_at_date(sport, session_date, params={}):
    # from NS retrieve all sessions properties (like hour) of a given sport at a given date
    params['sport'] = sport
    params['date'] = session_date
    q = query_from_tpl(queries.GetCampusSportClasses, params)
    resp = requests.post(url_post_to(), data=q, headers=form_headers())
    try:
        resp.raise_for_status()
        return resp.json()['data']['getCampusSportClasses']
    except requests.exceptions.HTTPError as e:
        log_all(f"Error GETting the possible sessions for {sport} the {session_date} : {e}", logging.ERROR)
        return []

def book_session(session_id):
    # to NS, book a session by id
    params = {'classId': session_id}
    q = query_from_tpl(queries.BookCampusSportClass, params, defaults=False)
    resp = requests.post(url_post_to(), data=q, headers=form_headers())
    try:
        resp.raise_for_status()
        return resp.json()['data']['bookCampusSportClass']
    except requests.exceptions.HTTPError as e:
        log_all(f"Error booking with the id {session_id} : {e}", logging.ERROR)
        return {}

def validate_booked(response_booking, sport):
    global booked

    if response_booking and response_booking.get('isBooked'):
        booked[sport] = booked.get(sport, []) + [response_booking['classId']]
        return f"BOOKED {response_booking['classId']}"
    return f"Wasn't able to book the session, maybe already booked for this sport the same day (response: {response})"

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
        log_all(f" [{sport}]   Dates for which we would check sessions : {matches}")
        for matching_date, query_sessions in matches.items():
            sessions_at_date = get_sessions_at_date(sport, matching_date)
            log_all(f" | Found {len(matching_date)} possible sessions the {matching_date} matching day {query_sessions}")
            log_all(f" | Sessions details : {NEWLINE.join(matching_date)}", logging.DEBUG)
            sessions_matches = matching_sessions_at_date(sessions_at_date, query_sessions)
            log_all(f" | Selected {len(sessions_matches)} sessions the {matching_date} matching hours {query_sessions}")
            log_all(f" | Selected sessions ids : {sessions_matches}")
            for session_hour, session_id in sessions_matches.items():
                if sport_query['autobooking']:
                    log_all(f" | BOOKING : Prepare to book session of {sport} at {session_hour} (id {session_id})")
                    response_booking = book_session(session_id)
                    result_booking = validate_booked(response_booking, sport)
                    log_all(f" | Result for booking at {session_hour} : {result_booking}")


def process(given_interval=None):
    global config, interval

    max_interval = max(MIN_INTERVAL+5, config['max_interval'])
    wait_next_hour, to_wait = close_to_new_hour(max_interval)
    log_all(f"NEW ITERATION at {datetime.datetime.now()}")
    if wait_next_hour:
        log_all(f"We will wait {to_wait}s until next hour ...")
        sleep(to_wait + 10)
    else:
        interval = given_interval if given_interval else randint(MIN_INTERVAL, max_interval)
        log_all(f"Wait a random amount of time : {interval}")
        sleep(interval)
    log_all(f"LAUNCH CHECKING at {datetime.datetime.now()}")
    iteration_check(config['param_queries'])


if __name__ == '__main__':
    global config, interval, booked

    config = {}
    interval = MIN_INTERVAL
    booked = {}

    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("-c", "--config", default="config.json", help="A JSON file containing config and sport sessions parameters")
    parser.add_argument("-p", "--port", type=int, default=8080, help="The port on which query the local HTTP server serving current auth token")
    parser.add_argument("-i", "--interval", type=int, default=None, help="Give a fixed interval between checking iterations, instead of random considering max in config")
    args_cli = parser.parse_args()

    try:
        config = json.loads(Path(args_cli.config).read_text())
    except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
        print(f"An error was raised when trying to read config file {args_cli.config} :", e)
        sys.exit(1)

    setup_logging()

    try:
        while True:
            process(args_cli.interval)
    except KeyboardInterrupt:
        log_all(f"Checker stopped. Managed to book following classes :\n{booked}")
