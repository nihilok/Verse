# Frontend Environment Variables

## Allowed Hosts Configuration

To configure allowed hosts for the Vite development server, create a `.env` file in the `frontend` directory with the following:

```env
# Allowed hosts for Vite dev server (comma-separated)
# Example for Raspberry Pi or remote access:
ALLOWED_HOSTS=localhost,192.168.1.100,myapp.local,raspberrypi.local
```

### Usage

1. Copy `.env.example` to `.env`:

   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your allowed hosts (comma-separated):

   ```env
   ALLOWED_HOSTS=localhost,192.168.1.100,verse.local
   ```

3. Restart the development server for changes to take effect:
   ```bash
   docker compose restart frontend
   # or
   bun run dev
   ```

### Notes

- Leave `ALLOWED_HOSTS` empty or omit it to allow all hosts (default behavior)
- Use comma-separated values for multiple hosts
- No spaces needed around commas (they will be trimmed automatically)
- This is particularly useful when accessing the dev server from other devices on your network
