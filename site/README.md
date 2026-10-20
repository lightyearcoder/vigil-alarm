# Documentatiesite (proef)

Starlight-site die uit `../docs`, `../esphome/README.md` en `../CHANGELOG.md` wordt
gegenereerd. De bron blijft `docs/`; pas nooit bestanden in `site/src/content/docs` aan.

    cd site
    npm ci
    npm run dev       # lokaal bekijken
    npm run build     # bouwt naar dist/

Publiceren gaat via `.github/workflows/docs.yml` naar GitHub Pages
(Instellingen → Pages → Source: GitHub Actions). Pas `site` en `base` in
`astro.config.mjs` aan als de repository of gebruikersnaam anders is.
