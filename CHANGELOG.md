# Changelog

All notable changes to the Japanese Public Officials Scraper project.

## [1.1.2] - 2025-10-20

### Fixed - Character Encoding Issue
- **Shift_JIS Encoding Support**: Fixed garbled Japanese characters in election data
  - HTTP client now auto-detects and applies Shift_JIS encoding for Japanese government sites
  - Fixed "CRecÕWv" and similar garbled text appearing in election names
  - Added encoding detection for SOUMU election committee website
  - CSV export maintains UTF-8 BOM for Excel compatibility

### Added
- **CLI Command**: Added `clear-cache` command to purge old cached data with wrong encoding
- **Documentation**: Created ENCODING_FIX_v1.1.2.md with detailed fix explanation

### Technical Details
- Updated `src/core/http_client.py` to detect Shift_JIS from:
  - HTTP response apparent_encoding
  - HTML/XML encoding declaration
- No breaking changes, backward compatible
- Users need to run `python main.py clear-cache` once to see corrected data

---

## [1.1.1] - 2025-10-17

### Fixed - Critical Bug
- **ElectionsScraper Implementation**: Added missing `scrape()` method required by `BaseScraper` abstract class
  - Fixed TypeError when instantiating ElectionsScraper
  - Program now successfully runs `python main.py run-all` without crashes
  - All integration tests passing (46/46)
  - No breaking changes or migration required

### Verified
- ✅ All 7 CLI commands working correctly
- ✅ 13/13 unit tests passing
- ✅ Full integration test successful
- ✅ Data collection from all 3 sources (Officials, Elections, Funding)
- ✅ 281 election schedules successfully collected in tests

---

## [1.1.0] - 2025-10-17

### Added - Advanced Features
All v1.0 limitations are now addressable with optional advanced features:

- **JavaScript Rendering**:
  - `AdvancedHTTPClient` with Playwright integration
  - Auto-detection of JS-heavy pages
  - Smart fallback (try static first, use Playwright if needed)
  - Configurable wait conditions (networkidle, load, domcontentloaded)
  
- **SNS Verification Detection**:
  - HTML pattern matching for verification badges
  - Support for X/Twitter, Instagram, Facebook, YouTube
  - Follower count extraction from HTML
  - No API keys required
  
- **PDF Parsing**:
  - `pdfplumber` integration for table extraction
  - OCR fallback with `pytesseract` for scanned PDFs
  - Funding totals parsing (income, expense, balance)
  - Japanese pattern recognition (令和 year conversion)
  
- **Name Matching**:
  - Name normalization (remove suffixes, convert cases)
  - Fuzzy matching with `rapidfuzz`
  - Optional semantic matching with sentence transformers
  - Multi-strategy fallback (exact → fuzzy → semantic)
  - Batch matching utilities

### Changed
- Updated `config/config.yaml` with `advanced:` section
- Updated `requirements.txt` with optional dependencies
- Updated README.md with advanced features overview

### Added - Documentation
- `ADVANCED_FEATURES.md` - Comprehensive guide for all advanced features
- `demo_advanced.py` - Demo script showcasing all capabilities
- Installation guides for each advanced feature
- Performance and accuracy benchmarks
- Troubleshooting section

## [1.0.0] - 2025-10-17

### Added
- Initial release of the scraper platform
- **Officials Scraper**:
  - Extract public official information (name, age, faction, promises)
  - Auto-detect and extract SNS links (X/Twitter, Instagram, Facebook, YouTube)
  - Support for national, prefectural, and municipal officials
  - Configurable seed URLs via `sources.yaml`
  
- **Elections Scraper**:
  - Scrape scheduled election dates from election management committees
  - Extract election results with candidate names and vote counts
  - Support for SOUMU and prefectural election commission sites
  
- **Funding Scraper**:
  - Discover political funding report links
  - Optional parsing of income/expense totals
  - Support for both national and prefectural disclosure portals
  
- **Core Infrastructure**:
  - Rate-limited HTTP client with caching (requests-cache)
  - robots.txt compliance
  - Automatic retry with exponential backoff
  - Comprehensive logging with rotation
  - CSV export with UTF-8 BOM for Excel compatibility
  
- **CLI Interface**:
  - `scrape-officials` - Collect official data
  - `scrape-elections` - Collect election data
  - `scrape-funding` - Collect funding data
  - `run-all` - Run all scrapers sequentially
  - Rich progress bars and formatted output
  - Configurable limits and verbosity
  
- **Configuration**:
  - YAML-based configuration (`config.yaml`)
  - Separate sources file (`sources.yaml`)
  - SNS pattern matching rules
  - Per-domain rate limiting
  
- **Documentation**:
  - Comprehensive README with setup instructions
  - macOS and Windows setup scripts
  - Example configurations
  - Legal and compliance notes
  
- **Testing**:
  - Unit tests for parsers and models
  - Pytest fixtures for sample data
  - Schema validation tests

### Technical Details
- Python 3.10+ required
- Dependencies: requests, beautifulsoup4, pandas, pydantic, typer, rich
- Modular architecture with clear separation of concerns
- Pydantic models for data validation
- Configurable output formats and encodings

### Known Limitations
- SNS verification status not available without API access
- Political funding totals parsing is heuristic-based
- Some prefectural sites may have varying structures
- JavaScript-heavy sites not fully supported (planned for v2)

### Compliance
- Respects robots.txt
- Implements polite crawling (1.5s default delay)
- Collects only publicly available information
- No authentication bypass or paywall circumvention
