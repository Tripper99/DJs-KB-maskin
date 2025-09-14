# DJs KB-maskin

[![Version](https://img.shields.io/badge/version-1.7.4-blue.svg)](https://github.com/Tripper99/DJs-KB-maskin/releases)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

En specialiserad Python-applikation för hantering av tidningsfiler från "Svenska Tidningar" - utvecklad för Kungliga Biblioteket (KB).

## Översikt

DJs KB-maskin är ett GUI-baserat verktyg som automatiserar nedladdning och bearbetning av digitaliserade tidningsskanningar. Applikationen har två huvudfunktioner:

1. **Gmail JPG-nedladdare** - Laddar ner JPG-bilagor från Gmail med hjälp av Gmail API
2. **KB-filbearbetare** - Konverterar JPG-filer till PDF:er med meningsfulla namn och slår samman flersidiga artiklar

## Funktioner

- 📧 **Gmail-integration** - OAuth-autentisering och automatisk nedladdning av bilagor
- 📄 **Smart PDF-konvertering** - Automatisk namngivning baserad på tidningskoder
- 🗂️ **CSV-baserad mappning** - Använder CSV-filer för bib-kod till tidningsnamn
- 🔄 **Uppdateringssystem** - Automatisk kontroll av nya versioner via GitHub
- 🛡️ **Säkerhet** - Omfattande vägvalidering och säkra filoperationer
- 🇸🇪 **Svenskt gränssnitt** - Komplett lokalisering på svenska
- ⚡ **Responsivt** - Bakgrundstrådar håller gränssnittet responsivt
- 🎯 **Konflikthantering** - Interaktiva dialoger för hantering av befintliga filer

## Installation

### Windows Installer
1. Ladda ner senaste `DJs_KB_maskin_vX.X.X_setup.exe` från [Releases](https://github.com/Tripper99/DJs-KB-maskin/releases)
2. Kör installationsprogrammet
3. Följ instruktionerna.


### Gmail-nedladdning
1. Välj "Gmail jpg-bilage nedladdning" i gränssnittet
2. Ange e-postadress och lösenord (app-specifikt lösenord för Gmail)
3. Välj datumintervall för sökning
4. Klicka "Kör igång" för att starta nedladdningen

### KB-filbearbetning
1. Välj "KB filkonvertering" i gränssnittet
2. Välj mapp med JPG-filer att bearbeta
3. Välj utdatamapp för PDF:er
4. Klicka "Kör igång" för att starta konverteringen

### Filnamnkonventioner
- **Indata JPG**: `bib{kod}_{datum}_{sekvens}.jpg`
- **Omdöpta JPG**: `{datum} {tidning} {bib} {nummer}.jpg`
- **Utdata PDF**: `{datum} {tidning} ({sidor} sid).pdf`

## Projektstruktur

```
DJs_KB_maskin/
├── app.py                 # Huvudingångspunkt
├── src/                   # Källkod
│   ├── gmail/            # Gmail API-integration
│   ├── kb/               # KB-filbearbetning
│   ├── gui/              # Användargränssnitt
│   ├── security/         # Säkerhetsmoduler
│   ├── update/           # Uppdateringssystem
│   └── version.py        # Versionshantering
├── build-tools/          # Byggverktyg
│   ├── pyinstaller/      # PyInstaller-konfiguration
│   ├── inno-setup/       # Inno Setup-skript
│   └── scripts/          # Byggskript
├── tests/                # Testsvit
├── docs/                 # Dokumentation
└── requirements.txt      # Python-beroenden
```

## Utveckling

## Versionshistorik

### v1.7.4 (2025-09-10)
- Buggfix: "Skriv över alla" fungerar nu korrekt över flera filkonflikter

### v1.7.0 (2025-09-10)
- Stor uppdatering: Ersatte Excel med CSV för bib-koduppslag
- Förenklat gränssnitt och minskade beroenden

Se [DEVELOPMENT_HISTORY.md](DEVELOPMENT_HISTORY.md) för fullständig historik.

## Licens

Detta projekt är licensierat under MIT-licensen - se [LICENSE](LICENSE) för detaljer.

## Upphovsman

Dan Josefsson - dan@josefsson.net

## Erkännanden

- Utvecklad med hjälp av Claude Code, Grok och Cursor
- Använder [ttkbootstrap](https://github.com/israel-dryer/ttkbootstrap) för modernt GUI
- Google Gmail API för e-postintegration

## Support

För problem eller frågor, vänligen öppna ett [GitHub Issue](https://github.com/Tripper99/DJs-KB-maskin/issues).

## Skärmdumpar

*Kommer snart*

---

**Notera**: Denna applikation är specifikt utvecklad för arbete med filer hämtade från databasen Svenska tidningar (Kungliga biblioteket) och gränssnittet är helt på svenska.