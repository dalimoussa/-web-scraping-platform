"""
CSV export functionality with proper encoding and data normalization.
"""

import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..core.logger import get_logger


class CSVExporter:
    """
    Export data to CSV with consistent formatting.
    Handles UTF-8 with BOM for Excel compatibility.
    """
    
    def __init__(
        self,
        output_dir: str = "data/outputs",
        encoding: str = "utf-8-sig",
        delimiter: str = ",",
        quotechar: str = '"',
        date_format: str = "%Y-%m-%d",
        datetime_format: str = "%Y-%m-%d %H:%M:%S",
    ):
        """
        Initialize CSV exporter.
        
        Args:
            output_dir: Directory for output files
            encoding: File encoding (utf-8-sig for Excel)
            delimiter: CSV delimiter
            quotechar: Quote character
            date_format: Format for date fields
            datetime_format: Format for datetime fields
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.encoding = encoding
        self.delimiter = delimiter
        self.quotechar = quotechar
        self.date_format = date_format
        self.datetime_format = datetime_format
        
        self.logger = get_logger(__name__)
    
    def _normalize_value(self, value: Any) -> str:
        """
        Normalize value for CSV export.
        
        Args:
            value: Value to normalize
            
        Returns:
            String representation
        """
        if value is None:
            return ""
        
        if isinstance(value, datetime):
            return value.strftime(self.datetime_format)
        
        if isinstance(value, bool):
            return "1" if value else "0"
        
        if isinstance(value, (list, tuple)):
            return "; ".join(str(v) for v in value)
        
        if isinstance(value, dict):
            return str(value)
        
        return str(value).strip()
    
    def export(
        self,
        data: List[Dict[str, Any]],
        filename: str,
        fieldnames: Optional[List[str]] = None,
        append: bool = False,
    ) -> Path:
        """
        Export data to CSV file.
        
        Args:
            data: List of dictionaries to export
            filename: Output filename (without path)
            fieldnames: Column names (auto-detected if None)
            append: Append to existing file
            
        Returns:
            Path to created file
        """
        if not data:
            self.logger.warning(f"No data to export for {filename}")
            return self.output_dir / filename
        
        # Auto-detect fieldnames from first record
        if fieldnames is None:
            fieldnames = list(data[0].keys())
        
        output_path = self.output_dir / filename
        mode = 'a' if append and output_path.exists() else 'w'
        
        # Check if we need to write header
        write_header = mode == 'w' or not output_path.exists()
        
        try:
            with open(output_path, mode, encoding=self.encoding, newline='') as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=fieldnames,
                    delimiter=self.delimiter,
                    quotechar=self.quotechar,
                    quoting=csv.QUOTE_MINIMAL,
                    extrasaction='ignore',  # Ignore extra fields
                )
                
                if write_header:
                    writer.writeheader()
                
                # Normalize and write rows
                for row in data:
                    normalized_row = {
                        k: self._normalize_value(v)
                        for k, v in row.items()
                        if k in fieldnames
                    }
                    writer.writerow(normalized_row)
            
            record_count = len(data)
            action = "Appended" if append and mode == 'a' else "Exported"
            self.logger.info(f"{action} {record_count} records to {output_path}")
            
            return output_path
            
        except Exception as e:
            self.logger.error(f"Failed to export {filename}: {e}")
            raise
    
    def export_multiple(
        self,
        datasets: Dict[str, List[Dict[str, Any]]],
        fieldnames: Optional[Dict[str, List[str]]] = None,
    ) -> Dict[str, Path]:
        """
        Export multiple datasets to separate CSV files.
        
        Args:
            datasets: Dict mapping filename to data
            fieldnames: Dict mapping filename to fieldnames
            
        Returns:
            Dict mapping filename to output path
        """
        fieldnames = fieldnames or {}
        results = {}
        
        for filename, data in datasets.items():
            fields = fieldnames.get(filename)
            try:
                path = self.export(data, filename, fieldnames=fields)
                results[filename] = path
            except Exception as e:
                self.logger.error(f"Failed to export {filename}: {e}")
                results[filename] = None
        
        return results
    
    def get_output_path(self, filename: str) -> Path:
        """Get full path for output file."""
        return self.output_dir / filename
