# Goal 02 - Extraction Pipeline Validation Report

- Model: gpt-4o-mini
- Target: 50 websites
- Attempted: 70
- Crawled OK: 52
- Passed: 50
- Schema valid: 52/52 crawled (STABLE)
- Target met: yes
- Mean extraction confidence: 0.47
- Tokens: 282150 prompt + 92624 completion
- Est. cost: $0.0979

| # | Domain | Pages | Schema | Svc | Area | Loc | FAQ | Trust | Phone | Conf | Result |
|---|--------|-------|--------|-----|------|-----|-----|-------|-------|------|--------|
| 1 | goettl.com | 6 | ok | 18 | 24 | 3 | 20 | 14 | Y | 0.45 | PASS |
| 2 | parkerandsons.com | 6 | ok | 17 | 49 | 1 | 0 | 29 | Y | 0.45 | PASS |
| 3 | onehourairftworth.com | 6 | ok | 10 | 6 | 4 | 0 | 9 | Y | 0.52 | PASS |
| 4 | aireserv.com | 6 | ok | 8 | 0 | 0 | 4 | 10 | - | 0.47 | PASS |
| 5 | bakerbrothersplumbing.com | 6 | ok | 32 | 68 | 6 | 0 | 10 | Y | 0.45 | PASS |
| 6 | michaelandson.com | 6 | ok | 12 | 5 | 15 | 0 | 10 | Y | 0.51 | PASS |
| 7 | serviceexperts.com | 6 | ok | 31 | 0 | 1 | 10 | 13 | Y | 0.49 | PASS |
| 8 | arsservice.com | 6 | ok | 8 | 0 | 1 | 10 | 7 | Y | 0.38 | PASS |
| 9 | morrisjenkins.com | 5 | ok | 9 | 5 | 1 | 0 | 6 | Y | 0.44 | PASS |
| 10 | fixmyhome.com | 6 | ok | 28 | 11 | 1 | 10 | 11 | Y | 0.52 | PASS |
| 11 | coolray.com | 6 | ok | 20 | 58 | 3 | 14 | 11 | Y | 0.4 | PASS |
| 12 | hellerphc.com | 0 | BAD | - | - | - | - | - | - | - | FAIL (no pages crawled) |
| 13 | bgehome.com | 6 | ok | 23 | 11 | 2 | 0 | 13 | Y | 0.53 | PASS |
| 14 | donnellymech.com | 6 | ok | 23 | 2 | 1 | 0 | 12 | Y | 0.4 | PASS |
| 15 | snellheatingandair.com | 6 | ok | 14 | 24 | 4 | 3 | 10 | Y | 0.55 | PASS |
| 16 | brennanheating.com | 6 | ok | 15 | 10 | 1 | 2 | 5 | Y | 0.56 | PASS |
| 17 | fhfurr.com | 6 | ok | 27 | 14 | 4 | 6 | 13 | Y | 0.49 | PASS |
| 18 | jacksonsfourseasons.com | 0 | BAD | - | - | - | - | - | - | - | FAIL (no pages crawled) |
| 19 | airprosusa.com | 6 | ok | 14 | 17 | 11 | 0 | 10 | Y | 0.51 | PASS |
| 20 | servicechampions.com | 6 | ok | 14 | 20 | 2 | 15 | 19 | Y | 0.5 | PASS |
| 21 | gogreenair.com | 6 | ok | 15 | 1 | 1 | 0 | 9 | Y | 0.45 | PASS |
| 22 | reliablehomecomfort.com | 1 | ok | 0 | 0 | 0 | 0 | 0 | - | - | FAIL (low coverage) |
| 23 | haukeheatingandair.com | 0 | BAD | - | - | - | - | - | - | - | FAIL (no pages crawled) |
| 24 | comfortexperts.com | 0 | BAD | - | - | - | - | - | - | - | FAIL (no pages crawled) |
| 25 | estesservices.com | 0 | BAD | - | - | - | - | - | - | - | FAIL (no pages crawled) |
| 26 | happyhiller.com | 6 | ok | 19 | 5 | 2 | 8 | 7 | Y | 0.47 | PASS |
| 27 | berkeys.com | 6 | ok | 31 | 76 | 2 | 0 | 9 | Y | 0.43 | PASS |
| 28 | hobaica.com | 6 | ok | 20 | 33 | 1 | 4 | 9 | Y | 0.42 | PASS |
| 29 | johnmooreservices.com | 1 | ok | 0 | 0 | 0 | 0 | 0 | - | - | FAIL (low coverage) |
| 30 | abacusplumbing.net | 6 | ok | 30 | 37 | 3 | 1 | 11 | Y | 0.49 | PASS |
| 31 | horizonservices.com | 6 | ok | 33 | 15 | 8 | 1 | 15 | Y | 0.5 | PASS |
| 32 | rotorooter.com | 0 | BAD | - | - | - | - | - | - | - | FAIL (AttributeError: 'list' object has no attribute 'lower') |
| 33 | mrrooter.com | 6 | ok | 14 | 0 | 1 | 2 | 4 | - | 0.59 | PASS |
| 34 | benjaminfranklinplumbing.com | 6 | ok | 15 | 0 | 1 | 7 | 16 | Y | 0.5 | PASS |
| 35 | onehourheatandair.com | 6 | ok | 18 | 0 | 1 | 0 | 4 | Y | 0.35 | PASS |
| 36 | mistersparky.com | 5 | ok | 13 | 0 | 1 | 2 | 8 | Y | 0.45 | PASS |
| 37 | mrhandyman.com | 6 | ok | 20 | 0 | 0 | 7 | 7 | - | 0.5 | PASS |
| 38 | lentheplumber.com | 6 | ok | 16 | 39 | 0 | 3 | 12 | Y | 0.51 | PASS |
| 39 | petriplumbing.com | 6 | ok | 18 | 4 | 2 | 0 | 9 | Y | 0.53 | PASS |
| 40 | wmhenderson.com | 6 | ok | 36 | 16 | 1 | 0 | 3 | Y | 0.53 | PASS |
| 41 | hallerent.com | 6 | ok | 27 | 70 | 4 | 0 | 8 | Y | 0.5 | PASS |
| 42 | petro.com | 6 | ok | 21 | 0 | 0 | 0 | 5 | Y | 0.42 | PASS |
| 43 | thomasgalbraith.com | 6 | ok | 15 | 3 | 2 | 0 | 13 | Y | 0.47 | PASS |
| 44 | gemplumbing.com | 0 | BAD | - | - | - | - | - | - | - | FAIL (no pages crawled) |
| 45 | lindstromair.com | 6 | ok | 12 | 20 | 4 | 3 | 11 | Y | 0.46 | PASS |
| 46 | sobieskiinc.com | 6 | ok | 30 | 4 | 1 | 0 | 12 | Y | 0.45 | PASS |
| 47 | griffithenergyservices.com | 6 | ok | 11 | 17 | 18 | 1 | 5 | Y | 0.55 | PASS |
| 48 | ranshaw.com | 6 | ok | 10 | 15 | 3 | 0 | 5 | - | 0.68 | PASS |
| 49 | hillerplumbing.com | 6 | ok | 21 | 5 | 2 | 8 | 7 | Y | 0.47 | PASS |
| 50 | mauzy.com | 6 | ok | 11 | 25 | 3 | 12 | 11 | Y | 0.53 | PASS |
| 51 | goodberlet.com | 1 | ok | 6 | 0 | 0 | 0 | 0 | - | 0.4 | PASS |
| 52 | larryandsons.com | 6 | ok | 43 | 11 | 1 | 0 | 7 | Y | 0.41 | PASS |
| 53 | michaelbonsby.com | 0 | BAD | - | - | - | - | - | - | - | FAIL (no pages crawled) |
| 54 | cmcservice.com | 1 | ok | 0 | 0 | 0 | 0 | 0 | Y | - | PASS |
| 55 | lulasplumbing.com | 0 | BAD | - | - | - | - | - | - | - | FAIL (no pages crawled) |
| 56 | airnowcooling.com | 0 | BAD | - | - | - | - | - | - | - | FAIL (no pages crawled) |
| 57 | weldonp_h.com | 0 | BAD | - | - | - | - | - | - | - | FAIL (no pages crawled) |
| 58 | bluedotservice.com | 0 | BAD | - | - | - | - | - | - | - | FAIL (no pages crawled) |
| 59 | precisionhvactexas.com | 0 | BAD | - | - | - | - | - | - | - | FAIL (no pages crawled) |
| 60 | dynamicairllc.com | 0 | BAD | - | - | - | - | - | - | - | FAIL (no pages crawled) |
| 61 | coolingunlimited.com | 6 | ok | 30 | 101 | 4 | 0 | 6 | - | 0.48 | PASS |
| 62 | frostingny.com | 0 | BAD | - | - | - | - | - | - | - | FAIL (no pages crawled) |
| 63 | airassurance.com | 6 | ok | 6 | 2 | 1 | 0 | 13 | Y | 0.43 | PASS |
| 64 | acbyj.com | 6 | ok | 12 | 6 | 1 | 0 | 11 | Y | 0.49 | PASS |
| 65 | classicairtexas.com | 0 | BAD | - | - | - | - | - | - | - | FAIL (no pages crawled) |
| 66 | comfortmasters.com | 6 | ok | 17 | 6 | 1 | 0 | 9 | Y | 0.49 | PASS |
| 67 | airsupplyheating.com | 0 | BAD | - | - | - | - | - | - | - | FAIL (no pages crawled) |
| 68 | allproplumbing.com | 6 | ok | 4 | 0 | 0 | 8 | 2 | - | 0.26 | PASS |
| 69 | scottsheatingandair.com | 0 | BAD | - | - | - | - | - | - | - | FAIL (no pages crawled) |
| 70 | totalcomfortmechanical.com | 6 | ok | 27 | 14 | 0 | 0 | 7 | - | 0.41 | PASS |
