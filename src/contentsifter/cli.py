"""CLI entry point for ContentSifter."""

import logging
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from contentsifter.config import DEFAULT_DB_PATH, DEFAULT_TRANSCRIPTS_DIR
from contentsifter.extraction.chunker import chunk_transcript
from contentsifter.extraction.extractor import extract_from_chunk
from contentsifter.llm.client import create_client
from contentsifter.parser.metadata import parse_metadata
from contentsifter.parser.splitter import split_all_files, split_merged_file
from contentsifter.parser.turns import parse_speaker_turns
from contentsifter.storage.database import Database
from contentsifter.storage.repository import Repository

console = Console(force_terminal=True)


@click.group()
@click.option(
    "--db",
    default=str(DEFAULT_DB_PATH),
    help="Database path",
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
def cli(ctx, db, llm_mode, model, verbose):
    """ContentSifter - Extract and search coaching call transcripts."""
    ctx.ensure_object(dict)
    ctx.obj["db_path"] = Path(db)
    ctx.obj["llm_mode"] = llm_mode
    ctx.obj["model"] = model
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO, format="%(message)s")


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
                record.raw_text, record.source_file, record.original_filename
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

    if not db_path.exists():
        console.print("[yellow]No database found.[/yellow] Run 'parse' first.")
        return

    with Database(db_path) as db:
        repo = Repository(db)
        summary = repo.get_progress_summary()

        console.print()
        console.print("[bold]ContentSifter Status[/bold]")
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
    llm = create_client(ctx.obj["llm_mode"], ctx.obj["model"])

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
    llm = create_client(ctx.obj["llm_mode"], ctx.obj["model"])

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
            llm = create_client(ctx.obj["llm_mode"], ctx.obj["model"])
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

    from contentsifter.config import DRAFTS_DIR
    from contentsifter.generate.drafts import generate_draft
    from contentsifter.planning.voiceprint import load_voice_print
    from contentsifter.search.filters import SearchFilters
    from contentsifter.search.keyword import keyword_search

    db_path = ctx.obj["db_path"]
    llm = create_client(ctx.obj["llm_mode"], ctx.obj["model"])

    # Load voice print if available and requested
    voice_print = None
    if use_voice_print:
        voice_print = load_voice_print()
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
        save_to = DRAFTS_DIR / f"{format_type}-{timestamp}.md"

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
    default=str(DEFAULT_DB_PATH.parent / "exports"),
    type=click.Path(),
    help="Output directory",
)
@click.pass_context
def export_cmd(ctx, output):
    """Export extracted data as JSON files."""
    from contentsifter.storage.export import export_all

    db_path = ctx.obj["db_path"]
    output_dir = Path(output)

    with Database(db_path) as db:
        summary = export_all(db, output_dir)

    console.print(f"[green]Exported {summary['total']} extractions to {output_dir}[/green]")
    console.print(f"  By category: {summary['by_category']}")
    console.print(f"  Calls with extractions: {summary['calls_with_extractions']}")


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
    """Analyze coach's speaking patterns and generate a voice profile."""
    from contentsifter.config import VOICE_PRINT_PATH
    from contentsifter.planning.voiceprint import (
        analyze_voice,
        get_coach_turn_stats,
        load_voice_print,
        save_voice_print,
    )

    if not force and load_voice_print() is not None:
        console.print(f"[yellow]Voice print already exists:[/yellow] {VOICE_PRINT_PATH}")
        console.print("Use --force to regenerate.")
        return

    db_path = ctx.obj["db_path"]
    llm = create_client(ctx.obj["llm_mode"], ctx.obj["model"])

    with Database(db_path) as db:
        stats = get_coach_turn_stats(db)
        console.print(
            f"Analyzing [bold]{stats['turn_count']:,}[/bold] coach turns "
            f"across [bold]{stats['call_count']}[/bold] calls..."
        )
        console.print("Running 3-pass voice analysis (this takes a few minutes)...")
        console.print()

        result = analyze_voice(db, llm, sample_per_bucket=sample_size)

    out_path = save_voice_print(result)
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
    llm = None
    if not no_llm:
        llm = create_client(ctx.obj["llm_mode"], ctx.obj["model"])

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
        )

    console.print(f"[green]Calendar saved to:[/green] {output_path}")
    console.print()
    console.print(markdown)


if __name__ == "__main__":
    cli()
