# checkNovaSport
Automate booking of sport sessions on NovaSport website - be first, be smart

Requirements :
- Firefox with a userscript manager like [ViolentMonkey](https://violentmonkey.github.io/) and an account on [Nova Sport website](https://login.novasport.be/)
- Python 3.7 or higher
- A clone of this repo with sport lessons adapted to you needs in [config file](./config.json)

The tool splits the work on 3 parts :
1. A browser userscript running on the https://login.novasport.be/ webpage, refreshing and pushing the current auth token to a local HTTP server (2.)
2. An HTTP server serving userscript to have fast integration and the current token to identify user. Run by default on port 8080 :
   - Current auth token : http://localhost:8080/token
   - The userscript to install : http://localhost:8080/NovaSportAutoCheck.user.js (visit it with ViolentMonkey installed to integrate it directly)
3. A NovaSport checker instance constantly monitoring targeted available sport sessions, able to notify about/automatically book one as long as there is a free place

These can be launched separately or at once simply with
```
./start.py [arguments, see -h to get a list]
```
