"""CLI entry point for ContentSifter."""

import logging
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from contentsifter.config import (
    DEFAULT_DB_PATH,
    DEFAULT_TRANSCRIPTS_DIR,
    ClientConfig,
    create_client as create_client_config,
    list_clients as list_clients_config,
    load_client,
    set_default_client,
)
from contentsifter.extraction.chunker import chunk_transcript
from contentsifter.extraction.extractor import extract_from_chunk
from contentsifter.llm.client import create_client as create_llm_client
from contentsifter.parser.metadata import parse_metadata
from contentsifter.parser.splitter import split_all_files, split_merged_file
from contentsifter.parser.turns import parse_speaker_turns
from contentsifter.storage.database import Database
from contentsifter.storage.repository import Repository

console = Console(force_terminal=True)


def _get_client_config(ctx) -> ClientConfig:
    """Get the client config from context."""
    return ctx.obj["client_config"]


@click.group()
@click.option(
    "--client", "-C",
    default=None,
    help="Client slug (default: from clients.json)",
)
@click.option(
    "--db",
    default=None,
    help="Database path (overrides client config)",
    type=click.Path(),
)
@click.option(
    "--llm-mode",
    type=click.Choice(["auto", "api", "claude-code"]),
    default="auto",
    help="LLM access mode",
)
@click.option(
    "--model",
    default="claude-sonnet-4-20250514",
    help="Claude model to use",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging")
@click.pass_context
def cli(ctx, client, db, llm_mode, model, verbose):
    """ContentSifter - Extract and search coaching call transcripts."""
    ctx.ensure_object(dict)

    # Load client config
    client_config = load_client(client)
    ctx.obj["client_config"] = client_config

    # Allow --db to override client config
    if db:
        ctx.obj["db_path"] = Path(db)
    else:
        ctx.obj["db_path"] = client_config.db_path

    ctx.obj["llm_mode"] = llm_mode
    ctx.obj["model"] = model
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO, format="%(message)s")


# ---------------------------------------------------------------------------
# Client Management Commands
# ---------------------------------------------------------------------------


@cli.group(name="client")
def client_group():
    """Manage clients."""
    pass


@client_group.command(name="create")
@click.argument("slug")
@click.option("--name", required=True, help="Client display name")
@click.option("--email", default="", help="Client email")
@click.option("--description", default="", help="Short description")
def client_create(slug, name, email, description):
    """Create a new client."""
    try:
        config = create_client_config(slug, name, email, description)
        console.print(f"[green]Created client:[/green] {slug}")
        console.print(f"  Name: {config.name}")
        console.print(f"  DB: {config.db_path}")
        console.print(f"  Content: {config.content_dir}")
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")


@client_group.command(name="list")
def client_list():
    """List all registered clients."""
    clients = list_clients_config()
    if not clients:
        console.print("[yellow]No clients registered.[/yellow]")
        return

    table = Table(title="Registered Clients")
    table.add_column("Slug", style="cyan")
    table.add_column("Name", style="bold")
    table.add_column("Email")
    table.add_column("Description")
    table.add_column("Default", justify="center")

    for c in clients:
        table.add_row(
            c["slug"],
            c["name"],
            c["email"],
            c["description"],
            "[green]✓[/green]" if c["is_default"] else "",
        )
    console.print(table)


@client_group.command(name="info")
@click.argument("slug")
def client_info(slug):
    """Show details for a client."""
    try:
        config = load_client(slug)
        console.print(f"[bold]{config.name}[/bold] ({config.slug})")
        console.print(f"  Email: {config.email}")
        console.print(f"  DB: {config.db_path}")
        console.print(f"  Content dir: {config.content_dir}")
        console.print(f"  Voice print: {config.voice_print_path}")
        console.print(f"  Drafts: {config.drafts_dir}")
        console.print(f"  Calendar: {config.calendar_dir}")

        if config.db_path.exists():
            with Database(config.db_path) as db:
                repo = Repository(db)
                summary = repo.get_progress_summary()
                console.print(f"\n  Calls: {summary['total_calls']}")
                console.print(f"  Extractions: {summary['total_extractions']}")

                # Content items count
                try:
                    row = db.conn.execute("SELECT COUNT(*) as cnt FROM content_items").fetchone()
                    console.print(f"  Content items: {row['cnt']}")
                except Exception:
                    pass
        else:
            console.print("\n  [dim]No database yet (run ingest to start).[/dim]")

        if config.voice_print_path.exists():
            console.print(f"\n  [green]Voice print exists[/green]")
        else:
            console.print(f"\n  [dim]No voice print yet (run voice-print to generate).[/dim]")
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")


@client_group.command(name="set-default")
@click.argument("slug")
def client_set_default(slug):
    """Set the default client."""
    try:
        set_default_client(slug)
        console.print(f"[green]Default client set to:[/green] {slug}")
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")


# ---------------------------------------------------------------------------
# Pipeline Commands
# ---------------------------------------------------------------------------


@cli.command()
@click.option(
    "--input",
    "-i",
    "input_path",
    required=True,
    type=click.Path(exists=True),
    help="Transcript file or directory",
)
@click.pass_context
def parse(ctx, input_path):
    """Parse merged markdown files into the database."""
    db_path = ctx.obj["db_path"]
    client_config = _get_client_config(ctx)
    input_path = Path(input_path)

    with Database(db_path) as db:
        repo = Repository(db)

        # Split files
        if input_path.is_dir():
            console.print(f"Scanning [bold]{input_path}[/bold] for transcript files...")
            records = split_all_files(input_path)
        else:
            records = split_merged_file(input_path)

        console.print(f"Found [bold]{len(records)}[/bold] individual call records.")

        new_count = 0
        skip_count = 0

        for record in records:
            if repo.call_exists(record.original_filename):
                skip_count += 1
                continue

            # Parse metadata and speaker turns
            metadata = parse_metadata(
                record.raw_text, record.source_file, record.original_filename,
                coach_name=client_config.name, coach_email=client_config.email,
            )
            turns = parse_speaker_turns(record.raw_text)

            if not turns:
                console.print(
                    f"  [yellow]Warning:[/yellow] No speaker turns found in {record.original_filename}"
                )
                continue

            call_id = repo.insert_call(metadata, turns)
            new_count += 1

            if new_count % 10 == 0:
                console.print(f"  Parsed {new_count} calls...")

        console.print()
        console.print(f"[green]Done![/green] Parsed [bold]{new_count}[/bold] new calls.")
        if skip_count:
            console.print(f"Skipped [dim]{skip_count}[/dim] already-parsed calls.")
        console.print(f"Total calls in database: [bold]{repo.get_call_count()}[/bold]")


@cli.command()
@click.pass_context
def status(ctx):
    """Show processing progress."""
    db_path = ctx.obj["db_path"]
    client_config = _get_client_config(ctx)

    if not db_path.exists():
        console.print("[yellow]No database found.[/yellow] Run 'parse' or 'ingest' first.")
        return

    with Database(db_path) as db:
        repo = Repository(db)
        summary = repo.get_progress_summary()

        console.print()
        console.print(f"[bold]ContentSifter Status[/bold] [dim]({client_config.name})[/dim]")
        console.print()

        # Progress table
        table = Table(title="Processing Progress")
        table.add_column("Stage", style="cyan")
        table.add_column("Completed", justify="right")
        table.add_column("Total", justify="right")
        table.add_column("Progress", justify="right")

        total = summary["total_calls"]
        for stage in ["parsed", "chunked", "extracted"]:
            completed = summary["stages"].get(stage, 0)
            pct = f"{completed / total * 100:.0f}%" if total else "0%"
            table.add_row(stage.capitalize(), str(completed), str(total), pct)

        console.print(table)

        # Content items count
        try:
            row = db.conn.execute("SELECT COUNT(*) as cnt FROM content_items").fetchone()
            content_count = row["cnt"]
            if content_count > 0:
                console.print()
                ci_table = Table(title="Ingested Content Items")
                ci_table.add_column("Type", style="cyan")
                ci_table.add_column("Count", justify="right")
                rows = db.conn.execute(
                    "SELECT content_type, COUNT(*) as cnt FROM content_items GROUP BY content_type ORDER BY cnt DESC"
                ).fetchall()
                for r in rows:
                    ci_table.add_row(r["content_type"], str(r["cnt"]))
                ci_table.add_row("[bold]Total[/bold]", f"[bold]{content_count}[/bold]")
                console.print(ci_table)
        except Exception:
            pass

        # Extraction counts
        if summary["total_extractions"] > 0:
            console.print()
            ext_table = Table(title="Extractions by Category")
            ext_table.add_column("Category", style="cyan")
            ext_table.add_column("Count", justify="right")

            category_labels = {
                "qa": "Q&As",
                "testimonial": "Testimonials",
                "playbook": "Playbooks",
                "story": "Stories",
            }
            for cat, count in summary["extractions"].items():
                ext_table.add_row(category_labels.get(cat, cat), str(count))
            ext_table.add_row(
                "[bold]Total[/bold]",
                f"[bold]{summary['total_extractions']}[/bold]",
            )

            console.print(ext_table)


@cli.command()
@click.option("--call-id", type=int, help="Process a specific call")
@click.option("--limit", type=int, help="Max calls to process")
@click.option("--force", is_flag=True, help="Re-process already chunked calls")
@click.pass_context
def chunk(ctx, call_id, limit, force):
    """Run topic chunking on parsed calls."""
    db_path = ctx.obj["db_path"]
    llm = create_llm_client(ctx.obj["llm_mode"], ctx.obj["model"])

    with Database(db_path) as db:
        repo = Repository(db)

        if call_id:
            call_ids = [call_id]
        else:
            call_ids = repo.get_calls_needing_stage("chunked")
            if limit:
                call_ids = call_ids[:limit]

        if not call_ids:
            console.print("[green]All calls already chunked.[/green]")
            return

        console.print(f"Chunking [bold]{len(call_ids)}[/bold] calls...")

        for i, cid in enumerate(call_ids):
            call = repo.get_call_by_id(cid)
            if not call:
                continue

            turns = repo.get_turns_for_call(cid)
            console.print(
                f"  [{i + 1}/{len(call_ids)}] {call['title'][:60]}... "
                f"({len(turns)} turns)"
            )

            try:
                chunks = chunk_transcript(
                    cid, call["title"], call["call_date"],
                    call["call_type"], turns, llm,
                )
                repo.insert_topic_chunks(cid, chunks)
                console.print(f"    [green]{len(chunks)} topic segments[/green]")
            except Exception as e:
                console.print(f"    [red]Error: {e}[/red]")

        console.print(f"\n[green]Done![/green] Chunking complete.")


@cli.command()
@click.option("--call-id", type=int, help="Process a specific call")
@click.option("--limit", type=int, help="Max calls to process")
@click.option("--force", is_flag=True, help="Re-process already extracted calls")
@click.pass_context
def extract(ctx, call_id, limit, force):
    """Extract content from chunked calls."""
    db_path = ctx.obj["db_path"]
    client_config = _get_client_config(ctx)
    llm = create_llm_client(ctx.obj["llm_mode"], ctx.obj["model"])

    with Database(db_path) as db:
        repo = Repository(db)

        if call_id:
            call_ids = [call_id]
        else:
            call_ids = repo.get_calls_needing_stage("extracted")
            if limit:
                call_ids = call_ids[:limit]

        if not call_ids:
            console.print("[green]All calls already extracted.[/green]")
            return

        console.print(f"Extracting from [bold]{len(call_ids)}[/bold] calls...")
        total_extractions = 0

        for i, cid in enumerate(call_ids):
            call = repo.get_call_by_id(cid)
            if not call:
                continue

            chunks = repo.get_chunks_for_call(cid)
            if not chunks:
                console.print(
                    f"  [{i + 1}/{len(call_ids)}] {call['title'][:60]}... "
                    f"[yellow]no chunks, skipping[/yellow]"
                )
                continue

            console.print(
                f"  [{i + 1}/{len(call_ids)}] {call['title'][:60]}... "
                f"({len(chunks)} chunks)"
            )

            call_extractions = 0
            for chunk_data in chunks:
                turns = repo.get_turns_for_range(
                    cid, chunk_data["start_turn_index"], chunk_data["end_turn_index"]
                )
                if not turns:
                    continue

                try:
                    extractions = extract_from_chunk(
                        turns,
                        call["call_type"],
                        call["call_date"],
                        chunk_data["topic_title"],
                        chunk_data["topic_summary"],
                        llm,
                        coach_name=client_config.name,
                        coach_email=client_config.email,
                    )
                    if extractions:
                        repo.insert_extractions(cid, chunk_data["id"], extractions)
                        call_extractions += len(extractions)
                except Exception as e:
                    console.print(f"    [red]Error on chunk '{chunk_data['topic_title']}': {e}[/red]")

            repo.mark_extracted(cid)
            total_extractions += call_extractions
            console.print(f"    [green]{call_extractions} items extracted[/green]")

        console.print(
            f"\n[green]Done![/green] Extracted [bold]{total_extractions}[/bold] "
            f"items from {len(call_ids)} calls."
        )


@cli.command()
@click.option(
    "--input", "-i", "input_path",
    type=click.Path(exists=True),
    help="Transcript file or directory (runs parse first if provided)",
)
@click.option("--limit", type=int, help="Max calls to process per stage")
@click.option("--dry-run", is_flag=True, help="Show what would be processed")
@click.pass_context
def sift(ctx, input_path, limit, dry_run):
    """Run full pipeline: parse -> chunk -> extract."""
    db_path = ctx.obj["db_path"]

    # Step 1: Parse (if input provided)
    if input_path:
        console.print("[bold]Step 1/3: Parsing transcripts...[/bold]")
        ctx.invoke(parse, input_path=input_path)
        console.print()

    with Database(db_path) as db:
        repo = Repository(db)

        # Step 2: Chunk
        needs_chunking = repo.get_calls_needing_stage("chunked")
        if limit:
            needs_chunking = needs_chunking[:limit]

        if dry_run:
            console.print(f"[bold]Would chunk:[/bold] {len(needs_chunking)} calls")
            needs_extraction = repo.get_calls_needing_stage("extracted")
            if limit:
                needs_extraction = needs_extraction[:limit]
            console.print(f"[bold]Would extract:[/bold] {len(needs_extraction)} calls")
            return

    if needs_chunking:
        console.print("[bold]Step 2/3: Topic chunking...[/bold]")
        ctx.invoke(chunk, call_id=None, limit=limit, force=False)
        console.print()

    # Step 3: Extract
    with Database(db_path) as db:
        repo = Repository(db)
        needs_extraction = repo.get_calls_needing_stage("extracted")
        if limit:
            needs_extraction = needs_extraction[:limit]

    if needs_extraction:
        console.print("[bold]Step 3/3: Content extraction...[/bold]")
        ctx.invoke(extract, call_id=None, limit=limit, force=False)
        console.print()

    # Show final status
    console.print("[bold]Pipeline complete![/bold]")
    ctx.invoke(status)


@cli.command()
@click.pass_context
def stats(ctx):
    """Show detailed database statistics."""
    db_path = ctx.obj["db_path"]

    if not db_path.exists():
        console.print("[yellow]No database found.[/yellow] Run 'parse' first.")
        return

    with Database(db_path) as db:
        repo = Repository(db)

        # Call type breakdown
        rows = db.conn.execute(
            "SELECT call_type, COUNT(*) as cnt FROM calls GROUP BY call_type ORDER BY cnt DESC"
        ).fetchall()

        console.print()
        table = Table(title="Calls by Type")
        table.add_column("Type", style="cyan")
        table.add_column("Count", justify="right")
        for r in rows:
            table.add_row(r["call_type"], str(r["cnt"]))
        console.print(table)

        # Date range
        row = db.conn.execute(
            "SELECT MIN(call_date) as earliest, MAX(call_date) as latest FROM calls"
        ).fetchone()
        if row and row["earliest"]:
            console.print(
                f"\nDate range: [bold]{row['earliest']}[/bold] to [bold]{row['latest']}[/bold]"
            )

        # Total turns
        row = db.conn.execute(
            "SELECT COUNT(*) as cnt, SUM(turn_count) as turns FROM calls"
        ).fetchone()
        console.print(f"Total calls: [bold]{row['cnt']}[/bold]")
        console.print(f"Total speaker turns: [bold]{row['turns']}[/bold]")

        # Tag counts
        rows = db.conn.execute(
            """SELECT t.name, COUNT(*) as cnt FROM tags t
               JOIN extraction_tags et ON t.id = et.tag_id
               GROUP BY t.name ORDER BY cnt DESC LIMIT 20"""
        ).fetchall()
        if rows:
            console.print()
            tag_table = Table(title="Top Tags")
            tag_table.add_column("Tag", style="cyan")
            tag_table.add_column("Count", justify="right")
            for r in rows:
                tag_table.add_row(r["name"], str(r["cnt"]))
            console.print(tag_table)


@cli.command()
@click.argument("query")
@click.option("--semantic", is_flag=True, help="Use Claude for semantic search")
@click.option("--category", "-c", multiple=True, help="Filter by category (qa, testimonial, playbook, story)")
@click.option("--tag", "-t", multiple=True, help="Filter by tag")
@click.option("--date-from", help="Filter from date (YYYY-MM-DD)")
@click.option("--date-to", help="Filter to date (YYYY-MM-DD)")
@click.option("--call-type", help="Filter by call type")
@click.option("--min-quality", type=int, help="Minimum quality score (1-5)")
@click.option("--limit", type=int, default=20, help="Max results")
@click.option(
    "--output-format",
    type=click.Choice(["table", "json", "full"]),
    default="table",
    help="Output format",
)
@click.pass_context
def search(ctx, query, semantic, category, tag, date_from, date_to,
           call_type, min_quality, limit, output_format):
    """Search extracted content."""
    import json as json_mod
    from contentsifter.search.filters import SearchFilters
    from contentsifter.search.keyword import keyword_search
    from contentsifter.search.semantic import semantic_search

    db_path = ctx.obj["db_path"]

    filters = SearchFilters(
        categories=list(category),
        tags=list(tag),
        date_from=date_from,
        date_to=date_to,
        call_types=[call_type] if call_type else [],
        min_quality=min_quality,
        limit=limit,
    )

    with Database(db_path) as db:
        if semantic:
            llm = create_llm_client(ctx.obj["llm_mode"], ctx.obj["model"])
            results = semantic_search(db, query, llm, filters)
        else:
            results = keyword_search(db, query, filters)

    if not results:
        console.print("[yellow]No results found.[/yellow]")
        return

    if output_format == "json":
        console.print(json_mod.dumps(results, indent=2))
    elif output_format == "full":
        for r in results:
            console.print(f"\n[bold cyan]{r['title']}[/bold cyan]")
            console.print(f"[dim]{r['category'].upper()} | Quality: {r['quality_score']}/5 | {r['call_date']}[/dim]")
            if r.get("tags"):
                console.print(f"[dim]Tags: {', '.join(r['tags'])}[/dim]")
            console.print(f"\n{r['content']}")
            if r.get("raw_quote"):
                console.print(f'\n[italic]> "{r["raw_quote"]}"[/italic]')
            console.print(f"[dim]From: {r['call_title']}[/dim]")
            console.print("─" * 60)
    else:
        table = Table(title=f"Search: {query}")
        table.add_column("#", style="dim", width=3)
        table.add_column("Cat", style="cyan", width=5)
        table.add_column("Q", width=2)
        table.add_column("Title", style="bold")
        table.add_column("Date", style="dim", width=10)
        table.add_column("Tags", style="dim")

        cat_abbr = {"qa": "Q&A", "testimonial": "WIN", "playbook": "PLAY", "story": "STORY"}
        for i, r in enumerate(results):
            table.add_row(
                str(i + 1),
                cat_abbr.get(r["category"], r["category"]),
                str(r["quality_score"]),
                r["title"][:50],
                r["call_date"],
                ", ".join(r.get("tags", [])[:3]),
            )
        console.print(table)
        console.print(f"\n[dim]Showing {len(results)} results. Use --output-format full for details.[/dim]")


@cli.command()
@click.option("--query", "-q", required=True, help="Search query for source material")
@click.option(
    "--format", "-f", "format_type",
    type=click.Choice([
        "linkedin", "newsletter", "thread", "playbook",
        "video-script", "carousel",
        "email-welcome", "email-weekly", "email-sales",
    ]),
    required=True,
    help="Output format",
)
@click.option("--topic", help="Topic/title for the generated content")
@click.option("--category", "-c", multiple=True, help="Filter source by category")
@click.option("--min-quality", type=int, default=3, help="Minimum quality for source material")
@click.option("--limit", type=int, default=10, help="Max source items to use")
@click.option("--voice-print/--no-voice-print", "use_voice_print", default=True,
              help="Use voice print for tone matching (default: on if voice-print.md exists)")
@click.option("--save", is_flag=True, help="Save draft to content/drafts/")
@click.option("--skip-gates", is_flag=True, help="Skip AI detection and voice matching gates")
@click.pass_context
def generate(ctx, query, format_type, topic, category, min_quality, limit,
             use_voice_print, save, skip_gates):
    """Generate content drafts from search results."""
    from datetime import datetime

    from contentsifter.generate.drafts import generate_draft
    from contentsifter.planning.voiceprint import load_voice_print
    from contentsifter.search.filters import SearchFilters
    from contentsifter.search.keyword import keyword_search

    db_path = ctx.obj["db_path"]
    client_config = _get_client_config(ctx)
    llm = create_llm_client(ctx.obj["llm_mode"], ctx.obj["model"])

    # Load voice print if available and requested
    voice_print = None
    if use_voice_print:
        voice_print = load_voice_print(path=client_config.voice_print_path)
        if voice_print:
            console.print("[dim]Using voice print for tone matching.[/dim]")

    filters = SearchFilters(
        categories=list(category),
        min_quality=min_quality,
        limit=limit,
    )

    with Database(db_path) as db:
        results = keyword_search(db, query, filters)

    if not results:
        console.print("[yellow]No source material found for that query.[/yellow]")
        return

    console.print(f"Found [bold]{len(results)}[/bold] source items. Generating {format_type} draft...")

    save_to = None
    if save:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        save_to = client_config.drafts_dir / f"{format_type}-{timestamp}.md"

    if not skip_gates and voice_print:
        console.print("[dim]Content gates enabled (AI detection + voice matching).[/dim]")

    draft = generate_draft(results, format_type, llm, topic,
                           voice_print=voice_print, save_to=save_to,
                           skip_gates=skip_gates)

    console.print()
    console.print("[bold]Generated Draft:[/bold]")
    console.print("=" * 60)
    console.print(draft)
    console.print("=" * 60)
    if save_to:
        console.print(f"\n[green]Saved to:[/green] {save_to}")


@cli.command(name="export")
@click.option(
    "--output", "-o",
    default=None,
    type=click.Path(),
    help="Output directory",
)
@click.pass_context
def export_cmd(ctx, output):
    """Export extracted data as JSON files."""
    from contentsifter.storage.export import export_all

    db_path = ctx.obj["db_path"]
    client_config = _get_client_config(ctx)
    output_dir = Path(output) if output else client_config.exports_dir

    with Database(db_path) as db:
        summary = export_all(db, output_dir)

    console.print(f"[green]Exported {summary['total']} extractions to {output_dir}[/green]")
    console.print(f"  By category: {summary['by_category']}")
    console.print(f"  Calls with extractions: {summary['calls_with_extractions']}")


# ---------------------------------------------------------------------------
# Content Ingestion Commands
# ---------------------------------------------------------------------------


@cli.command()
@click.argument("input_path", required=False, type=click.Path(exists=True))
@click.option(
    "--type", "-t", "content_type",
    type=click.Choice(["linkedin", "email", "newsletter", "blog", "transcript", "other"]),
    default=None,
    help="Content type (auto-detected from filename if not specified)",
)
@click.option("--status-only", "show_status", is_flag=True, help="Show ingested content counts")
@click.pass_context
def ingest(ctx, input_path, content_type, show_status):
    """Ingest content files into the database.

    Accepts markdown files with content items separated by --- dividers.
    Use --type to specify what kind of content, or let it auto-detect from filenames.
    """
    from contentsifter.ingest.reader import ingest_path, detect_content_type

    db_path = ctx.obj["db_path"]
    client_config = _get_client_config(ctx)

    if show_status:
        if not db_path.exists():
            console.print("[yellow]No database found.[/yellow]")
            return
        with Database(db_path) as db:
            try:
                rows = db.conn.execute(
                    "SELECT content_type, COUNT(*) as cnt, SUM(char_count) as chars "
                    "FROM content_items GROUP BY content_type ORDER BY cnt DESC"
                ).fetchall()
                if not rows:
                    console.print("[yellow]No content items ingested yet.[/yellow]")
                    return
                table = Table(title=f"Ingested Content ({client_config.name})")
                table.add_column("Type", style="cyan")
                table.add_column("Count", justify="right")
                table.add_column("Total Chars", justify="right")
                total_count = 0
                total_chars = 0
                for r in rows:
                    table.add_row(r["content_type"], str(r["cnt"]), f"{r['chars']:,}")
                    total_count += r["cnt"]
                    total_chars += r["chars"]
                table.add_row("[bold]Total[/bold]", f"[bold]{total_count}[/bold]", f"[bold]{total_chars:,}[/bold]")
                console.print(table)
            except Exception:
                console.print("[yellow]No content items table found.[/yellow]")
        return

    if not input_path:
        console.print("[red]Error:[/red] Provide a file/directory path, or use --status-only.")
        return

    input_path = Path(input_path)

    # For transcript type, delegate to the existing parse command
    if content_type == "transcript":
        console.print("Delegating to transcript parser...")
        ctx.invoke(parse, input_path=str(input_path))
        return

    with Database(db_path) as db:
        items = ingest_path(
            db, input_path, content_type=content_type, author=client_config.name,
        )

    console.print(f"[green]Done![/green] Ingested [bold]{len(items)}[/bold] content items.")
    for ct, count in _count_by_type(items):
        console.print(f"  {ct}: {count}")


def _count_by_type(items: list[dict]) -> list[tuple[str, int]]:
    """Count items by content_type."""
    counts: dict[str, int] = {}
    for item in items:
        ct = item.get("content_type", "other")
        counts[ct] = counts.get(ct, 0) + 1
    return sorted(counts.items())


# ---------------------------------------------------------------------------
# Voice Capture Interview Commands
# ---------------------------------------------------------------------------


@cli.group(name="interview")
def interview_group():
    """Voice capture interview: generate questionnaires and ingest transcripts."""
    pass


@interview_group.command(name="generate")
@click.option("--niche", "-n", type=str, default=None,
              help="Client's niche/industry for additional targeted prompts")
@click.option("--output", "-o", type=click.Path(), default=None,
              help="Output path (default: {content_dir}/interview-guide.md)")
@click.pass_context
def interview_generate(ctx, niche, output):
    """Generate a voice capture interview questionnaire.

    Creates a markdown file with 95+ questions across 9 categories that the client
    reads aloud and answers using any voice transcription tool.
    """
    from contentsifter.interview.generator import generate_questionnaire
    from contentsifter.interview.prompts import get_prompt_count

    client_config = _get_client_config(ctx)

    output_path = Path(output) if output else client_config.content_dir / "interview-guide.md"

    llm = None
    if niche:
        try:
            llm = create_llm_client(ctx.obj["llm_mode"], ctx.obj["model"])
        except Exception:
            console.print("[yellow]Warning:[/yellow] No LLM available — skipping niche prompt generation.")

    console.print(f"Generating interview questionnaire ({get_prompt_count()} universal prompts)...")
    if niche:
        console.print(f"[dim]Adding niche-specific prompts for: {niche}[/dim]")

    markdown, saved_path = generate_questionnaire(
        client_name=client_config.name,
        niche=niche,
        llm_client=llm,
        output_path=output_path,
    )

    console.print(f"\n[green]Questionnaire saved to:[/green] {saved_path}")
    console.print(f"[dim]Send this file to {client_config.name or 'the client'} to record their answers.[/dim]")


@interview_group.command(name="ingest")
@click.argument("transcript_path", type=click.Path(exists=True))
@click.option("--questionnaire", "-q", type=click.Path(exists=True), default=None,
              help="Path to the questionnaire used (default: {content_dir}/interview-guide.md)")
@click.pass_context
def interview_ingest(ctx, transcript_path, questionnaire):
    """Ingest a voice transcript from a completed interview.

    Parses the transcript by matching questions from the questionnaire,
    then stores each answer as a content item in the database.
    """
    from contentsifter.interview.parser import parse_interview_transcript

    db_path = ctx.obj["db_path"]
    client_config = _get_client_config(ctx)

    transcript_path = Path(transcript_path)
    questionnaire_path = (
        Path(questionnaire) if questionnaire
        else client_config.content_dir / "interview-guide.md"
    )

    if not questionnaire_path.exists():
        console.print(f"[red]Error:[/red] Questionnaire not found at {questionnaire_path}")
        console.print("Run 'contentsifter interview generate' first, or provide --questionnaire path.")
        return

    console.print(f"Parsing transcript: {transcript_path}")
    console.print(f"Using questionnaire: {questionnaire_path}")

    with Database(db_path) as db:
        items = parse_interview_transcript(
            transcript_path,
            questionnaire_path,
            db,
            author=client_config.name,
        )

    console.print(f"\n[green]Done![/green] Parsed [bold]{len(items)}[/bold] answers from the transcript.")
    if items:
        # Show category breakdown from metadata
        cats: dict[str, int] = {}
        for item in items:
            meta = item.get("metadata", {})
            cat = meta.get("category", "unknown") if meta else "unknown"
            cats[cat] = cats.get(cat, 0) + 1
        for cat, count in sorted(cats.items()):
            console.print(f"  {cat}: {count}")

    console.print(f"\n[dim]Next steps:[/dim]")
    console.print(f"  contentsifter voice-print --force    # Build/rebuild voice print")
    console.print(f"  contentsifter generate -q 'topic' -f linkedin  # Generate content")


@interview_group.command(name="status")
@click.pass_context
def interview_status(ctx):
    """Show interview ingestion status."""
    db_path = ctx.obj["db_path"]
    client_config = _get_client_config(ctx)

    if not db_path.exists():
        console.print("[yellow]No database found.[/yellow]")
        return

    with Database(db_path) as db:
        try:
            # Total interview items
            row = db.conn.execute(
                "SELECT COUNT(*) as cnt, COALESCE(SUM(char_count), 0) as chars "
                "FROM content_items WHERE content_type = 'interview'"
            ).fetchone()
            total = row["cnt"]
            total_chars = row["chars"]

            if total == 0:
                console.print(f"[yellow]No interview items found for {client_config.name}.[/yellow]")
                console.print("[dim]Run 'contentsifter interview generate' then 'contentsifter interview ingest'.[/dim]")
                return

            console.print(f"\n[bold]Interview Status[/bold] [dim]({client_config.name})[/dim]\n")
            console.print(f"Total interview answers: [bold]{total}[/bold] ({total_chars:,} chars)")

            # Breakdown by category (from metadata_json)
            rows = db.conn.execute(
                """SELECT
                     json_extract(metadata_json, '$.category') as category,
                     COUNT(*) as cnt
                   FROM content_items
                   WHERE content_type = 'interview' AND metadata_json IS NOT NULL
                   GROUP BY category
                   ORDER BY cnt DESC"""
            ).fetchall()

            if rows:
                console.print()
                table = Table(title="Interview Items by Category")
                table.add_column("Category", style="cyan")
                table.add_column("Count", justify="right")
                for r in rows:
                    table.add_row(r["category"] or "uncategorized", str(r["cnt"]))
                console.print(table)

            # Average answer length
            row = db.conn.execute(
                "SELECT AVG(char_count) as avg_len FROM content_items WHERE content_type = 'interview'"
            ).fetchone()
            if row and row["avg_len"]:
                console.print(f"\nAverage answer length: {int(row['avg_len']):,} chars")

        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")


# ---------------------------------------------------------------------------
# Content Planning Commands
# ---------------------------------------------------------------------------


@cli.command(name="init-templates")
@click.option("--force", is_flag=True, help="Overwrite existing template files")
@click.pass_context
def init_templates(ctx, force):
    """Generate content planning template files in content/templates/."""
    from contentsifter.planning.templates_static import ALL_TEMPLATES
    from contentsifter.planning.writer import ensure_content_dirs, write_markdown

    ensure_content_dirs()
    written = 0
    skipped = 0

    for name, (path, content) in ALL_TEMPLATES.items():
        if write_markdown(Path(path), content, force):
            written += 1
            console.print(f"  [green]Wrote[/green] {path}")
        else:
            skipped += 1
            console.print(f"  [dim]Skipped[/dim] {path} (exists, use --force)")

    console.print()
    console.print(f"[green]Done![/green] Wrote {written} template files.")
    if skipped:
        console.print(f"[dim]Skipped {skipped} existing files.[/dim]")


@cli.command(name="voice-print")
@click.option("--force", is_flag=True, help="Regenerate even if voice-print.md exists")
@click.option("--sample-size", type=int, default=100, help="Turns per sample bucket")
@click.pass_context
def voice_print_cmd(ctx, force, sample_size):
    """Analyze speaking/writing patterns and generate a voice profile."""
    from contentsifter.planning.voiceprint import (
        analyze_voice,
        get_coach_turn_stats,
        get_content_item_stats,
        load_voice_print,
        save_voice_print,
    )

    client_config = _get_client_config(ctx)
    vp_path = client_config.voice_print_path

    if not force and load_voice_print(path=vp_path) is not None:
        console.print(f"[yellow]Voice print already exists:[/yellow] {vp_path}")
        console.print("Use --force to regenerate.")
        return

    db_path = ctx.obj["db_path"]
    llm = create_llm_client(ctx.obj["llm_mode"], ctx.obj["model"])

    with Database(db_path) as db:
        # Check for speaker turns (transcript data)
        turn_stats = get_coach_turn_stats(db, coach_name=client_config.name, coach_email=client_config.email)
        # Check for content items (ingested written content)
        content_stats = get_content_item_stats(db)

        total_items = turn_stats["turn_count"] + content_stats["item_count"]
        if total_items == 0:
            console.print("[red]No content found.[/red] Ingest some content or parse transcripts first.")
            return

        if turn_stats["turn_count"] > 0:
            console.print(
                f"Found [bold]{turn_stats['turn_count']:,}[/bold] speaker turns "
                f"across [bold]{turn_stats['call_count']}[/bold] calls"
            )
        if content_stats["item_count"] > 0:
            console.print(
                f"Found [bold]{content_stats['item_count']:,}[/bold] content items "
                f"({content_stats['total_chars']:,} chars)"
            )
        console.print("Running 3-pass voice analysis (this takes a few minutes)...")
        console.print()

        result = analyze_voice(
            db, llm, sample_per_bucket=sample_size,
            coach_name=client_config.name, coach_email=client_config.email,
        )

    out_path = save_voice_print(result, path=vp_path)
    console.print(f"[green]Voice print saved to:[/green] {out_path}")


@cli.command(name="plan-week")
@click.option("--week-of", type=str, help="Start date (YYYY-MM-DD, defaults to next Monday)")
@click.option("--topic-focus", type=str, help="Optional tag to emphasize this week")
@click.option("--no-llm", is_flag=True, help="Generate calendar without LLM drafts")
@click.option("--skip-gates", is_flag=True, help="Skip AI detection and voice matching gates")
@click.pass_context
def plan_week(ctx, week_of, topic_focus, no_llm, skip_gates):
    """Generate a weekly content calendar with suggested content for each day."""
    from contentsifter.planning.calendar import generate_calendar

    db_path = ctx.obj["db_path"]
    client_config = _get_client_config(ctx)
    llm = None
    if not no_llm:
        llm = create_llm_client(ctx.obj["llm_mode"], ctx.obj["model"])

    with Database(db_path) as db:
        console.print("Generating weekly content calendar...")
        if topic_focus:
            console.print(f"[dim]Topic focus: {topic_focus}[/dim]")
        if no_llm:
            console.print("[dim]No-LLM mode: source material only, no drafts.[/dim]")
        else:
            console.print("[dim]Generating drafts for each day (this may take a few minutes)...[/dim]")
            if not skip_gates:
                console.print("[dim]Content gates enabled (AI detection + voice matching).[/dim]")
        console.print()

        markdown, output_path = generate_calendar(
            db,
            week_of=week_of,
            topic_focus=topic_focus,
            llm_client=llm,
            use_llm=not no_llm,
            skip_gates=skip_gates,
            calendar_dir=client_config.calendar_dir,
            voice_print_path=client_config.voice_print_path,
        )

    console.print(f"[green]Calendar saved to:[/green] {output_path}")
    console.print()
    console.print(markdown)


if __name__ == "__main__":
    cli()
