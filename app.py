import hmac
import json
import os
import secrets
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlsplit

from flask import (
    Flask,
    abort,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024


def is_enabled_environment_value(value):
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


app.config["ENABLE_RESUME_UPLOADS"] = is_enabled_environment_value(
    os.environ.get("PORTFOLIO_ENABLE_RESUME_UPLOADS", "true")
)
app.config["ENABLE_NAUKRI_AUTOMATION"] = is_enabled_environment_value(
    os.environ.get(
        "PORTFOLIO_ENABLE_NAUKRI_AUTOMATION",
        "true" if os.name == "nt" else "false",
    )
)
app.config["ENABLE_PROJECT_MANAGEMENT"] = is_enabled_environment_value(
    os.environ.get(
        "PORTFOLIO_ENABLE_PROJECT_MANAGEMENT",
        "true" if os.name == "nt" else "false",
    )
)

PROFILE = {
    "name": "Aamir Hussain",
    "role": "Silicon Automation & Validation Engineer",
    "location": "Bengaluru, India",
    "email": "aamirbhet@gmail.com",
    "phone": "+91 77808 23430",
    "phone_link": "+917780823430",
    "linkedin_url": "https://www.linkedin.com/in/aamirhussainbhat",
    "intro": (
        "Silicon validation engineer with 4 years of experience in pre-silicon "
        "and post-silicon validation, platform bring-up, and Python test automation "
        "for Intel Xeon servers and Microsoft Maia AI accelerators."
    ),
    "about": (
        "I build Python and Robot Framework automation for complex silicon and "
        "server platforms. At UST, I have worked across Intel Xeon server "
        "validation and Microsoft Maia AI accelerators, combining platform "
        "bring-up, firmware testing, and hands-on hardware debug. I automated "
        "300+ test cases and helped reduce validation cycle time by 60%."
    ),
}

SKILLS = [
    {"name": "Python", "group": "Automation", "mark": "Py"},
    {"name": "Robot Framework", "group": "Test automation", "mark": "RF"},
    {"name": "Linux", "group": "Operating systems", "mark": "Li"},
    {"name": "PCIe Gen4 / 5 / 6", "group": "High-speed I/O", "mark": "PC"},
    {"name": "DDR4 / DDR5 / HBM", "group": "Memory", "mark": "DR"},
    {"name": "SR-IOV", "group": "Virtualization", "mark": "IO"},
    {"name": "Firmware validation", "group": "Platform testing", "mark": "FW"},
    {"name": "JTAG / ITP", "group": "Hardware debug", "mark": "HW"},
    {"name": "Intel Xeon", "group": "Server platforms", "mark": "XE"},
    {"name": "Microsoft Maia", "group": "AI accelerators", "mark": "AI"},
    {"name": "Root-cause analysis", "group": "Failure analysis", "mark": "RC"},
    {"name": "Platform bring-up", "group": "Silicon validation", "mark": "SV"},
]

IMPACT_STATS = [
    {"value": "4 years", "label": "Silicon validation"},
    {"value": "300+", "label": "Automated test cases"},
    {"value": "60%", "label": "Faster validation cycles"},
    {"value": "1S–8S", "label": "Server configurations"},
]

VALIDATION_AREAS = [
    {
        "number": "01",
        "title": "High-speed interfaces",
        "details": "PCIe Gen4 / Gen5 / Gen6, SR-IOV, SerDes, Ethernet, and USB",
        "mark": "I/O",
    },
    {
        "number": "02",
        "title": "Memory & training",
        "details": "DDR4 / DDR5, HBM, memory controller and PHY, margin and stress testing",
        "mark": "MEM",
    },
    {
        "number": "03",
        "title": "Platform & power",
        "details": "PMSS, RAPL, P-States, C-States, SST, PECI, and ISS",
        "mark": "SYS",
    },
    {
        "number": "04",
        "title": "Bring-up & debug",
        "details": "Firmware flashing, JTAG, ITP, logic analyzers, and root-cause analysis",
        "mark": "DBG",
    },
]

EXPERIENCE = [
    {
        "role": "Python Automation Engineer (Silicon Validation)",
        "company": "UST Global",
        "location": "Bengaluru, India",
        "dates": "Oct 2022 — Present",
        "highlights": [
            "Built Python and Robot Framework automation for firmware validation and regression testing.",
            "Automated 300+ test cases and reduced Intel Xeon validation cycle time by 60%.",
            "Validated Microsoft Maia accelerator platforms, including SR-IOV virtualization and secure firmware workflows.",
            "Debugged platform issues using JTAG, ITP, logic analyzers, and log/trace analysis.",
        ],
    },
]

PROJECTS = [
    {
        "number": "01",
        "title": "Microsoft Maia 200 / 300",
        "description": (
            "Owned validation and Python/Robot Framework automation for AI "
            "accelerator platforms. Enabled SR-IOV PF/VF/VM configurations and "
            "supported secure subsystem communication and inference workloads."
        ),
        "tags": ["Python", "Robot Framework", "SR-IOV", "Firmware"],
        "label": "AI accelerator",
    },
    {
        "number": "02",
        "title": "Intel Xeon server platforms",
        "description": (
            "Validated Sapphire Rapids, Emerald Rapids, and Granite Rapids "
            "platforms across PCIe, DDR, power management, and multi-socket "
            "configurations. Automated 300+ tests, cutting regression cycle time by 60%."
        ),
        "tags": ["Python", "Intel Xeon", "PCIe", "DDR4 / DDR5"],
        "label": "Server validation",
    },
]

EDUCATION = {
    "degree": "B.Tech, Computer Science and Engineering",
    "institution": "Jammu University",
    "year": "2021",
}

RESUME_NAME = "Aamir_Hussain_Resume.pdf"
RESUME_PATH = Path(app.root_path) / "static" / "resume" / RESUME_NAME
UPDATED_RESUME_PATH = Path(app.instance_path) / "resume.pdf"
ADDED_PROJECTS_PATH = Path(app.instance_path) / "projects.json"
ADMIN_PASSWORD_PATH = Path(app.instance_path) / "resume_admin_password.txt"
NAUKRI_STATUS_PATH = Path(app.instance_path) / "naukri_status.json"
NAUKRI_RUNNER_PATH = Path(app.root_path) / "naukri_task.py"
NAUKRI_TASK_NAME = "AamirPortfolioNaukriResumeUpdate"
NAUKRI_PROFILE_URL = "https://www.naukri.com/mnjuser/homepage"
app.config["RESUME_PATH"] = RESUME_PATH
app.config["UPDATED_RESUME_PATH"] = UPDATED_RESUME_PATH
app.config["ADDED_PROJECTS_PATH"] = ADDED_PROJECTS_PATH
app.config["ADMIN_PASSWORD_PATH"] = ADMIN_PASSWORD_PATH
app.config["NAUKRI_STATUS_PATH"] = NAUKRI_STATUS_PATH
app.config["NAUKRI_RUNNER_PATH"] = NAUKRI_RUNNER_PATH


def get_admin_password():
    configured_password = app.config.get("ADMIN_PASSWORD") or os.environ.get(
        "PORTFOLIO_ADMIN_PASSWORD"
    )
    if configured_password:
        return configured_password

    password_path = Path(app.config["ADMIN_PASSWORD_PATH"])
    password_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with password_path.open("x", encoding="utf-8") as password_file:
            password_file.write(secrets.token_urlsafe(32))
    except FileExistsError:
        pass
    return password_path.read_text(encoding="utf-8").strip()


def read_added_projects():
    projects_path = Path(app.config["ADDED_PROJECTS_PATH"])
    if not projects_path.is_file():
        return []

    projects = json.loads(projects_path.read_text(encoding="utf-8"))
    if not isinstance(projects, list) or any(
        not isinstance(project, dict) for project in projects
    ):
        raise ValueError(f"Project data has an invalid format: {projects_path}")
    return projects


def write_added_projects(projects):
    projects_path = Path(app.config["ADDED_PROJECTS_PATH"])
    projects_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=projects_path.parent,
            prefix="projects-",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            json.dump(projects, temporary_file, ensure_ascii=False, indent=2)
            temporary_file.write("\n")
        os.replace(temporary_path, projects_path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def project_form_error(form):
    title = form.get("title", "").strip()
    label = form.get("label", "").strip()
    description = form.get("description", "").strip()
    tags = [tag.strip() for tag in form.get("tags", "").split(",") if tag.strip()]
    link = form.get("link", "").strip()

    if not title or len(title) > 100:
        return None, "Project title is required and must be 100 characters or fewer."
    if not label or len(label) > 60:
        return None, "Project category is required and must be 60 characters or fewer."
    if not description or len(description) > 1200:
        return None, "Description is required and must be 1,200 characters or fewer."
    if not tags or len(tags) > 8 or any(len(tag) > 32 for tag in tags):
        return None, "Add between 1 and 8 technologies, each 32 characters or fewer."
    if len(set(tag.casefold() for tag in tags)) != len(tags):
        return None, "Remove duplicate technologies from the project tags."
    if link:
        try:
            parsed_link = urlsplit(link)
        except ValueError:
            return None, "Project link must be a valid HTTPS or HTTP URL."
        if parsed_link.scheme not in {"http", "https"} or not parsed_link.netloc:
            return None, "Project link must be a valid HTTPS or HTTP URL."

    return {
        "id": secrets.token_urlsafe(9),
        "title": title,
        "label": label,
        "description": description,
        "tags": tags,
        "link": link,
    }, None


def read_naukri_status():
    status_path = Path(app.config["NAUKRI_STATUS_PATH"])
    if not status_path.is_file():
        return {
            "status": "not-run",
            "started_at": None,
            "finished_at": None,
            "message": "No portfolio-managed Naukri update has run yet.",
        }

    try:
        status = json.loads(status_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {
            "status": "unknown",
            "started_at": None,
            "finished_at": None,
            "message": "The last-run status file could not be read.",
        }
    if not isinstance(status, dict):
        return {
            "status": "unknown",
            "started_at": None,
            "finished_at": None,
            "message": "The last-run status file has an invalid format.",
        }
    return status


def is_naukri_schedule_enabled():
    if os.name != "nt":
        return False
    try:
        result = subprocess.run(
            ["schtasks.exe", "/Query", "/TN", NAUKRI_TASK_NAME],
            capture_output=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def update_naukri_schedule(enable):
    if os.name != "nt":
        return False, "Daily scheduling is available only on Windows."

    schedule_script = Path(app.root_path) / "manage_naukri_schedule.ps1"
    if not schedule_script.is_file():
        return False, "The Windows schedule manager is unavailable."
    try:
        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(schedule_script),
                "-Action",
                "Install" if enable else "Remove",
            ],
            capture_output=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False, "Windows Task Scheduler could not be reached."
    if result.returncode != 0:
        return False, result.stderr.decode(errors="replace").strip() or (
            "Windows Task Scheduler could not update the schedule."
        )
    if enable:
        return True, (
            "Daily Aamir Naukri resume update scheduled between 8:15 and 8:30 AM "
            "local time. Stay signed in and keep the computer awake."
        )
    return True, "The daily Naukri resume update schedule was removed."


@app.get("/")
def home():
    return render_template(
        "index.html",
        profile=PROFILE,
        skills=SKILLS,
        impact_stats=IMPACT_STATS,
        validation_areas=VALIDATION_AREAS,
        naukri_status=read_naukri_status(),
        experience=EXPERIENCE,
        projects=PROJECTS + read_added_projects(),
        education=EDUCATION,
        naukri_enabled=app.config["ENABLE_NAUKRI_AUTOMATION"],
        project_management_enabled=app.config["ENABLE_PROJECT_MANAGEMENT"],
    )


@app.get("/resume")
def download_resume():
    updated_resume_path = Path(app.config["UPDATED_RESUME_PATH"])
    resume_path = (
        updated_resume_path
        if updated_resume_path.is_file()
        else Path(app.config["RESUME_PATH"])
    )
    if not resume_path.is_file():
        abort(404, description="No resume is available to download.")
    return send_file(
        resume_path,
        as_attachment=True,
        download_name=RESUME_NAME,
        mimetype="application/pdf",
    )


@app.route("/resume/upload", methods=["GET", "POST"])
def upload_resume():
    if not app.config["ENABLE_RESUME_UPLOADS"]:
        abort(404)

    if request.method == "GET":
        get_admin_password()
        updated = request.args.get("updated") == "1"
        return render_template(
            "upload_resume.html",
            message=(
                "Resume updated. The public download now serves the new PDF."
                if updated
                else None
            ),
            message_type="success" if updated else None,
        )

    submitted_password = request.form.get("password", "")
    if not hmac.compare_digest(submitted_password, get_admin_password()):
        return render_template(
            "upload_resume.html",
            message="The admin password is incorrect.",
            message_type="error",
        ), 403

    resume = request.files.get("resume")
    if resume is None or not resume.filename:
        return render_template(
            "upload_resume.html",
            message="Choose a PDF file to upload.",
            message_type="error",
        ), 400
    if Path(resume.filename).suffix.lower() != ".pdf":
        return render_template(
            "upload_resume.html",
            message="The uploaded file must have a .pdf extension.",
            message_type="error",
        ), 400
    if resume.stream.read(5) != b"%PDF-":
        return render_template(
            "upload_resume.html",
            message="The selected file does not appear to be a valid PDF.",
            message_type="error",
        ), 400

    resume.stream.seek(0)
    updated_resume_path = Path(app.config["UPDATED_RESUME_PATH"])
    updated_resume_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=updated_resume_path.parent,
            prefix="resume-",
            suffix=".upload",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            resume.save(temporary_file)
        os.replace(temporary_path, updated_resume_path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)

    return redirect(url_for("upload_resume", updated="1"))


@app.route("/projects/manage", methods=["GET", "POST"])
def manage_projects():
    if not app.config["ENABLE_PROJECT_MANAGEMENT"]:
        abort(404)

    if request.method == "GET":
        get_admin_password()
        message = None
        if request.args.get("added") == "1":
            message = "Project added to your portfolio."
        elif request.args.get("deleted") == "1":
            message = "Project removed from your portfolio."
        return render_template(
            "manage_projects.html",
            projects=read_added_projects(),
            message=message,
            message_type="success" if message else None,
        )

    submitted_password = request.form.get("password", "")
    if not hmac.compare_digest(submitted_password, get_admin_password()):
        return render_template(
            "manage_projects.html",
            projects=read_added_projects(),
            message="The admin password is incorrect.",
            message_type="error",
        ), 403

    projects = read_added_projects()
    action = request.form.get("action")
    if action == "add":
        project, error = project_form_error(request.form)
        if error:
            return render_template(
                "manage_projects.html",
                projects=projects,
                message=error,
                message_type="error",
            ), 400
        project["number"] = f"{len(PROJECTS) + len(projects) + 1:02}"
        projects.append(project)
        write_added_projects(projects)
        return redirect(url_for("manage_projects", added="1"))

    if action == "delete":
        project_id = request.form.get("project_id", "")
        remaining_projects = [
            project for project in projects if project.get("id") != project_id
        ]
        if len(remaining_projects) == len(projects):
            return render_template(
                "manage_projects.html",
                projects=projects,
                message="That project could not be found.",
                message_type="error",
            ), 404
        write_added_projects(remaining_projects)
        return redirect(url_for("manage_projects", deleted="1"))

    return render_template(
        "manage_projects.html",
        projects=projects,
        message="Choose a valid project action.",
        message_type="error",
    ), 400


@app.get("/todos")
def todos():
    if not app.config["ENABLE_NAUKRI_AUTOMATION"]:
        abort(404)

    return render_template(
        "todos.html",
        schedule_enabled=is_naukri_schedule_enabled(),
        status=read_naukri_status(),
        profile_url=NAUKRI_PROFILE_URL,
        message=(
            "The portfolio-managed update has started."
            if request.args.get("started") == "1"
            else None
        ),
        message_type="success" if request.args.get("started") == "1" else None,
    )


@app.route("/todos/naukri", methods=["GET", "POST"])
def manage_naukri_todo():
    if not app.config["ENABLE_NAUKRI_AUTOMATION"]:
        abort(404)

    if request.method == "GET":
        get_admin_password()
        return render_template(
            "naukri_todo.html",
            message=(
                "The portfolio-managed update has started."
                if request.args.get("started") == "1"
                else None
            ),
            message_type="success" if request.args.get("started") == "1" else None,
            schedule_enabled=is_naukri_schedule_enabled(),
            status=read_naukri_status(),
            profile_url=NAUKRI_PROFILE_URL,
        )

    submitted_password = request.form.get("password", "")
    if not hmac.compare_digest(submitted_password, get_admin_password()):
        return render_template(
            "naukri_todo.html",
            message="The admin password is incorrect.",
            message_type="error",
            schedule_enabled=is_naukri_schedule_enabled(),
            status=read_naukri_status(),
            profile_url=NAUKRI_PROFILE_URL,
        ), 403

    action = request.form.get("action")
    if action in {"schedule", "unschedule"}:
        success, message = update_naukri_schedule(action == "schedule")
        return render_template(
            "naukri_todo.html",
            message=message,
            message_type="success" if success else "error",
            schedule_enabled=is_naukri_schedule_enabled(),
            status=read_naukri_status(),
            profile_url=NAUKRI_PROFILE_URL,
        ), 200 if success else 503

    if action == "run":
        runner_path = Path(app.config["NAUKRI_RUNNER_PATH"])
        if not runner_path.is_file():
            abort(503, description="The Naukri update runner is unavailable.")
        try:
            subprocess.Popen(
                [sys.executable, str(runner_path)],
                cwd=app.root_path,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                close_fds=True,
            )
        except OSError:
            return render_template(
                "naukri_todo.html",
                message="Could not start the Naukri updater.",
                message_type="error",
                schedule_enabled=is_naukri_schedule_enabled(),
                status=read_naukri_status(),
                profile_url=NAUKRI_PROFILE_URL,
            ), 503
        return redirect(url_for("manage_naukri_todo", started="1"))

    return render_template(
        "naukri_todo.html",
        message="Choose a valid task action.",
        message_type="error",
        schedule_enabled=is_naukri_schedule_enabled(),
        status=read_naukri_status(),
        profile_url=NAUKRI_PROFILE_URL,
    ), 400


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
