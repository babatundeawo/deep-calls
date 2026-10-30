<div align="center">

<img src="docs/assets/logo.svg" alt="Deep Calls logo" width="88" height="88">

# Deep Calls

**Long form faith for people who ask hard questions.**

[![Build and deploy](https://github.com/babatundeawo/deep-calls/actions/workflows/deploy.yml/badge.svg)](https://github.com/babatundeawo/deep-calls/actions/workflows/deploy.yml)
[![CodeQL](https://github.com/babatundeawo/deep-calls/actions/workflows/codeql.yml/badge.svg)](https://github.com/babatundeawo/deep-calls/actions/workflows/codeql.yml)

[Read the essays](https://babatundeawo.github.io/deep-calls/) · [Browse the library](https://babatundeawo.github.io/deep-calls/library.html) · [Get in touch](https://babatundeawo.github.io/deep-calls/contact.html)

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/assets/preview-dark.png">
  <img src="docs/assets/preview-light.png" alt="The Deep Calls home page" width="860">
</picture>

</div>

## About

Deep Calls is a library of long form Christian apologetics essays written from Nigeria for the curious, the sceptical and the tired. Each essay starts with a real question about scripture, doubt, culture or suffering, and takes its time with the answer.

## Features

* 29 essays across six themes, with search (press Ctrl or Cmd + K), filters and sorting
* Calm reading: clear type, contents list, reading progress and estimated reading time
* Save for later, adjustable text size, and continue reading where you stopped
* Select a passage to copy it as a quote with a link back
* Light and dark themes that follow your device
* Fast, accessible and works without JavaScript
* Pages that print cleanly

## How to use

Open **[babatundeawo.github.io/deep-calls](https://babatundeawo.github.io/deep-calls/)** in any browser. Pick an essay from the home page or the library, or press Ctrl/Cmd + K to search.

Have a question or found a mistake? [Open an issue](https://github.com/babatundeawo/deep-calls/issues/new/choose) or use the [contact page](https://babatundeawo.github.io/deep-calls/contact.html).

## Tech stack

Python and Markdown generate a plain HTML, CSS and JavaScript site, with no framework and no tracking. It is built and published by GitHub Actions to GitHub Pages. Fonts (Fraunces, Literata, Inter) are hosted on the site itself.

## Project structure

```text
content/    the essays, one Markdown file each
assets/     styles, scripts and fonts
scripts/    the site generator and quality checks
docs/       guides for the site owner
.github/    automated build, deploy and security checks
```

Guides for the owner: [deploying](docs/DEPLOYMENT.md) and [customising](docs/CUSTOMISING.md). Standards for writing essays are in [content/README.md](content/README.md).

## Contributing

Corrections and topic suggestions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Security

See [SECURITY.md](SECURITY.md) to report a concern.

## Licence and credits

Essay text and site design © Babatunde Awoyemi. All rights reserved. Fonts are used under the SIL Open Font Licence; the licences are in [`assets/fonts`](assets/fonts).

## Contact

babatundeawoyemi91@gmail.com · [@babatundeawo](https://github.com/babatundeawo)
