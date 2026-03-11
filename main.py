# Created: 2026-03-11 11:00
import sys
from datetime import datetime
from pathlib import Path

import click
from dotenv import load_dotenv
from rich import print as rprint
from rich.console import Console
from rich.table import Table

load_dotenv(Path(__file__).parent / ".env")

from db import init_db
from matcher import match_job
from reminders import get_reminders
from tracker import (
    VALID_STATUSES,
    add_application,
    delete_application,
    get_application,
    list_applications,
    update_application,
)

console = Console()

STATUS_STYLES = {
    "Applied": "blue",
    "Phone Screen": "yellow",
    "Interview": "cyan",
    "Offer": "bold green",
    "Rejected": "red",
    "Withdrawn": "dim",
    "Ghosted": "dim red",
}


@click.group()
def cli():
    """Job Search Helper — track applications, match postings, get follow-up reminders."""
    init_db()


@cli.command()
def add():
    """Add a new job application."""
    company = click.prompt("Company")
    role = click.prompt("Role / Title")
    status = click.prompt(
        "Status",
        type=click.Choice(VALID_STATUSES),
        default="Applied",
        show_default=True,
    )
    date_applied = click.prompt(
        "Date applied (YYYY-MM-DD)",
        default=datetime.now().strftime("%Y-%m-%d"),
    )
    url = click.prompt("Job URL", default="", show_default=False)
    contact = click.prompt("Contact (name / email)", default="", show_default=False)
    notes = click.prompt("Notes", default="", show_default=False)

    app_id = add_application(
        company=company,
        role=role,
        status=status,
        date_applied=date_applied,
        url=url or None,
        contact=contact or None,
        notes=notes or None,
    )
    rprint(f"\n[bold green]✓ Added application #{app_id}:[/bold green] {role} at {company}")


@cli.command("list")
@click.option(
    "--status",
    type=click.Choice(VALID_STATUSES + ["all"]),
    default="all",
    show_default=True,
    help="Filter by status.",
)
def list_apps(status):
    """List job applications."""
    apps = list_applications(status if status != "all" else None)

    if not apps:
        rprint("[yellow]No applications found.[/yellow]")
        return

    title = f"Job Applications" + (f" — {status}" if status != "all" else "")
    table = Table(title=title, show_lines=True)
    table.add_column("#", style="dim", width=4, justify="right")
    table.add_column("Company", style="bold", min_width=14)
    table.add_column("Role", min_width=18)
    table.add_column("Status", min_width=12)
    table.add_column("Applied", style="green", width=11)
    table.add_column("Follow-up", width=11)
    table.add_column("Notes", style="dim", max_width=35)

    for app in apps:
        style = STATUS_STYLES.get(app["status"], "white")
        table.add_row(
            str(app["id"]),
            app["company"],
            app["role"],
            f"[{style}]{app['status']}[/{style}]",
            app["date_applied"] or "—",
            app["follow_up_date"] or "—",
            (app["notes"] or "")[:60],
        )

    console.print(table)
    rprint(f"[dim]{len(apps)} application(s)[/dim]")


@cli.command()
@click.argument("id", type=int)
def update(id):
    """Update an application by ID."""
    app = get_application(id)
    if not app:
        rprint(f"[red]Application #{id} not found.[/red]")
        sys.exit(1)

    rprint(f"\nUpdating [bold]#{id}[/bold]: {app['role']} at {app['company']}  [{app['status']}]")

    field = click.prompt(
        "Field to update",
        type=click.Choice(["status", "notes", "contact", "url", "follow_up_date"]),
    )

    if field == "status":
        value = click.prompt(
            "New status",
            type=click.Choice(VALID_STATUSES),
            default=app["status"],
        )
    else:
        current = app[field] or ""
        value = click.prompt(f"New {field}", default=current) or None

    update_application(id, **{field: value})
    rprint(f"[bold green]✓ Updated #{id}[/bold green]")


@cli.command()
@click.argument("id", type=int)
def delete(id):
    """Delete an application by ID."""
    app = get_application(id)
    if not app:
        rprint(f"[red]Application #{id} not found.[/red]")
        sys.exit(1)

    if click.confirm(f"Delete '{app['role']}' at '{app['company']}'?"):
        delete_application(id)
        rprint(f"[bold green]✓ Deleted application #{id}[/bold green]")
    else:
        rprint("[dim]Cancelled.[/dim]")


@cli.command()
def reminders():
    """Show applications that need follow-up."""
    items = get_reminders()

    if not items:
        rprint("[bold green]✓ No follow-ups needed right now.[/bold green]")
        return

    table = Table(title="Follow-up Reminders", show_lines=True)
    table.add_column("#", style="dim", width=4, justify="right")
    table.add_column("Company", style="bold", min_width=14)
    table.add_column("Role", min_width=18)
    table.add_column("Status", min_width=12)
    table.add_column("Reason", style="yellow", min_width=30)
    table.add_column("Contact", style="dim")

    for app, reason in items:
        style = STATUS_STYLES.get(app["status"], "white")
        table.add_row(
            str(app["id"]),
            app["company"],
            app["role"],
            f"[{style}]{app['status']}[/{style}]",
            reason,
            app["contact"] or "—",
        )

    console.print(table)
    rprint(f"[yellow]{len(items)} application(s) need attention.[/yellow]")


@cli.command()
@click.option(
    "--file", "filepath",
    type=click.Path(exists=True),
    default=None,
    help="Path to a text file containing the job posting.",
)
def match(filepath):
    """Match a job posting to your resume using Claude AI.

    Paste the job posting interactively, or pass --file to read from a file.
    """
    if filepath:
        with open(filepath, encoding="utf-8") as f:
            job_posting = f.read()
    else:
        rprint("[cyan]Paste the job posting below. Type [bold]END[/bold] on a new line when done:[/cyan]\n")
        lines = []
        while True:
            try:
                line = input()
                if line.strip().upper() == "END":
                    break
                lines.append(line)
            except EOFError:
                break
        job_posting = "\n".join(lines)

    if not job_posting.strip():
        rprint("[red]No job posting provided.[/red]")
        sys.exit(1)

    rprint("\n[cyan]Analyzing job fit with Claude...[/cyan]\n")
    rprint("[dim]─" * 60 + "[/dim]")
    match_job(job_posting)
    rprint("[dim]─" * 60 + "[/dim]")


if __name__ == "__main__":
    cli()
