


# Experiments 



Thanks to:
https://algorithmafternoon.com/books/simulated_annealing/chapter02/



1. Iteratief
--> Eerst overal kabels neer zetten en dan steeds een kabel weghalen en kijken of de state beter is.
    Voordeel: Hoogst waarschijnlijk een goed algoritme om een oplossing te vinden voor een gegeven configuratie.
    Probleem: Het is heel erg onwaarschijnlijk dat de gevonden oplossing optimaal is.

    Om het te kunnen implementeren zou er een hoge cost verbonden moeten zijn wanneer twee gates uit een netlist niet meer verbonden zijn, zodat we de connecties wel overhouden.
    
    Een vervolg op dit Hill Climb algoritme hierboven zou zijn om bijvoorbeeld een temperatuur toe te voegen (Simulated Annealing) of meerdere configuraties te gelijk doen en dan steeds de configuratie met de minste kost kiezen (Population based algorithm).
    We zouden eventueel ook een Genetic algoritme kunnen gebruiken om zoveel mogelijk bij elke gate connectie kijken of we de beste connectie tussen de ouders kunnen bepalen en dat herhalen voor alle kabel connecties. De verschillen tussen de kinderern zouden dan veroorzaakt kunnen worden door verschillende connecties eerst te kiezen wat weer effect heeft op de overige connecties.

2. Constructief

    Beam Search: Is eigenlijk een greedy algoritme, maar dan in plaats van alleen naar de beste state te kijken, kijk je naar de n beste states. Dit zou een grotere kans kunnen geven om toch de optimale oplossing te vinden doordat je naar meer states kijkt in plaats van alleen naar de locaal beste keuze.
    Greedy with Lookahead: Gready algoritme waar je voordat je een keuze maakt n stappen vooruit kijkt en daarvandaan de beste optie kiest gebaseerd op waar je uiteindelijk eindigt. Dit geeft een grotere kans om een meer optimale oplossing te vinden, aangezien het greedy algoritme verder kan kijken en daarmee betere lange-termijn keuzes kan maken.

    We zouden ook beide algoritmes hierboven kunnen combineren door naar de n beste states te kijken, en dat elke beste state is bepaald door vanuit elke state m stappen vooruit te kijken.