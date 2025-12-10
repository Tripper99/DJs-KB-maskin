Om DJ:s KB-maskin

![Skärmbild 2025-12-03 084223](https://github.com/user-attachments/assets/ccb4ca1e-e5a6-497d-bccb-c85c03ab7a92)

Detta windows-program (finns i nuläget inte till Mac) är skapat för att förenkla tillvaron för oss som brukar ladda ned större mängder tidningssidor från Kungliga Bibliotekets databas Svenska Tidningar. Deras system funkar så att du från en skärm på KB skicka jpg-bilder av tidningssidor till dig själv via mejl. Varje enskild jpg skicks som bilaga i ett separat mejl. Du måste sedan öppna ditt mejlprogram och spara ned alla jpg-bilagorna en och en. Vanligen vill du också döpa om filerna eftersom de är namngivna med en lång kod istället för tidningsnamn. För att kunna arbeta med filerna vill du antagligen också konvertera bilderna till pdf, och slå samman flersidiga artiklar till flersidiga pdf-filer. Alla som gått igenom denna process med 500 jpg-bilagor (maxantalet som kan skickas från KB under en session) vet att det kan ta väldigt lång tid.
Det är här DJ:s KB-maskin kommer in i bilden.
För att använda appen behöver du först koppla ett Gmail-konto till ditt konto på Svenska Tidningar. Då kan appen automatiskt koppla upp sig till gmailkontot via API och hämta ned samtliga jpg-filer som kommit från KB inom ett tidsspann som du själv bestämmer. Appen konverterar automatiskt jpg-bilderna pdf:er, slår samma flersidiga artiklar, samt ger filerna begripliga namn bestående av datum för publicering, tidningsnamn samt sidantal.

Exempel
Låt oss säga att du hämtat hem dessa fyra filer, som alltså anländer i vars ett mail från KB:
bib4345612_19850708_10985_181_0001.jpg
bib4345612_19850708_10985_181_0007.jpg
bib4345612_19850708_10985_181_0008.jpg
bib4345612_19850708_10985_181_0009.jpg

DJ:s KB-maskin hämtar automatiskt hem filerna utan att du ens behöver öppna Gmail, och skapar denna fil av dem:

1985-07-08 AFTONBLADET (4 sid).pdf

Specialfunktiner
Under konverteringsprocessen döper appen om jpg-filerna till begripliga namn, varefter de konverteras till pdf. Som standard raderas de omdöpta jpg-bilderna men du kan även välja att spara dem. Detta kan t ex vara vara bra om en redigerare vill använda tidningssidorna som jpg i teve- eller tidningsproduktion och då vill slippa konvertera tillbaka från pdf-format.

Exempel
Om du i exemplet ovan väljer att även spara de omdöpta jpg-filerna så kommer appen att producera dessa filer:
1985-07-08 AFTONBLADET (4 sid).pdf
1985-07-08 AFTONBLADET bib4345612 10985_181_0001.jpg
1985-07-08 AFTONBLADET bib4345612 10985_181_0007.jpg
1985-07-08 AFTONBLADET bib4345612 10985_181_0008.jpg
1985-07-08 AFTONBLADET bib4345612 10985_181_0009.jpg

Tips för ökad säkerhet
Det rekommenderas starkt att du skapar en ny gmail-adress som bara används tillsammans med Svenska Tidningar. Du måste nämligen ge appen rättigheter att läsa Gmail-kontot via API. Appen kan i och för sig inte göra något annat än spara ned jpg-bilagor från den avsändare som du själv anger, så säkerhetsrisken är minimal. Men det är ändå klokt att inte öppna ditt vanliga gmail-konto för API-access i onödan.

Tips för ännu bättre arbetsflöde
DJ:s KB-maskin har en syster-app som heter DJ:s Timeline-maskin. Den är skapad för journalist, forskare och researchers som gillar att organisera sin research i form av timelines i excel. DJ:s Timeline-maskin är ett verktyg som låter dig snabbt och effektivt lägga till rader i din timeline utan att du behöver redigera excel-dokumentet manuellt. DJ:s Timeline-maskin arbetar mycket effektivt med pdf:er som skapats med hjälp av DJ:s KB-maskin.

DJ:s KB-maskin är skrivet i Python av journalisten Dan Josefsson 2025, som själv använder appen flitigt i sitt jobb.
Rapportera gärna buggar till dan@josefsson.net.
Python-kodningen är gjord med assistans av Claude Code.
Alla användning av programmet sker på egen risk.
