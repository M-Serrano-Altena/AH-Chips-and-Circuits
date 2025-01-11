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

    * $3^{2rk - (r + k)} - 3^{L_{min}}$, waar $r =$ aantal rijen, $k =$ aantal kolomen en $L_{min} =$ minimale lengte van alle gate connecties (dus minimale aantal kabels voor een gegeven configuratie). <br><br> $L_{min} = \sum_{i, j} \sum_{k = 1}^{dim} |(\vec{r_i} - \vec{r_j})_k|$,
    waar i en j een combinatie uit de netlist is en de binnenste som alle componenten van de vector sommeert. (Dus in 2D is dit ∆x + ∆y van de twee gate coördinaten) <br><br>

    * Stel we hebben een 3x3 met gates op $(0, 0)$ en $(2, 2)$. Dan is de maximale bekabeling: $2 \cdot 3 \cdot 3 - (3 + 3) = 12$ en de minimale afstand is $4$. <br><br>De bovengrens zou dan volgens de formule zijn: $3^{12} - 3^{4-1} = 531 414.$ <br><br>In dit voorbeeld hebben wij 11 mogelijke paden geteld. <br><br>De bovengrens is dus in iedergeval boven de werkelijke aantal opties, maar waarschijnlijk zouden er nog meer aannames in verwerkt kunnen worden om de bovengrens te verkleinen. <br><br>

    * Voor het voorbeeld van Chips & Circuits: $r = 7, k = 8, L_{min} = 20$, dus <br><br>$$\text{Bovengrens} = 3^{2 \cdot 7 \cdot 8 - (7 + 8)} - 3^{20 - 1} \approx 1.91 \cdot 10^{46}$$ <br><br>


## State Space uitleg

Het probleem: vind de optimale configuratie aan kabels (laagste kosten op basis van kosten kabel: 1; kosten kortsluiting: 300) die alle gates aan elkaar verbindt volgens de netlist (constraint optimization problem).

Het lastige aan de statespace van dit probleem is dat wanneer we constraint versoepelen (kabels mogen over elkaar heenlopen) de statespace oneindig groot wordt, omdat er altijd een kabel aan elke configuratie kan worden toegevoegd.

Om toch een eindige statespace te krijgen, hebben wij een paar aannames gemaakt. Als eerst hebben we de grid waarin de kabels zich kunnen bevinden eindig gemaakt (met een dimensie van $r \times k$, waarbij $r = \text{rijen}$, $k = \text{kolommen}$). Verder beschouwen wij de bovengrens van het aantal kabels als de hele grid vol is met kabels, ookal is het nooit mogelijk om dit te bereiken vanuit $1$ kabel zonder overlap. Maar op deze manier weten we dat dit de maximale kabellengte is waarop elke gate met elk andere gate verbonden is. De optimale oplossing zal dan dus niet langere kabels hebben dan deze maximale lengte ($L_{max}$). 

Als we een kabel aanleggen kunnen we $3$ richtingen kiezen: links, rechtdoor of rechts. Hierdoor bestaat de keuzeruimte uit drie opties, en de maximale lengte is wanneer op alle mogelijke plekken in de $r \times k$ grid er kabel ligt. De totale lengte van de kabels wordt dan: 

$$\boxed{L_{max} = (r - 1) \cdot k + (k - 1)\cdot r = 2rk - (r + k)}$$

Als we deze lengte hebben bereikt dan weten we zeker dat alle gates met elkaar verbonden zijn aangezien alles met elkaar verbonden is. Ook weten we zeker dat de kabel niet langer kan zijn dan deze lengte. Er zouden dan namelijk kabels over elkaar moeten lopen, en dit is niet toegestaan. Het aantal mogelijkheden kabel paden die van maximale lengte is daarom: 

$$\text{state space (alleen max kabels)} = 3^{2rk - (r + k)}$$

Maar dit is alleen de state space voor kabels van maximale lengte, terwijl de oplossing van het probleem ook kortere kabels kan hebben. Het korste dat de kabels kunnen zijn is de som van alle afstanden tussen de gates. Want een kortere kabel zou niet alle gates kunnen bereiken en is dus geen geldige oplossing. We kunnen deze minimale afstand als volgt opschrijven:

$$\boxed{L_{min} = \sum_{i, j} \sum_{k = 1}^{dim} |(\vec{r_i} - \vec{r_j})_k|}$$

Hierin is de binnenste som over alle vector componenten tussen twee gates (dus $\Delta x + \Delta y$ in 2D) en de buitenste som over alle gate paren in de netlist. <br><br>

We weten dus dat de optimale oplossing een kabel lengte tussen $L_{min}$ en $L_{max}$ moet hebben. De totale state space ($\Omega$) kunnen dus bepalen met de volgende formule:

$$\boxed{\Omega = \sum_{i=L_{min}}^{L_{max}} 3^{i}}$$

<br><br>

Als we alleen de laatste $3$ termen van $\Omega$ berekenen (dus als $L_{min} = L_{max} - 3$, wat een extreem hoge $L_{min}$ is) voor verschillende grid groottes, dan zien we dat de state space gigantisch toeneemt: <br><br>

$$\Omega_{3 \times 3} = 3^{2 \cdot 3 \cdot 3 - (3 + 3) - 2} + 3^{2 \cdot 3 \cdot 3 - (3 + 3) - 1} + 3^{2 \cdot 3 \cdot 3 - (3 + 3)} = 7.7 \cdot 10^{5}$$
$$\Omega_{3 \times 4} = 3^{2 \cdot 3 \cdot 4 - (3 + 4) - 2} + 3^{2 \cdot 3 \cdot 4 - (3 + 4) - 1} + 3^{2 \cdot 3 \cdot 4 - (3 + 4)} = 1.9 \cdot 10^{9}$$
$$\Omega_{4 \times 4} = 3^{2 \cdot 4 \cdot 4 - (4 + 4) - 2} + 3^{2 \cdot 4 \cdot 4 - (4 + 4) - 1} + 3^{2 \cdot 4 \cdot 4 - (4 + 4)} = 4.1 \cdot 10^{11}$$

<br>

$$\Omega_{7 \times 8} = 3^{2 \cdot 7 \cdot 8 - (7 + 8) - 2} + 3^{2 \cdot 7 \cdot 8 - (7 + 8) - 1} + 3^{2 \cdot 7 \cdot 8 - (7 + 8)} =  2.8 \cdot 10^{46} \ \ \text{(example question)}$$
$$\Omega_{12 \times 17} = 3^{2 \cdot 12 \cdot 17 - (12 + 17) - 2} + 3^{2 \cdot 12 \cdot 17 - (12 + 17) - 1} + 3^{2 \cdot 12 \cdot 17 - (12 + 17)} = 9.7 \cdot 10^{180} \ \ \text{(Chip 1)}$$
$$\Omega_{16 \times 17} = 3^{2 \cdot 16 \cdot 17 - (16 + 17) - 2} + 3^{2 \cdot 16 \cdot 17 - (16 + 17) - 1} + 3^{2 \cdot 16 \cdot 17 - (16 + 17)} = 9.3 \cdot 10^{243} \ \ \text{(Chip 2)}$$

<br><br>

En deze berekeningen zijn in 2D. In 3D wordt de maximale kabel lengte ($L_{max}$) een stuk groter. De algemene formule is:

$$L_{max} = (r - 1) \cdot k \cdot h + r \cdot (k - 1) \cdot h + r \cdot k \cdot (h - 1)$$

Bij onze chips staat de grid hoogte vast, namelijk $h = 8$. Als we dit invullen en versimpelen vinden we uiteindelijk:

$$\boxed{L_{max} = 23rk - 8(r + k)}$$

<br>

Om een idee te geven van de toename van de state space in 3D is dit de state space van de $3 \times 3$ als we ook kabels tot $8$ hoog mogen zetten:

$$\Omega_{3 \times 3} = 3^{23 \cdot 3 \cdot 3 - 8(3 + 3) - 2} + 3^{23 \cdot 3 \cdot 3 - 8(3 + 3) - 1} + 3^{23 \cdot 3 \cdot 3 - 8(3 + 3)} = 1.1 \cdot 10^{76}$$


