# Automated Schema Matcher Setup Guide

This guide explains how to set up and use the automated schema matching system for the Marine Data Integration Platform.

## Overview

The automation system consists of:
- **Schema Matcher** (`scripts/schema_matcher.py`) - Core matching logic
- **Automation Runner** (`automation/run_schema_matcher.py`) - Platform-independent execution wrapper
- **Scheduler** (`automation/scheduler.py`) - Cross-platform scheduling system
- **Configuration** (`config/schema_matcher_config.yaml`) - Centralized configuration

## Quick Start

### 1. Install Dependencies

```bash
# Install automation dependencies
pip install -r requirements_automation.txt

# Or install individually:
pip install pandas psycopg2-binary pymongo python-dotenv PyYAML croniter
```

### 2. Configure the System

Edit `config/schema_matcher_config.yaml` to customize:
- Directories to scan
- Database connections
- Scheduling frequency
- Notification settings

### 3. Test the Schema Matcher

```bash
# Test manual execution
python3 scripts/schema_matcher.py data/ --output-format console

# Test automation wrapper
python3 automation/run_schema_matcher.py --verbose

# Test single run via scheduler
python3 automation/scheduler.py --run-once
```

## Usage Options

### Manual Execution

Run schema matching immediately for specific directories:

```bash
# Basic usage
python3 scripts/schema_matcher.py /path/to/data --output-format all

# With custom settings
python3 scripts/schema_matcher.py /path/to/data \
  --similarity-threshold 0.8 \
  --output-file my_matches.json \
  --log-level DEBUG
```

### Automated Execution

Use the automation wrapper for enhanced error handling and notifications:

```bash
# Run once with full automation features
python3 automation/run_schema_matcher.py --verbose

# Run for specific directories
python3 automation/run_schema_matcher.py /path/to/data1 /path/to/data2

# Use custom config file
python3 automation/run_schema_matcher.py --config my_config.yaml
```

### Scheduled Execution

#### Option 1: Built-in Scheduler (Recommended)

```bash
# Run as daemon (keeps running)
python3 automation/scheduler.py --daemon

# Check scheduler status
python3 automation/scheduler.py --status

# Run once and exit
python3 automation/scheduler.py --run-once
```

#### Option 2: System Service Installation

```bash
# Install as system service (Linux/macOS)
sudo python3 automation/scheduler.py --install-service

# On Linux with systemd:
sudo systemctl start schema-matcher-scheduler
sudo systemctl enable schema-matcher-scheduler

# Check service status
sudo systemctl status schema-matcher-scheduler
```

#### Option 3: Traditional Cron (Linux/macOS)

```bash
# Add to crontab
crontab -e

# Add this line for daily execution at 2 AM:
0 2 * * * cd /home/rewansh57/SIH/marine-data-platform && python3 automation/run_schema_matcher.py
```

#### Option 4: Windows Task Scheduler

1. Open Windows Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., Daily at 2:00 AM)
4. Set action: Start Program
5. Program: `python3` or full Python path
6. Arguments: `/path/to/automation/run_schema_matcher.py`
7. Start in: `/path/to/marine-data-platform`

## Configuration

### Main Configuration File: `config/schema_matcher_config.yaml`

```yaml
# Directories to scan
scan_directories:
  - "/home/rewansh57/SIH/marine-data-platform/data"
  - "/tmp/marine_data_uploads"

# Database connections
databases:
  postgres:
    host: "localhost"
    port: 5432
    database: "marine_db"
    user: "marineuser"
  mongodb:
    connection_string: "mongodb://localhost:27017/"
    database: "marine_db"

# Scheduling (cron format)
scheduling:
  enabled: true
  cron_schedule: "0 2 * * *"  # Daily at 2 AM

# Email notifications
notifications:
  email:
    enabled: false
    smtp_server: "localhost"
    to_addresses: ["admin@example.com"]
```

### Environment Variables

Set sensitive information via environment variables:

```bash
export POSTGRES_PASSWORD="your_postgres_password"
export MONGO_CONNECTION="mongodb://user:pass@localhost:27017/"
export EMAIL_PASSWORD="your_email_password"
```

Or create a `.env` file:

```env
POSTGRES_PASSWORD=your_postgres_password
MONGO_CONNECTION=mongodb://user:pass@localhost:27017/
EMAIL_PASSWORD=your_email_password
```

## Platform Compatibility

### Linux (Fedora/Ubuntu/CentOS)
- ✅ Manual execution
- ✅ Built-in scheduler
- ✅ Systemd service
- ✅ Cron jobs
- ✅ Email notifications

### macOS
- ✅ Manual execution
- ✅ Built-in scheduler
- ✅ LaunchAgent service
- ✅ Cron jobs
- ✅ Email notifications

### Windows
- ✅ Manual execution
- ✅ Built-in scheduler
- ✅ Task Scheduler
- ✅ Email notifications
- ⚠️ Service installation requires additional setup

## Output and Logging

### Reports
- Location: `reports/schema_matches_YYYYMMDD_HHMMSS.*`
- Formats: JSON (detailed), CSV (summary), Console (human-readable)

### Logs
- Automation: `logs/automation.log`
- Schema Matcher: `logs/schema_matcher.log`
- Scheduler: `logs/scheduler.log`

### Log Rotation
Logs automatically rotate when they exceed the configured size limit.

## Monitoring and Alerts

### Check Status

```bash
# Scheduler status
python3 automation/scheduler.py --status

# View recent logs
tail -f logs/automation.log

# Check system service (Linux)
sudo systemctl status schema-matcher-scheduler
```

### Email Notifications

Configure email notifications for:
- Successful runs with matches found
- Errors and failures
- No matches found (optional)
- Dependency issues

## Troubleshooting

### Common Issues

1. **Missing Dependencies**
   ```bash
   pip install -r requirements_automation.txt
   ```

2. **Database Connection Issues**
   - Check database credentials in config or environment variables
   - Ensure databases are running
   - Verify network connectivity

3. **Permission Issues**
   - Ensure write permissions for logs and reports directories
   - For system service: use appropriate user permissions

4. **Schedule Not Working**
   - Check cron expression syntax
   - Verify scheduler daemon is running
   - Check log files for errors

### Debug Mode

Run with verbose logging for troubleshooting:

```bash
python3 automation/run_schema_matcher.py --verbose
python3 scripts/schema_matcher.py data/ --log-level DEBUG
```

## Security Considerations

1. **Database Credentials**: Use environment variables, not config files
2. **File Permissions**: Restrict access to config files and logs
3. **Email Passwords**: Store in environment variables
4. **System Service**: Run with appropriate user privileges

## Performance Tuning

### Large Datasets
- Adjust `csv_sample_rows` in configuration
- Set `max_file_size_mb` limit
- Increase `timeout_seconds` for large operations

### High Frequency Scanning
- Use more specific directory patterns
- Implement file age thresholds
- Enable `skip_already_processed` option

## Examples

### Development Setup
```bash
# Quick test
python3 automation/scheduler.py --run-once --verbose

# Manual run with custom settings
python3 scripts/schema_matcher.py data/ \
  --similarity-threshold 0.7 \
  --output-format console \
  --log-level INFO
```

### Production Setup
```bash
# Install as system service
sudo python3 automation/scheduler.py --install-service

# Start and enable
sudo systemctl start schema-matcher-scheduler
sudo systemctl enable schema-matcher-scheduler

# Monitor
sudo journalctl -u schema-matcher-scheduler -f
```

## Support

For issues and questions:
1. Check the log files in `logs/`
2. Review configuration in `config/`
3. Test with `--verbose` flag for detailed output
4. Ensure all dependencies are installed