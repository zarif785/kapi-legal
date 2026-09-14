# Kapi legal-site publication bundle

Prepared from the authoritative `docs/privacy.md` and `docs/terms.md` (version 1.1). The stylesheet and HTML structure reuse the existing public `kapi-legal` site; a narrow-screen link wrapping rule is added. The existing public contact address is retained until the owner changes it.

## Review locally

```sh
python3 docs/legal-site/build.py --check
python3 -m http.server 8766 --directory docs/legal-site
```

Open `http://localhost:8766/`. The Privacy, Terms and Support pages link to each other and work as static files; no scripts, tracking, remote fonts or dependencies are added.

## Regenerate after a policy edit

```sh
python3 docs/legal-site/build.py
python3 docs/legal-site/build.py --check
```

Edit the authoritative Markdown in `docs/` for policies. Support copy is in `docs/legal-site/support.md`. The builder accepts the specific Markdown constructs used in these pages and rejects unsupported block constructs. It checks every visible source block in order, safe URL schemes, existing local links, both MIT notices and page freshness. `verification.json` records source hashes and counts.

## Files to publish after approval

Copy these files into the existing `kapi-legal` site's publishing root:

- `index.html`
- `style.css`
- `.nojekyll`
- `privacy/index.html`
- `terms/index.html`
- `support/index.html`

Keep the builder, Markdown, verification files and this README in the workspace; they do not need to be published. Preserve the live site's other files. Do not copy an older policy from a separate checkout.

After publishing, verify these URLs signed out:

- `https://zarif785.github.io/kapi-legal/privacy/`
- `https://zarif785.github.io/kapi-legal/terms/`
- `https://zarif785.github.io/kapi-legal/support/`

Both policy pages must show version 1.1. Confirm full MIT notices, the working contact address, the corrected reset/privacy/EULA language, and monthly/yearly only. Set the corresponding URLs in App Store Connect.

This bundle is prepared for review only. No hosted site, repository, branch, commit, push, deployment or App Store setting has been changed by this preparation.

## Link check result

All local navigation and stylesheet targets pass. Of 21 external HTTPS references checked, 20 returned HTTP200. The canonical ManyThings attribution page returned HTTP406 to the automated request; its upstream address is retained rather than substituted with an invented mirror. Check that one manually in a normal browser before publishing. See `external-links.json` for individual results. Mail links use the current public address; no test email was sent.
