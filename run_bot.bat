@echo off
:: Navigate to the bot's directory
cd /d "C:\USERS\KHUSH\onedrive\desktop\DevOpsBot"

:: Run your bot and redirect both standard output and errors to the log file
:: Replace 'python bot.py' with your actual command
python devops_hub.py nudge > debug_log.txt 2>&1

:: Optional: Record the exit code
echo Exit Code: %errorlevel% >> error_log.txt