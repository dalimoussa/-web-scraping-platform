"""
Main CLI interface for the Japanese Public Officials scraper.
Uses Typer for command-line interface with Rich for beautiful output.
"""

from pathlib import Path
from typing import Optional
import sys

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich import print as rprint

from src.scrapers.officials import OfficialsScraper
from src.scrapers.elections import ElectionsScraper
from src.scrapers.funding import FundingScraper
from src.core.csv_exporter import CSVExporter
from src.core.config import get_config
from src.core.logger import get_logger, ScraperLogger


app = typer.Typer(
    name="officials-scraper",
    help="Japanese Public Officials Data Collection Platform",
    add_completion=False,
)

console = Console()


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    config = get_config()
    log_config = config.logging_config
    
    level = "DEBUG" if verbose else log_config.get('level', 'INFO')
    
    return ScraperLogger.get_logger(
        name="scraper",
        log_file=log_config.get('file', 'logs/scraper.log'),
        level=level,
        max_bytes=log_config.get('max_bytes', 10485760),
        backup_count=log_config.get('backup_count', 5),
        console_output=log_config.get('console_output', True),
    )


@app.command()
def scrape_officials(
    limit: Optional[int] = typer.Option(None, "--limit", "-l", help="Limit number of officials to scrape"),
    use_cache: bool = typer.Option(True, "--use-cache/--no-cache", help="Use cached responses"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose logging"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output CSV filename"),
):
    """
    Scrape public official information (names, ages, factions, SNS links).
    This is the highest priority data collection.
    """
    logger = setup_logging(verbose)
    console.print("\n[bold cyan]🏛️  Scraping Public Officials Data[/bold cyan]\n")
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            # Initialize scraper
            task = progress.add_task("Initializing scraper...", total=None)
            scraper = OfficialsScraper()
            
            # Scrape data
            progress.update(task, description="Collecting official data...")
            officials = scraper.scrape(limit=limit)
            sns_data = scraper.get_sns_results()
            
            # Export to CSV
            progress.update(task, description="Exporting to CSV...")
            exporter = CSVExporter()
            
            officials_file = output or "officials.csv"
            sns_file = "officials_social.csv"
            
            officials_path = exporter.export(officials, officials_file)
            sns_path = exporter.export(sns_data, sns_file) if sns_data else None
            
            progress.update(task, description="✓ Complete", completed=True)
        
        # Display results
        console.print(f"\n[bold green]✓ Success![/bold green]")
        console.print(f"  Officials collected: {len(officials)}")
        console.print(f"  SNS profiles found: {len(sns_data)}")
        console.print(f"\n[bold]Output files:[/bold]")
        console.print(f"  📄 {officials_path}")
        if sns_path:
            console.print(f"  📄 {sns_path}")
        
        # Show sample
        if officials:
            console.print(f"\n[bold]Sample (first 5 records):[/bold]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Name", style="cyan")
            table.add_column("Age", style="green")
            table.add_column("Faction", style="yellow")
            table.add_column("Office", style="blue")
            
            for official in officials[:5]:
                table.add_row(
                    official.get('name', 'N/A'),
                    str(official.get('age', 'N/A')),
                    official.get('faction', 'N/A'),
                    official.get('office_type', 'N/A'),
                )
            
            console.print(table)
        
    except Exception as e:
        logger.error(f"Failed to scrape officials: {e}", exc_info=True)
        console.print(f"\n[bold red]✗ Error:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def scrape_elections(
    limit: Optional[int] = typer.Option(None, "--limit", "-l", help="Limit number of sources to scrape"),
    include_results: bool = typer.Option(True, "--results/--no-results", help="Include election results"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose logging"),
):
    """
    Scrape election schedules and results.
    """
    logger = setup_logging(verbose)
    console.print("\n[bold cyan]🗳️  Scraping Election Data[/bold cyan]\n")
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            task = progress.add_task("Initializing scraper...", total=None)
            scraper = ElectionsScraper()
            
            # Scrape schedules
            progress.update(task, description="Collecting election schedules...")
            elections = scraper.scrape_schedules(limit=limit)
            
            # Scrape results
            results = []
            if include_results:
                progress.update(task, description="Collecting election results...")
                results = scraper.scrape_results(limit=limit)
            
            # Export
            progress.update(task, description="Exporting to CSV...")
            exporter = CSVExporter()
            
            elections_path = exporter.export(elections, "elections.csv")
            results_path = None
            if results:
                results_path = exporter.export(results, "election_results.csv")
            
            progress.update(task, description="✓ Complete", completed=True)
        
        console.print(f"\n[bold green]✓ Success![/bold green]")
        console.print(f"  Elections found: {len(elections)}")
        if results:
            console.print(f"  Results found: {len(results)}")
        console.print(f"\n[bold]Output files:[/bold]")
        console.print(f"  📄 {elections_path}")
        if results_path:
            console.print(f"  📄 {results_path}")
        
    except Exception as e:
        logger.error(f"Failed to scrape elections: {e}", exc_info=True)
        console.print(f"\n[bold red]✗ Error:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def scrape_funding(
    limit: Optional[int] = typer.Option(None, "--limit", "-l", help="Limit number of sources to scrape"),
    parse_totals: bool = typer.Option(False, "--parse-totals", help="Attempt to parse income/expense totals"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose logging"),
):
    """
    Scrape political funding/activity fund reports.
    """
    logger = setup_logging(verbose)
    console.print("\n[bold cyan]💰 Scraping Funding Data[/bold cyan]\n")
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            task = progress.add_task("Initializing scraper...", total=None)
            scraper = FundingScraper()
            
            if parse_totals:
                scraper.parse_totals = True
            
            progress.update(task, description="Collecting funding data...")
            funding = scraper.scrape(limit=limit)
            
            progress.update(task, description="Exporting to CSV...")
            exporter = CSVExporter()
            funding_path = exporter.export(funding, "funding.csv")
            
            progress.update(task, description="✓ Complete", completed=True)
        
        console.print(f"\n[bold green]✓ Success![/bold green]")
        console.print(f"  Funding records found: {len(funding)}")
        console.print(f"\n[bold]Output file:[/bold]")
        console.print(f"  📄 {funding_path}")
        
    except Exception as e:
        logger.error(f"Failed to scrape funding: {e}", exc_info=True)
        console.print(f"\n[bold red]✗ Error:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def run_all(
    limit: Optional[int] = typer.Option(None, "--limit", "-l", help="Limit per scraper"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose logging"),
):
    """
    Run all scrapers sequentially (officials, elections, funding).
    """
    logger = setup_logging(verbose)
    console.print("\n[bold cyan]🚀 Running All Scrapers[/bold cyan]\n")
    
    try:
        # 1. Officials (highest priority)
        console.print("[bold]1/3 - Scraping Officials...[/bold]")
        scraper_officials = OfficialsScraper()
        officials = scraper_officials.scrape(limit=limit)
        sns_data = scraper_officials.get_sns_results()
        console.print(f"  ✓ Collected {len(officials)} officials\n")
        
        # 2. Elections
        console.print("[bold]2/3 - Scraping Elections...[/bold]")
        scraper_elections = ElectionsScraper()
        elections = scraper_elections.scrape_schedules(limit=limit)
        results = scraper_elections.scrape_results(limit=limit)
        console.print(f"  ✓ Collected {len(elections)} elections, {len(results)} results\n")
        
        # 3. Funding
        console.print("[bold]3/3 - Scraping Funding...[/bold]")
        scraper_funding = FundingScraper()
        funding = scraper_funding.scrape(limit=limit)
        console.print(f"  ✓ Collected {len(funding)} funding records\n")
        
        # Export all
        console.print("[bold]Exporting all data to CSV...[/bold]")
        exporter = CSVExporter()
        
        datasets = {
            'officials.csv': officials,
            'officials_social.csv': sns_data,
            'elections.csv': elections,
            'election_results.csv': results,
            'funding.csv': funding,
        }
        
        paths = exporter.export_multiple(datasets)
        
        # Summary
        console.print(f"\n[bold green]✓ All scrapers complete![/bold green]\n")
        
        summary_table = Table(title="Collection Summary", show_header=True, header_style="bold magenta")
        summary_table.add_column("Dataset", style="cyan")
        summary_table.add_column("Records", style="green", justify="right")
        summary_table.add_column("Output File", style="yellow")
        
        summary_table.add_row("Officials", str(len(officials)), "officials.csv")
        summary_table.add_row("SNS Profiles", str(len(sns_data)), "officials_social.csv")
        summary_table.add_row("Elections", str(len(elections)), "elections.csv")
        summary_table.add_row("Results", str(len(results)), "election_results.csv")
        summary_table.add_row("Funding", str(len(funding)), "funding.csv")
        
        console.print(summary_table)
        console.print(f"\n[bold]All files saved to:[/bold] data/outputs/\n")
        
    except Exception as e:
        logger.error(f"Failed during full scrape: {e}", exc_info=True)
        console.print(f"\n[bold red]✗ Error:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def export(
    input_dir: str = typer.Option("data/cache", help="Input directory with cached data"),
    output_dir: str = typer.Option("data/outputs", help="Output directory for CSV files"),
):
    """
    Export cached/scraped data to CSV files.
    """
    console.print("\n[bold cyan]📤 Exporting Data[/bold cyan]\n")
    console.print(f"  Input: {input_dir}")
    console.print(f"  Output: {output_dir}\n")
    
    # This would be implemented if we have a state management system
    console.print("[yellow]Note: Export from cache not yet implemented.[/yellow]")
    console.print("[yellow]Use scrape commands which automatically export to CSV.[/yellow]\n")


@app.command()
def clear_cache():
    """Clear HTTP cache and force fresh data collection."""
    import shutil
    
    console.print("\n[bold cyan]🗑️  Clearing Cache[/bold cyan]\n")
    
    cache_dir = Path("data/cache")
    
    if not cache_dir.exists():
        console.print("[yellow]No cache directory found.[/yellow]\n")
        return
    
    try:
        # Count files before deletion
        cache_files = list(cache_dir.glob("*"))
        file_count = len(cache_files)
        
        # Clear cache
        shutil.rmtree(cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        console.print(f"[green]✓ Cleared {file_count} cached files[/green]")
        console.print("[dim]Next scrape will fetch fresh data with correct encoding.[/dim]\n")
        
    except Exception as e:
        console.print(f"[red]Error clearing cache: {e}[/red]\n")


@app.command()
def version():
    """Show version information."""
    console.print("\n[bold cyan]Japanese Public Officials Scraper[/bold cyan]")
    console.print("Version: 1.1.2")
    console.print("Release Date: 2025-10-20")
    console.print("Latest Fix: Shift_JIS encoding support for Japanese government sites\n")


@app.command()
def info():
    """Show configuration and system information."""
    config = get_config()
    
    console.print("\n[bold cyan]System Information[/bold cyan]\n")
    
    info_table = Table(show_header=False)
    info_table.add_column("Setting", style="cyan")
    info_table.add_column("Value", style="green")
    
    info_table.add_row("Default Delay", f"{config.get('scraping.default_delay', 1.5)}s")
    info_table.add_row("Max Retries", str(config.get('scraping.max_retries', 3)))
    info_table.add_row("Timeout", f"{config.get('scraping.timeout', 30)}s")
    info_table.add_row("Cache Enabled", str(config.get('scraping.use_cache', True)))
    info_table.add_row("Respect robots.txt", str(config.get('scraping.respect_robots_txt', True)))
    info_table.add_row("Output Directory", config.get('output.directory', 'data/outputs'))
    info_table.add_row("Log Level", config.get('logging.level', 'INFO'))
    
    console.print(info_table)
    console.print()


if __name__ == "__main__":
    app()
