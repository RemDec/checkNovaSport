script = """\
// ==UserScript==
// @name        NovaSportAutoCheck
// @namespace   Violentmonkey Scripts
// @match       https://login.novasport.be/
// @grant       none
// @version     1.0
// @author      -
// @description 02/11/2021, 20:41:55
// ==/UserScript==


const STORAGE_KEY = "CognitoIdentityServiceProvider.68majga0ulte4tt8tmpismer85.%(email)s.idToken";
const URL = "http://localhost:%(port)s/token";
const INTERVAL = %(interval)s * 60 * 1000;

function getAuthToken() {
  return localStorage.getItem(STORAGE_KEY);
}

async function postToken(tokenValue) {
  const request = {
    method: 'POST',
    headers: new Headers({'content-type': 'application/json'}),
    body: JSON.stringify({token: tokenValue})
  };
  const resp = await fetch(URL, request);
  const json_resp = await resp.json();
  console.log(json_resp);
}

function processToken() {
  var token = getAuthToken();
  console.log('Token to POST', token);
  postToken(token);
  setTimeout(() => location.reload(), INTERVAL);  // This will relaunch this whole script !
}

function process() {
  setTimeout(processToken, 3000);  // Wait a bit to be sure token was refreshed at page reload if needed
}

process();

"""
