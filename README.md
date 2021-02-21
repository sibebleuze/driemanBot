# driemanBot

Een Discord bot om te kunnen driemannen (regels: https://wina-gent.be/drieman.pdf). De regels zijn ook beschikbaar in
het document drieman.pdf.

Om de bot te kunnen runnen, moet je bij de bestanden die eindigen op .example de gegevens invullen die daarin nodig zijn
en de extensie .example weghalen. De bestanden in de map pictures kan je vervangen door wat je maar wilt, zolang ze er
allemaal zijn (zonder .example extensie) loopt de bot zonder problemen. Als dit allemaal ingevuld is, zou het
commando ```python3 bot.py``` zonder problemen moeten kunnen uitgevoerd worden.

De versies van dependencies beschreven in requirements.txt zijn niet per se de enige versies die werken, het zijn echter
de versies die ik had staan op moment van programmeren, dus deze werken zeker.

Gebruikte packages zijn o.a. discord, dotenv en os om te verbinden met de Discord API en de Discord token in te lezen
uit .env, traceback en datetime om getimestampede errors weg te schrijven, sys en importlib om zonder onderbreking
(van het python script, de bot wordt wel herstart) aanpassingen te kunnen inladen, gc om garbage collection te doen en
numpy.random om dobbelstenen te simuleren.