# Publish to GitHub and Streamlit Community Cloud

## 1. Create the GitHub repository

Suggested name: `binomial-decisions-studio`.

Upload the **contents** of this folder, not the ZIP file. Keep the directory structure intact. Confirm that these paths appear in GitHub:

```
app.py
requirements.txt
.streamlit/config.toml
lattice_component/index.html
guided.py
builder.py
builder_model.py
```

The other Python modules and tests must also be uploaded. GitHub Desktop can publish this folder as a repository and preserves dot-folders. If using GitHub's browser uploader, explicitly check that `.streamlit/config.toml` was included. Do not upload the surrounding textbook directory.

## 2. Deploy

1. Sign in at https://share.streamlit.io with the GitHub account that has repository access.
2. Select **Create app**, then the existing-app option.
3. Select your repository and its branch (normally `main`).
4. Enter **app.py** for the main file path.
5. In **Advanced settings**, select **Python 3.13**, matching the locally tested major/minor version. Leave secrets empty.
6. Choose an available app subdomain if desired, then deploy.

Settings summary:

| Setting | Value |
|---|---|
| Main file | app.py |
| Python | 3.13 |
| Dependencies | requirements.txt (Streamlit 1.51.0) |
| Secrets / API keys | None |
| System packages | None |
| Extra component build | None |

These instructions follow the official [deployment guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy), [file organization guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/file-organization), and [dependency guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies), checked October 19, 2026.

## 3. Check the hosted app

- Open the one-period example and answer the five setup questions.
- Continue to the lattice; verify that clicking an early node shows the right-to-left warning.
- At the up maturity node, enter `max(0,S-K)`; the value should be 20.
- Complete the down payoff and the root with `(p*Vu+(1-p)*Vd)/R`; the root should be 11.904762.
- In the three-period example, solve a maturity node and test the column-fill prompt.
- Check the full lattice view and a phone-sized browser window.

After deployment, share the resulting `https://...streamlit.app` URL. The local `127.0.0.1` address only works on the machine running the app. To link directly to a page, append `?page=one`, `?page=setup`, `?page=gates-three`, or another route from the app.

## Updating

Commit changed files to the same GitHub branch. Community Cloud will pick up repository changes. Preserve the pinned requirements until an upgrade has been tested.

## Troubleshooting

- Missing-module error: confirm all Python modules are alongside app.py.
- Blank or missing lattice: confirm lattice_component/index.html exists with exactly that capitalization and path.
- Missing theme: check .streamlit/config.toml at the repository root.
- Dependency error: confirm requirements.txt and the selected Python version; inspect the cloud build logs.
- Progress resets after a session ends: expected. The studio stores practice progress in session state, not a database.

This package has been locally verified; GitHub publication and Community Cloud deployment have not been performed for you.
