# Evidence entries to verify by hand

These entries in `data/evidence.json` have `"url_confidence": "check"`. Each one points at an organisation's main page (or a page I'm not fully sure of) instead of a specific article. For each: find the exact fact-check or guidance page, paste it into `source_url` (and update `source_title`), then set `url_confidence` to `"high"`.

The 35 `"high"` entries link to well-known WHO fact sheets and the WHO COVID-19 Mythbusters page. Click through them once before demoing too: URLs move.

| id | source_org | current URL | myth |
|---|---|---|---|
| `covid-cow-urine` | MoHFW | https://www.mohfw.gov.in/ | Drinking cow urine or applying cow dung prevents or cures COVID-19. |
| `covid-steam` | PIB Fact Check | https://pib.gov.in/ | Steam inhalation kills the coronavirus in your nose and lungs. |
| `covid-vaccine-infertility` | WHO | https://www.who.int/news-room/questions-and-answers/item/coronavirus-disease-(covid-19)-vaccines | COVID-19 vaccines cause infertility or impotence. |
| `covid-vaccine-microchip` | WHO | https://www.who.int/news-room/questions-and-answers/item/coronavirus-disease-(covid-19)-vaccines | COVID-19 vaccines contain microchips or make your arm magnetic. |
| `onion-fever` | MoHFW | https://www.mohfw.gov.in/ | Putting onion slices in your socks or under your feet draws out fever. |
| `onion-heatstroke` | NCDC | https://ncdc.mohfw.gov.in/ | Keeping an onion in your pocket prevents heatstroke. |
| `conjunctivitis-eye-contact` | NCDC | https://ncdc.mohfw.gov.in/ | Conjunctivitis (eye flu) spreads just by looking into an infected person's eyes. |

Also check the `fact` text of the 7 entries above against whatever page you find. The facts were written from general public-health guidance, not copied from those pages.
