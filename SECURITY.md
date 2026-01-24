# Security Policy

## Reporting Security Issues

If you discover a security vulnerability in this project, please report it by opening an issue or contacting the repository owner directly.

## Security Best Practices

### 1. Protect Your Telegram Bot Token
- **Never commit** your bot token to version control
- Keep your `.env` file secure and private
- Regenerate your token immediately if it's exposed
- Use environment variables for all sensitive configuration

### 2. User Authentication
- The bot uses `USER_MAPPING` to map Telegram user IDs to Linux usernames
- Only authorized users (those in `USER_MAPPING`) can execute commands
- Regularly review and update the user mapping

### 3. Command Execution
- The bot can execute system commands with user or root privileges
- Ensure scripts in the `scripts/` directory are reviewed and trusted
- Be cautious with the `/run` command - it allows arbitrary command execution
- Commands run with `sudo` require proper sudoers configuration

### 4. Sensitive Information Handling
- Magic tokens and authentication credentials may be displayed in chat messages
- Ensure the bot is only used in private chats, not in groups
- Be aware that Telegram messages are stored on Telegram's servers
- Consider implementing additional masking for sensitive data

### 5. File System Access
- The bot can read disk usage and process information
- Private scripts in `private/` directory may contain sensitive operations
- The autologin feature uses `~/script/private/login_auto.sh` which is user-specific and not in the repository
- Review all scripts before making them executable
- Keep sensitive automation scripts outside the repository

### 6. Log Files
- Be careful with log files that might contain sensitive information
- Don't share logs publicly without redacting sensitive data
- Regularly clean up old logs

## Security Checklist for Deployment

- [ ] `.env` file is properly configured and not committed to git
- [ ] Bot token is kept secret and secure
- [ ] `USER_MAPPING` contains only authorized users
- [ ] Scripts in `scripts/` directory are reviewed and safe
- [ ] Sudoers is configured with minimal required permissions
- [ ] Bot is only used in private chats with authorized users
- [ ] Regular security updates are applied to dependencies
- [ ] Server has proper firewall and security configurations

## Dependencies

Keep all dependencies up to date to avoid known vulnerabilities:

```bash
uv sync
```

Regularly check for security advisories for:
- python-telegram-bot
- python-dotenv
- requests
