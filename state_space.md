# State Space

## Vragen

1. $$\frac{20!}{(20 - 12)!} = 6.03 \cdot 10^{13}$$
2. $$3^{20} = 3.49 \cdot 10^{9}$$
3. $$\frac{(25 + 3 - 1)!}{25! \cdot (3 - 1)!} = 351$$
4. $$\frac{110!}{30! \cdot (110 - 30)!} + \frac{110!}{31! \cdot (110 - 31)!} + \frac{110!}{32! \cdot (110 - 32)!} = 8.33 \cdot 10^{27}$$
5. $$\left(\frac{26!}{(26 - 7)!}\right)^{-1}$$
6. $$\sum_{r=15}^{45} \frac{(r + 2 - 1)!}{r! \cdot (2 - 1)!} = 961$$
7. 
    * Chips and Circuits <br><br>

    * Hoeveelheid gates, verbindingen tussen gates (nets), alle locaties van de gates en grootte (+ dimensie) van de grid, hoeveelheid verbindingen tussen de gates, lengte van de kabels tussen gates, hoeveelheid kruisingen (intersections). <br><br>

    * Aantal gates niet groter dan oppervlakte grid, locatie gates zijn uniek, alle gates zijn juist met elkaar verbonden (volgens de netlist), maximaal aantal kabels is de hele oppervlakte van de grid en de minimale afstand tussen alle gates is ook het minimale aantal kabels. <br><br>

    * $3^{2rk - (r + k)} - 3^{N_{min}}$, waar $r =$ aantal rijen, $k =$ aantal kolomen en $N_{min} =$ minimale lengte van alle gate connecties (dus minimale aantal kabels voor een gegeven configuratie). <br><br> $N_{min} = \sum_{i, j} \sum_{k = 1}^{dim} |(\vec{r_i} - \vec{r_j})_k|$,
    waar i en j een combinatie uit de netlist is en de binnenste som alle componenten van de vector sommeert. (Dus in 2D is dit ∆x + ∆y van de twee gate coördinaten) <br><br>

    * Stel we hebben een 3x3 met gates op $(0, 0)$ en $(2, 2)$. Dan is de maximale bekabeling: $2 \cdot 3 \cdot 3 - (3 + 3) = 12$ en de minimale afstand is $4$. <br><br>De bovengrens zou dan volgens de formule zijn: $3^{12} - 3^{4-1} = 531 414.$ <br><br>In dit voorbeeld hebben wij 11 mogelijke paden geteld. <br><br>De bovengrens is dus in iedergeval boven de werkelijke aantal opties, maar waarschijnlijk zouden er nog meer aannames in verwerkt kunnen worden om de bovengrens te verkleinen. <br><br>

    * Voor het voorbeeld van Chips & Circuits: $r = 7, k = 8, N_{min} = 20$, dus <br><br>$$\text{Bovengrens} = 3^{2 \cdot 7 \cdot 8 - (7 + 8)} - 3^{20 - 1} \approx 1.91 \cdot 10^{46}$$ <br><br>


## State Space uitleg

Statespace tekst verder uitgewerkt: 

Het probleem: vind de optimale configuratie aan kabels (laagste kosten op basis van kosten kabel: 1; kosten kortsluiting: 300) die alle gates aan elkaar verbindt volgens de netlist (constraint optimization problem).

Het lastige aan de statespace van dit probleem is dat wanneer we constraint versoepelen (kabels mogen over elkaar heenlopen) de statespace oneindig groot wordt, omdat er altijd een kabel aan elke configuratie kan worden toegevoegd.

De aanname die wij hebben gedaan in het toch proberen te berekenen van de statespace is dat er een vaste dimensie is van de grid waarin de bekabeling zich moet bevinden: $r = \text{rijen}$, $k = \text{kolommen}$, dat de kabel elk van de punten op de grid raakt. Op deze manier weten we dat dit de maximale kabellengte is waarop elke gate met elk andere gate in verbinding kan staan, en dus dat er in deze maximale ruimte een geldige oplossing moet zijn te vinden. 

Als we een kabel aanleggen kunnen we $3$ richtingen kiezen, links, rechtdoor of rechts. Hierdoor bestaat de keuzeruimte uit drie, en de maximale lengte is wanneer op alle mogelijke plekken in de $r \times k$ grid er kabel ligt: dit is "kabel van rijen + kabel van kolommen" ofwel $(r - 1) \cdot k + (k - 1)\cdot r$. Als we deze lengte hebben bereikt dan weten we zeker dat alle gates met elkaar verbonden zijn aangezien alles met elkaar verbonden is, en we weten ook zeker dat de kabel niet langer kan zijn dan deze lengte aangezien er dan kabels over hetzelfde lijnstuk lopen wat niet toegestaan is. Het aantal mogelijkheden van de legging van de kabel van maximale lengte is daarom: $3^{(r-1) \cdot k + (k - 1) \cdot r}$

Alleen de oplossing van het probleem hoeft niet perse een kabel te zijn van maximale lengte, hij kan ook $1$, $2$ of $10$ kabelstukken korter zijn, hij kan zo kort zijn als de korste kabel configuratie mogelijk, dat is de delta's van de coördinaten van de verbonden gates bij elkaar opgeteld, de hypothetisch korst mogelijk (en waarschijnlijk onjuiste) oplossing van dit probleem. In deze span bevindt onze oplossing zich en dit is de totale statespace van dit probleem: $\sum_{i=N_{min}}^{(r - 1) \cdot k + (k - 1) \cdot k} 3^{i}$

Dat is dus de volgende reeks: 

$$3^{(r - 1) \cdot k + (k - 1) \cdot r} + 3^{(r - 1) \cdot k + (k - 1) \cdot r - 1} + 3^{(r - 1) \cdot k + (k - 1) \cdot r - 2} + ... 3^{N_{min} + 1} + 3^{N_{min}}$$

<br>

Het is dus duidelijk dat wanneer de dimensies van de grid vergroot worden, de statespace gigantisch toeneemt:

$$3 \times 3 = 3^{2*3 + 2*3} + 3^(2*3 + 2*3 - 1) + 3^(2*3 + 2*3 - 2) + ... >= 767637$$
$$3 \times 4 = 3^{2*4 + 3*3} + 3^{2*4 + 3*3 - 1} + 3^{2*4 + 3*3 - 2} + ... >= 186535791$$
$$4 \times 4 = 3^{3*4 + 3*4} + 3^{3*4 + 3*4 - 1} + 3^{3*4 + 3*4 - 2} + ... >= 407953774917$$

<br>

$$7 \times 8 = 3^{6 \cdot 8 + 7 \cdot 7} + 3^{6 \cdot 8 + 7 \cdot 7 - 1} + 3^{6 \cdot 8 + 7 \cdot 7 - 2} + ... \geq 2.7571 \cdot 10^{46} \ \ \text{(example question)}$$
$$17 \times 12 = 3^{16 \cdot 12 + 17 \cdot 11} + 3^{16 \cdot 12 + 17 \cdot 11 - 1} + 3^{16 \cdot 12 + 17 \cdot 11 - 2} + ... \geq 9.7422 * 10^{180} \ \ \text{(Chip 1)}$$
$$17 \times 16 = 3^{16 \cdot 16 + 17 \cdot 15} + 3^{16 \cdot 16 + 17 \cdot 15 - 1} + 3^{16 \cdot 16 + 17 \cdot 15 - 2} + ... \geq 9.3038 * 10^{243} \ \ \text{(Chip 2)}$$


Note: Deze berekeningen houden geen rekening met een statespace in 3D, dit zal voor een nog grotere statespace zorgen. 

