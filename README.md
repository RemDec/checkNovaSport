# checkNovaSport
Automate booking of sport sessions on NovaSport website - be first, be smart

Requirements :
- Firefox with a userscript manager like [https://violentmonkey.github.io/](ViolentMonkey) and an account on [https://login.novasport.be/](Nova Sport website)
- Python 3.7 or higher
- A clone of this repo with sport lessons adapted to you needs in [config.json](config file)

The tool splits the work on 3 parts :
1. A browser userscript running on the https://login.novasport.be/ webpage, refreshing and pushing the current auth token to a local HTTP server (2.)
2. An HTTP server serving userscript to have fast integration and the current token to identify user
3. A NovaSport checker instance constantly monitoring targeted available sport sessions, able to notify about/automatically book one as long as there is a free place

These can be launched separately or at once simply with
```
./start.py [arguments, see -h to get a list]
```
