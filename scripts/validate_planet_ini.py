#!/usr/bin/env python3
"""Validate planet.ini and check that all active feeds are valid RSS/Atom feeds."""

import argparse
import concurrent.futures
import configparser
import io
import os
import sys
import urllib.parse

import feedparser
import requests

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REQUIRED_PLANET_OPTIONS = (
    'name', 'link', 'owner_name', 'owner_email',
    'output_theme', 'cache_directory', 'output_dir',
)
INTEGER_PLANET_OPTIONS = (
    'activity_threshold', 'feed_timeout', 'items_per_page', 'spider_threads',
)
DEFAULT_TIMEOUT = 20
# Match the User-Agent used by Planet Venus (python-httplib2) in the build container.
USER_AGENT = 'Python-httplib2/0.11.3 (gzip)'
MINOR_FEED_EXCEPTIONS = (
    feedparser.CharacterEncodingOverride,
    feedparser.NonXMLContentType,
)


def is_valid_url(url):
    try:
        parsed = urllib.parse.urlsplit(url)
        _ = parsed.port
    except ValueError:
        return False
    return (
        parsed.scheme in ('http', 'https')
        and bool(parsed.hostname)
        and '.' in parsed.hostname
        and not any(c.isspace() for c in url)
    )


def validate_config(config):
    """Validates planet.ini structure and returns (feeds, errors)."""
    errors = []
    if not config.has_section('Planet'):
        errors.append('Missing required [Planet] section')
        return [], errors

    planet = config['Planet']
    for option in REQUIRED_PLANET_OPTIONS:
        if not planet.get(option, '').strip():
            errors.append(f'[Planet] is missing required option "{option}"')
    for option in INTEGER_PLANET_OPTIONS:
        value = planet.get(option)
        if value is not None:
            try:
                int(value)
            except ValueError:
                errors.append(
                    f'[Planet] option "{option}" must be an integer, got "{value}"'
                )
    if link := planet.get('link', '').strip():
        if not is_valid_url(link):
            errors.append(f'[Planet] option "link" is not a valid URL: "{link}"')

    non_feed_sections = {'Planet'}
    for key in ('filters', 'template_files'):
        for item in planet.get(key, '').split():
            non_feed_sections.add(item.split('?', 1)[0])

    feeds = []
    for section in config.sections():
        if section in non_feed_sections:
            continue
        name = config.get(section, 'name', fallback='').strip()
        if not name:
            errors.append(f'Feed section [{section}] is missing "name"')
        if not is_valid_url(section):
            errors.append(f'Feed section [{section}] is not a valid http(s) URL')
            continue
        feeds.append((section, name or section))

    return feeds, errors


def check_feed(url, name, timeout):
    """Downloads a feed URL and checks that it parses as valid RSS or Atom."""
    try:
        response = requests.get(
            url, headers={'User-Agent': USER_AGENT}, timeout=timeout
        )
    except requests.RequestException as exc:
        return False, f'FAIL  {name} <{url}>: request failed: {exc}'

    if not response.ok:
        return (
            False,
            f'FAIL  {name} <{url}>: HTTP {response.status_code} {response.reason}',
        )

    parsed = feedparser.parse(
        io.BytesIO(response.content),
        response_headers={k.lower(): v for k, v in response.headers.items()},
    )
    if not parsed.version:
        return False, f'FAIL  {name} <{url}>: response is not an RSS or Atom feed'
    if parsed.bozo and not isinstance(parsed.bozo_exception, MINOR_FEED_EXCEPTIONS):
        return (
            False,
            f'FAIL  {name} <{url}>: malformed feed XML: {parsed.bozo_exception}',
        )

    return (
        True,
        f'OK    {name} <{url}> ({parsed.version}, {len(parsed.entries)} entries)',
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        'config',
        nargs='?',
        default=os.path.join(REPO_ROOT, 'planet.ini'),
        help='path to planet.ini (default: %(default)s)',
    )
    parser.add_argument(
        '--offline',
        action='store_true',
        help='only validate planet.ini syntax and options without fetching feeds',
    )
    args = parser.parse_args(argv)

    config = configparser.ConfigParser(interpolation=None)
    try:
        with open(args.config, encoding='utf-8') as f:
            config.read_file(f, source=args.config)
    except (OSError, UnicodeError, configparser.Error) as exc:
        print(f'ERROR: Failed to parse {args.config}: {exc}', file=sys.stderr)
        return 1

    feeds, errors = validate_config(config)
    for error in errors:
        print(f'ERROR: {error}', file=sys.stderr)

    if not args.offline and feeds:
        try:
            timeout = int(
                config.get('Planet', 'feed_timeout', fallback=DEFAULT_TIMEOUT)
            )
        except ValueError:
            timeout = DEFAULT_TIMEOUT

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            futures = [
                pool.submit(check_feed, url, name, timeout) for url, name in feeds
            ]
            for future in futures:
                ok, message = future.result()
                print(message, flush=True)
                if not ok:
                    errors.append(message)

    print(f'\nChecked {len(feeds)} active feeds: {len(errors)} error(s).')
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
