# driemanBot

Een Discord bot om te kunnen driemannen (regels: https://wina-gent.be/drieman.pdf). De regels zijn ook beschikbaar in
het document drieman.pdf.

Om de bot te kunnen runnen, moet je een bestand .env aanmaken en hierin de regel
```DISCORD_TOKEN=Nzg0NTAxNjAzNjQ1NjUzMDE4.X8qODQ.ZnHVnFEstq1qeF-vgW9U89Z1evk```
invullen, waarbij je dit voorbeeld token vervangt door het correcte Discord token uit de Discord Developer Portal.
Daarna kan je ```python3 bot.py``` uitvoeren.

De versies van dependencies beschreven in requirements.txt zijn niet per se de enige versies die werken, het zijn echter
de versies die ik had staan op moment van programmeren, dus deze werken zeker.

Gebruikte packages zijn o.a. discord, dotenv en os om te verbinden met de Discord API en de Discord token in te lezen
uit .env, traceback en datetime om getimestampede errors weg te schrijven, sys en importlib om zonder onderbreking
aanpassingen te kunnen inladen, gc om garbage collection te doen en numpy.random om dobbelstenen te simuleren.