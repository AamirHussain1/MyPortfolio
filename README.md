# Python Developer Portfolio

A responsive personal portfolio built with Python, Flask, Jinja, HTML, CSS, and a small amount of JavaScript.

## Run locally

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Then open <http://127.0.0.1:5000>.

## Start with one click

Double-click `start_portfolio.bat` in the project folder. It installs requirements, starts Flask in a hidden process, waits for the site to respond, and opens the portfolio in your browser. PowerShell is launched with a process-only execution-policy bypass; your system-wide policy is unchanged.

To stop the hidden server, double-click `stop_portfolio.bat`.

Launcher logs and its process ID are stored in `%LOCALAPPDATA%\AamirPortfolio`. The `.ps1` file is used internally by the batch launchers; you do not need to activate the virtual environment manually.

## Resume download and updates

The **Download resume** button serves `static/resume/Aamir_Hussain_Resume.pdf` as a PDF attachment. The portfolio footer's **Update resume** link opens the owner upload form. On the first visit to that form, a strong random password is generated and stored locally at `instance/resume_admin_password.txt`; read it in PowerShell with:

```powershell
Get-Content .\instance\resume_admin_password.txt
```

Use that password and a PDF file (up to 10 MB) to replace the active resume. The updated file is kept at `instance/resume.pdf`, while the original PDF remains untouched as a fallback. The `instance/` directory is excluded from Git so uploaded resumes and the local admin password are not committed.

For a hosted site, configure a strong `PORTFOLIO_ADMIN_PASSWORD` environment variable in the hosting provider before enabling uploads. Use HTTPS for the public site, and do not commit or share the admin password. Some free hosting plans use temporary storage; an uploaded replacement can be lost when the service redeploys unless persistent storage is configured.

## Free public hosting (Render)

The repository includes `render.yaml` for the `aamirhussain.onrender.com` free Render web service. Render's free service can spin down when idle and its filesystem is temporary, so the hosted configuration disables resume uploads and the Windows-only Naukri updater. Visitors can still download the original resume included in `static/resume/`. Continue to use the local Windows launcher for resume uploads and Naukri automation.

To publish:

1. Push this project to a GitHub repository connected to your Render account. This portfolio's current `AamirHussain1/MyPortfolio` repository is public: its source and the resume PDF in `static/resume/` are publicly visible/downloadable. Keep `.venv/`, `instance/`, and `__pycache__/` out of the repository; `.gitignore` already excludes them. Do not commit passwords or Naukri credentials.
2. In Render, choose **New > Blueprint**, enter the public repository URL, and deploy the `render.yaml` blueprint. The file selects Render's free web-service plan and runs Flask with Gunicorn. Connecting Render's GitHub integration instead enables repository-linked deployment features; using the public URL alone does not enable automatic deploys.
3. Wait for the first deploy to finish, then open the `onrender.com` URL shown in the Render dashboard. The first request after the service has been idle may take about a minute while the free service starts.
4. Verify the homepage, LinkedIn link, and `/resume` download. The resume-upload and Naukri automation routes are intentionally unavailable on the hosted copy; those workflows remain local. With a public repository URL, manually sync the Blueprint and deploy after pushing changes.

Render free services have usage limits and ephemeral storage. Do not enable public resume uploads unless you configure durable storage and a strong `PORTFOLIO_ADMIN_PASSWORD` first.

## Naukri Resume Updater

Open **Naukri Resume Updater** on the portfolio to run the existing `D:\Resume\update_naukri.py` updater for the Aamir profile, use the current portfolio resume, or enable/disable its daily Windows schedule. The daily schedule is enabled on this computer for between 8:15 and 8:30 AM local time, as the currently signed-in Windows user. Keep the computer awake and signed in; verify the result on Naukri after a run. The updater's existing login setup remains in the local resume-folder script and is not copied into the portfolio.

The first setup adds an Aamir-only execution mode to the existing updater. The portfolio runner sets that mode and the active resume path, so the normal script run is not used by the portfolio workflow. The scheduled task runs locally on your computer; it does not run when only a hosted copy of the portfolio is online.

## Portfolio content

The portfolio content is organized near the top of `app.py`: `PROFILE` contains contact details and the summary, `SKILLS` lists technical skills, `EXPERIENCE` contains employment highlights, `PROJECTS` describes platform work, and `EDUCATION` contains the degree details. Update those values to keep the page in sync with your latest resume.
