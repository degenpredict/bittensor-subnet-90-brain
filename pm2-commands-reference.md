# PM2 Commands Reference

## Basic Process Management

```bash
pm2 start ecosystem.config.js       # Start all configured processes
pm2 restart ecosystem.config.js     # Restart all processes  
pm2 stop all                        # Stop all processes
pm2 delete all                      # Delete all processes
pm2 reload all                      # Graceful reload (zero downtime)
```

---

## Process Status & Monitoring

```bash
pm2 status                          # Show all process status
pm2 list                            # Same as status
pm2 show <name>                     # Show detailed process info
pm2 monit                           # Real-time monitoring dashboard
pm2 logs                            # Show all process logs
pm2 logs <name>                     # Show logs for specific process
pm2 logs --lines 100                # Show last 100 lines
pm2 flush                           # Clear all logs
```

---

## Specific Process Control

```bash
# Start specific processes
pm2 start ecosystem.config.js --only miner_1
pm2 start ecosystem.config.js --only "miner*"

# Control individual processes
pm2 restart miner_1                 # Restart specific process
pm2 stop miner_1                    # Stop specific process
pm2 delete miner_1                  # Delete specific process
pm2 reload miner_1                  # Graceful reload
```

---

## Configuration & Persistence

```bash
pm2 save                            # Save current process list
pm2 startup                         # Generate startup script
pm2 unstartup                       # Disable startup script
pm2 resurrect                       # Restore saved processes
pm2 dump                            # Show saved configuration
```

---

## Process Scaling

```bash
pm2 scale miner_1 3                 # Scale miner_1 to 3 instances
pm2 scale all +2                    # Add 2 instances to each process
pm2 scale all -1                    # Remove 1 instance from each
```

---

## Log Management

```bash
pm2 logs                            # Stream all logs
pm2 logs miner_1                    # Stream specific process logs
pm2 logs --timestamp                # Add timestamps to logs
pm2 logs --raw                      # Raw logs without PM2 formatting
pm2 logs --err                      # Show only error logs
pm2 logs --out                      # Show only output logs
pm2 flush                           # Clear all log files
pm2 reloadLogs                      # Reload log files
```

---

## Environment & Configuration

```bash
pm2 env <id>                        # Show process environment variables
pm2 start app.js --env production   # Start with specific environment
pm2 restart all --update-env        # Restart with updated environment
```

---

## Process Information

```bash
pm2 describe <name>                 # Detailed process information
pm2 list --watch                    # Show which processes are watched
pm2 prettylist                     # Pretty formatted process list
pm2 jlist                          # JSON formatted process list
```

---

## Common Workflows

### Initial Setup
```bash
pm2 start ecosystem.config.js       # Start all processes
pm2 save                            # Save configuration
pm2 startup                         # Enable auto-start
# Run the generated command with sudo
```

### Daily Operations
```bash
pm2 status                          # Check process health
pm2 logs                            # Check recent logs
pm2 monit                          # Real-time monitoring
```

### Updates & Restarts
```bash
pm2 restart ecosystem.config.js     # Restart all after code changes
pm2 reload all                      # Zero-downtime restart
pm2 flush                           # Clear old logs
```

### Troubleshooting
```bash
pm2 logs miner_1 --lines 100        # Check recent logs
pm2 describe miner_1                # Check process details
pm2 restart miner_1                 # Restart problematic process
pm2 delete miner_1                  # Remove and recreate process
pm2 start ecosystem.config.js --only miner_1
```

---

## Useful Aliases

Add these to your `~/.bashrc` for convenience:

```bash
alias pms='pm2 status'
alias pml='pm2 logs'
alias pmr='pm2 restart ecosystem.config.js'
alias pmstart='pm2 start ecosystem.config.js'
alias pmstop='pm2 stop all'
```