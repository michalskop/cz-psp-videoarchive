Následující text je automatický přepis záznamu z jednání Poslanecké sněmovny. Přepis obsahuje chyby: chybějící diakritika, useknutá slova, občasné halucinace (opakující se nesmyslné fráze). Ignoruj tyto artefakty a soustřeď se na srozumitelný obsah.

Vytvoř strukturované shrnutí v češtině. Buď konkrétní a podrobný — shrnutí musí zachytit všechny identifikované řečníky, konkrétní čísla, návrhy a argumenty. Délka odpovídá bohatosti obsahu, ne pevnému limitu.

1. **Téma a účel jednání** — o čem jednání bylo, jaký byl jeho cíl (jeden až dva odstavce)

2. **Hlavní body** — pro každého identifikovaného řečníka samostatná odrážka ve formátu:
   **Jméno (instituce/strana)** — konkrétní argumenty, čísla, návrhy nebo rozhodnutí, která prezentoval. `[N/MM:SS]`
   kde `[N/MM:SS]` je číslo části přepisu a nejbližší časová značka ze začátku projevu daného řečníka (stejný formát jako u citací). Pokud nelze určit, neuváděj nic.
   Přidej i tematické body, které nelze přiřadit jednomu řečníkovi.
   Nehalucinuj — pokud jméno nelze určit, napiš „neidentifikovaný řečník".

3. **Výsledek / závěr** — co bylo rozhodnuto, dohodnuto nebo odloženo; pokud nebyl formální výsledek, popiš konsenzus nebo dominující postoje

4. **Poznámky** — pokud jsou části přepisu nesrozumitelné nebo chybí části záznamu, uveď to

---

## Doplňující otázky

- Zaznělo něco kontroverzního? Pro každý kontroverzní výrok nebo návrh uveď:
  - **Kdo** to říkal (jméno, instituce/strana)
  - **Co přesně** bylo řečeno nebo navrhováno
  - **Proč je to kontroverzní** nebo politicky citlivé
  - **Čas** — číslo části přepisu a nejbližší časová značka `[MM:SS]`; formát: `N/MM:SS` (příklad: `3/04:23`)

---

## Klíčové citace pro veřejnost

Vyber 3–5 nejdůležitějších výroků vhodných pro sdílení na sociálních sítích. Každý výrok musí být přibližně jedna věta. Preferuj tvrdá data a konkrétní čísla — výroky, které samy o sobě něco sdělují bez dalšího kontextu.

Pro každý výrok uveď:
- **Text** — přesná citace nebo parafrá ze (vyznač, o který typ jde)
- **Řečník** a jeho **afiliace** (strana nebo instituce)
- **Čas** — číslo části přepisu (Část N) a nejbližší `[MM:SS]` značka z textu přepisu; formát: `N/MM:SS` (příklad: `1/04:03`). Pokud časovou značku nelze určit, uveď `null`.

---

## JSON výstup

Po shrnutí vlož JSON blok v následujícím formátu. Všechna textová pole vyplň v češtině.
Metadata (`event`, `transcription`) přečti z hlavičky přepisu (tabulka na začátku souboru).
Pokud hodnotu nelze z přepisu určit, použij `null`.

**Zásadní pravidlo:** Textová pole v `summary` a `controversial` jsou Markdown řetězce — zkopíruj do nich celý obsah odpovídající části shrnutí výše (odstavce, tučné formátování, odrážky, vnořené odrážky), nikoli zkrácenou jednovětou verzi. JSON je strojově čitelná kopie lidsky čitelného shrnutí, ne jeho ochuzená verze.

```json
{
  "schema_version": "2",
  "created_at": null,
  "model_hint": null,
  "event": {
    "id": "<ID z hlavičky>",
    "name": "<název akce z hlavičky>",
    "classification": "<kategorie z hlavičky, např. Kulatý stůl>",
    "start_date": "<YYYY-MM-DDTHH:MM nebo YYYY-MM-DD>",
    "end_date": "<YYYY-MM-DDTHH:MM nebo null>",
    "sources": []
  },
  "transcription": {
    "parts_transcribed": <číslo>,
    "parts_total": <číslo>,
    "source": "<whisper | captions | groq | mixed>",
    "model": "<název modelu nebo null>"
  },
  "summary": {
    "topic": "<Markdown — celý text oddílu 'Téma a účel jednání', zachovej odstavce a formátování>",
    "main_points": [
      "<Markdown — každá odrážka z oddílu 'Hlavní body' jako samostatný prvek pole; může obsahovat tučná jména, vnořené odrážky apod.>"
    ],
    "outcome": "<Markdown — celý text oddílu 'Výsledek / závěr', zachovej odstavce, odrážky a formátování>",
    "notes": "<Markdown — celý text oddílu 'Poznámky'; null pokud oddíl chybí nebo je prázdný>"
  },
  "entities": {
    "speakers": [
      {"name": "<jméno>", "person_id": null, "affiliation": "<strana nebo instituce nebo null>"}
    ],
    "parties": ["<název strany>"],
    "institutions": ["<název instituce>"]
  },
  "highlights": [
    {
      "text": "<jedna věta — přesná citace nebo parafrá ze>",
      "type": "<citation | paraphrase>",
      "speaker": "<jméno nebo null>",
      "affiliation": "<strana nebo instituce nebo null>",
      "timestamp": "<formát N/MM:SS, např. '1/04:03', nebo null>",
      "screenshot_path": null
    }
  ],
  "controversial": [
    {
      "statement": "<Markdown — celý text dané odrážky z oddílu 'Doplňující otázky', zachovej formátování>",
      "speaker": "<jméno nebo null>",
      "affiliation": "<strana nebo instituce nebo null>",
      "timestamp": "<formát N/MM:SS, nebo null>",
      "screenshot_path": null
    }
  ],
  "quality": {
    "transcript_quality": "<good | partial | poor>",
    "unintelligible_parts": <true | false>
  },
  "extras": null
}
```
