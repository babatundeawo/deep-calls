# Deployment guide

Everything below happens in your web browser. You never need a terminal.

The site rebuilds and publishes itself every time a change lands on the `main` branch.

## 1. Replace the old repository with this one

Because the new repository keeps the name `deep-calls`, the web address stays the same.

1. Open the old repository on GitHub, then **Settings → General**, scroll to **Danger Zone**, and choose **Delete this repository** (or **Rename** it to `deep-calls-old` first if you want a safety net, and delete it once the new site works).
2. Click **+ → New repository**. Name it `deep-calls`, keep it **Public**, tick **Add a README file**, and click **Create repository**.
3. Unzip the package on your computer. Open the new repository, then **Add file → Upload files**, and drag in the contents of the unzipped folder (not the folder itself). GitHub accepts around 100 files at a time, so upload `content/` first, then the rest in a second batch, committing each time.
4. The hidden `.github` folder may not drag across. If it is missing, use **Add file → Create new file**, type `.github/workflows/deploy.yml` as the name (the slashes create folders), paste the file's text, and commit. Repeat for `codeql.yml`, `quality.yml`, `.github/dependabot.yml` and the files in `.github/ISSUE_TEMPLATE/`.
5. If the old README is still there, the upload replaces it.

## 2. Switch on publishing

1. Go to **Settings → Pages**.
2. Under **Build and deployment → Source**, choose **GitHub Actions**.
3. Open the **Actions** tab. The **Build and deploy** run should show a green tick within two minutes. Your site is then live at https://babatundeawo.github.io/deep-calls/.

If you see a red cross, open the run, click the failed step and read the message. It names the file and the problem (for example, an essay missing its title). Fix that file and commit; the site rebuilds automatically.

## 3. Switch on the security extras

Under **Settings → Code security**, turn on **Dependabot alerts**, **Dependabot security updates** and **Secret scanning**. Dependabot will then open pull requests for updates; see the next section on how to review them.

## Reviewing a pull request

1. Open the **Pull requests** tab and click the request.
2. Check that the **Checks** at the bottom are green. For a preview of the site, open **Checks → Build and deploy → Artifacts → site-preview**.
3. Click **Merge pull request**, then **Confirm**. The site updates in about two minutes.

## Adding or editing an essay

1. Open `content/` and click **Add file → Upload files** (or **Create new file**, or open an essay and click the pencil).
2. Drop in your `.md` file and click **Commit changes**. The details block at the top is optional (see [content/README.md](../content/README.md)).
3. Open the **Actions** tab. The **Build and deploy** run starts by itself and shows a green tick within about two minutes. The essay is then live.

If the run shows a yellow warning, the site still published; the warning names any file that was skipped and why. If it shows a red cross, open the run and read the failed step.

## Undoing a mistake

Open the **Commits** list, click the last good commit, and use **Browse files**; or open the bad commit and click **Revert**. Merge the revert and the site rebuilds.

## Using your own domain

1. In **Settings → Pages → Custom domain**, enter the domain and save.
2. At your domain provider, add the DNS records GitHub shows you.
3. Change `url` in `site.config.json` to the new address (keep the trailing `/`) and commit, so links, the sitemap and social cards use it.
