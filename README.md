# The Portfolio Strategist

Financia is a financial software (fintech) company that services online users with intuitive, user-friendly financial tools to create, monitor, and advise on budgets, portfolios, and investments, all to promote a simplified, interactive, and reliable approach to easily manage your assets.

## Installation - Docker

The easiest way to get up and running is with [Docker](https://www.docker.com/).

Just [install Docker](https://www.docker.com/get-started) and
[Docker Compose](https://docs.docker.com/compose/install/)
and then run:

```
make init
pip install -r requirements.txt
docker compose up --build 
make start


```

This will spin up a database, web worker, celery worker, and Redis broker and run your migrations.

You can then go to [localhost:8000](http://localhost:8000/) to view the app.

*Note: if you get an error, make sure you have a `.env` file, or create one based on `.env.example`.*

## File Access Configuration

The Docker setup has been configured to provide access to your local drive and cloud drives from within containers. This enables Cursor AI and other tools to read, write, and execute files on your system.

### Setup

Run the setup script to configure file access permissions:

```bash
./setup_file_access.sh
```

This script will:
- Check for common cloud drive locations (Google Drive, Dropbox, OneDrive, iCloud)
- Verify access to Documents, Desktop, and Downloads folders
- Set appropriate permissions where possible
- Create a test script to verify access from within containers

### Mounted Directories

The following directories are mounted into Docker containers:

- **Home Directory**: `/host/home` - Your entire home directory
- **Cloud Storage**: `/host/cloudstorage` - iCloud/CloudStorage directory
- **Google Drive**: `/host/googledrive` - Google Drive folder
- **Dropbox**: `/host/dropbox` - Dropbox folder
- **OneDrive**: `/host/onedrive` - OneDrive folder
- **iCloud Drive**: `/host/iclouddrive` - iCloud Drive folder
- **Documents**: `/host/documents` - Documents folder
- **Desktop**: `/host/desktop` - Desktop folder
- **Downloads**: `/host/downloads` - Downloads folder

### Testing File Access

To test file access from within a container:

```bash
# Enter the container
docker compose exec web bash

# Run the test script
bash test_file_access.sh
```

### Using File Access in Python

A utility module is available for accessing files from within the application:

```python
from apps.utils.file_access import (
    get_host_path,
    get_cloud_path,
    read_file,
    write_file,
    check_access,
    list_directory,
)

# Access a file in your home directory
file_path = get_host_path("Documents/myfile.txt")
content = read_file(file_path)

# Access a file in Google Drive
gdrive_path = get_cloud_path("googledrive", "MyFolder/file.txt")
if gdrive_path and gdrive_path.exists():
    content = read_file(gdrive_path)

# Check access permissions
access_info = check_access(file_path)
print(f"Readable: {access_info['readable']}, Writable: {access_info['writable']}")
```

### Security Notes

⚠️ **Important Security Considerations:**

- Containers run as root by default to ensure full file access
- This provides broad access to your file system - use with caution
- Only mount directories you trust
- Be aware that files created by containers will be owned by root on the host
- Consider using more restrictive mounts for production environments

### Troubleshooting

If you encounter permission issues:

1. **macOS Privacy Settings**: Ensure Docker has Full Disk Access in System Preferences → Security & Privacy → Privacy
2. **Directory Permissions**: Some directories may require sudo to modify permissions
3. **Cloud Drive Sync**: Ensure cloud drives are fully synced and accessible on your local system
4. **Docker Desktop Settings**: Check Docker Desktop → Settings → Resources → File Sharing to ensure directories are shared

For more help, see the test script output or check Docker logs:
```bash
docker compose logs web
```

### Using the Makefile

You can run `make` to see other helper functions, and you can view the source
of the file in case you need to run any specific commands.

For example, you can run management commands in containers using the same method
used in the `Makefile`. E.g.

```
docker compose exec web uv run manage.py createsuperuser
```

## Installation - Native

You can also install/run the app directly on your OS using the instructions below.

You can setup a virtual environment and install dependencies in a single command with:

```bash
uv sync
```

This will create your virtual environment in the `.venv` directory of your project root.

## Stock Market Data API Configuration

The application uses reliable stock market data APIs (Polygon.io and Alpha Vantage) instead of yfinance for more accurate and reliable data.

### Setting up API Keys

1. **Polygon.io (Recommended - Primary Provider)**
   - Sign up for a free account at https://polygon.io/
   - Get your API key from the dashboard (free tier: 5 calls/minute)
   - Provide the key via one of the following options:
     - Set an environment variable: `export POLYGON_API_KEY=your_key_here`
     - Add it to your `.env` file: `POLYGON_API_KEY=your_key_here`
     - Or store it in the database from **Django Admin → Stock Analysis → Market Data Credentials**

2. **Alpha Vantage (Fallback Provider)**
   - Sign up for a free account at https://www.alphavantage.co/support/#api-key
   - Get your API key from the website (free tier: 5 calls/minute, 500 per day)
   - Provide it through the same options (environment variable, `.env`, or Market Data Credential in Django Admin)

**Note:** At least one API key is required. Polygon.io is preferred as it's more reliable. The system will automatically fall back to Alpha Vantage if Polygon.io is unavailable.

## Set up database

*If you are using Docker you can skip these steps.*

Create a database named `portfolio_strategist`.

```
createdb portfolio_strategist
```

Create database migrations:

```
uv run manage.py makemigrations
```

Create database tables:

```
uv run manage.py migrate
```

## Running server

**Docker:**

```bash
make start
```

**Native:**

```bash
uv run manage.py runserver
```

## Building front-end

To build JavaScript and CSS files, first install npm packages:

**Docker:**

```bash
make npm-install
```

**Native:**

```bash
npm install
```

Then build (and watch for changes locally):

**Docker:**

```bash
make npm-watch
```

**Native:**

```bash
npm run dev-watch
```

## Running Celery

Celery can be used to run background tasks.
If you use Docker it will start automatically.

You can run it using:

```bash
celery -A portfolio_strategist worker -l INFO --pool=solo
```

Or with celery beat (for scheduled tasks):

```bash
celery -A portfolio_strategist worker -l INFO -B --pool=solo
```

Note: Using the `solo` pool is recommended for development but not for production.

## Updating translations

**Docker:**

```bash
make translations
```

**Native:**

```bash
uv run manage.py makemessages --all --ignore node_modules --ignore .venv
uv run manage.py makemessages -d djangojs --all --ignore node_modules --ignore .venv
uv run manage.py compilemessages --ignore .venv
```

## Google Authentication Setup

To setup Google Authentication, follow the [instructions here](https://docs.allauth.org/en/latest/socialaccount/providers/google.html).

## Installing Git commit hooks

To install the Git commit hooks run the following:

```shell
$ uv run pre-commit install --install-hooks
```

Once these are installed they will be run on every commit.

For more information see the [docs](https://docs.saaspegasus.com/code-structure.html#code-formatting).

## Running Tests

To run tests:

**Docker:**

```bash
make test
```

**Native:**

```bash
uv run manage.py test
```

Or to test a specific app/module:

**Docker:**

```bash
make test ARGS='apps.utils.tests.test_slugs --keepdb'
```

**Native:**

```bash
uv run manage.py test apps.utils.tests.test_slugs
```

On Linux-based systems you can watch for changes using the following:

**Docker:**

```bash
find . -name '*.py' | entr docker compose exec web uv run manage.py test apps.utils.tests.test_slugs
```

**Native:**

```bash
find . -name '*.py' | entr uv run manage.py test apps.utils.tests.test_slugs
```