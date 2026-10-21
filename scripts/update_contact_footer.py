"""Update only the contact footer in an existing RootLine checkout or ZIP folder."""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import shutil
from urllib.request import urlopen

FILES = (
    'templates/base.html',
    'templates/components/footer_links.html',
    'templates/components/footer_contact.html',
    'templates/components/contact_channels.html',
    'static/css/contact.css',
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ref', default='feature/rootline-contact-system', help='GitHub commit or branch to download')
    args = parser.parse_args()
    root = Path.cwd()
    if not (root / 'manage.py').is_file() or not (root / 'rootline/settings.py').is_file():
        parser.error('Open the Terminal in your RootLine project folder (the folder containing manage.py), then run again.')
    base = f'https://raw.githubusercontent.com/Muntasir-Mahin/RootLineFinal/{args.ref}/'
    # Finish all downloads before changing any existing files.
    downloaded = {}
    for filename in FILES:
        with urlopen(base + filename, timeout=30) as response:
            downloaded[filename] = response.read()
    stamp = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f')
    backup = root / 'work' / f'footer-backup-{stamp}'
    for filename in FILES:
        target = root / filename
        if target.exists():
            saved = backup / filename
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, saved)
    for filename, content in downloaded.items():
        target = root / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    print('Updated 5 footer files. Restart your server, then refresh with Command+Shift+R.')
    print(f'Original files saved in {backup}')


if __name__ == '__main__':
    main()
