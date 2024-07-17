# RPJ

6/21/2024
Gabauerov napad. Tie notifikacie nie len cez discord ale aj cez normalne SMSku
  - problem je ze nema cifrovanie
  - ale dalo by sa to vyriesit tak ze by som to posielal cez nieco elektricke ako whatsapp
  - a rovno by to islo do mobilu a aj sifrovane

Pozriet sa na Grafanu 
  - incident response maju celkom dobre urobenu
  - pridavanie alertov
  - a rozdelenie na contact pointy
  - ze sa da zaslat rozne notifkacie
  - mozno delit aj podla pritority
      - low,high atd a high posielat na mobil alebo tak
      - a ostatne inde
  - maju to celkom dobre urobene

6/25/2024
  - zaciatok programovania
  - napad ze urobit z toho docker image aby sa to lahsie installovalo/spustalo
  - urobit CLI program ktory bude vypisovat teda CPU, RAM, DISK, usage atd...


7/1/2024
  - pridat nejaku data collection
  - skusit tie usage disclaimers
  - problem ktory ma napadol je ze bude musiet bezat zaroven aj data collection a aj to aby
    sa dali spustat rozne scripts
  - do logov by sa potom pisali vsetky udalosti
  - ale podla toho na ktorej stranke by bol uzivatel podla toho by bolo vykreslovanie grafov
  - lebo tak naco grafy ked proste sa na to nema kto pozerat
  - ale toto s tym oddelenim bude velmi potrebne
  - napriklad pridat nastavenia na to ze co sa vobec loguje a potom zmenit

  - pridala som veci na disk usage
  - skusila pozriet na to runnovanie procesov
  - su na to 2 sposoby subprocess a os ale ten subprocess je better


7/16/2024
  - today I plan on creating basic Flask app for the project
  - also should solve the merge request from PC to notebook
  - created venv for this project
  - decided I will use Django instead of flask
  - performed basic testing database setup


  - idea I got while looking at the documentation is to store the command user adds in a database
  - the layout could me be something like access group command priv needed for the command maybe time stamps
  - also idk if good idea but store the autorun cmds in a DB

7/17/2024
  - begin learning about views
  - add some sample basic database