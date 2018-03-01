Unser System besteht aus:

1. Einer selbst gebauten Mechanik
2. Einem Arudino
    * der den Motor steuert
3. Einem Raspberry Pi
    * liest RFID-Tag aus
    * gleicht Tag mit Datenbank ab
    * gibt Signal an den Raspberry zum Öffnen des Fensters

Auf dem Raspberry laufen zwei Systeme:

* [Roseguarden](https://github.com/mdrobisch/roseguarden), ein RFID-System mit Datenbank und Web-Interface
* [Node-Red](https://nodered.org/) flows für einen Telegram-Bot, der über den Öffnungszustand informiert
    
# Konfiguration

## Roseguarden Konfiguration

Die Web-Oberfläche von Roseguarden ist erreichbar unter `<ip-im-lan>:8000`.

## Node-Red Konfiguration

Node-Red ist erreichbar unter `<ip-im-lan>:1880`. Um die Flows zu bearbeiten muss ein Passwort eingegeben werden.
