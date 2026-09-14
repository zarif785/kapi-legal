#!/usr/bin/env python3
"""Render the project's small legal Markdown subset; no packages or network needed.

python3 docs/legal-site/build.py          # regenerate + validate
python3 docs/legal-site/build.py --check  # fail if committed/prepared pages are stale
"""
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlparse, unquote

HERE = Path(__file__).resolve().parent
DOCS = HERE.parent
BASE = 'https://zarif785.github.io/kapi-legal'
TOKEN = re.compile(r'\[([^\]\n]+)\]\(([^\s)]+)\)|\*\*(.+?)\*\*|https://[^\s<>()]+|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}')


def link(url):
    parsed = urlparse(url)
    if parsed.scheme not in ('https', 'mailto'):
        raise ValueError(f'Unsupported link scheme: {parsed.scheme}')
    if parsed.scheme == 'https' and not parsed.netloc:
        raise ValueError('HTTPS link has no host')
    if url.rstrip('/') in (BASE + '/privacy', BASE + '/terms', BASE + '/support'):
        return '../' + url.rstrip('/').rsplit('/', 1)[1] + '/'
    return url


def inline(text):
    result, end = [], 0
    for match in TOKEN.finditer(text):
        result.append(html.escape(text[end:match.start()]))
        if match.group(1) is not None:
            result.append(f'<a href="{html.escape(link(match.group(2)), quote=True)}">{inline(match.group(1))}</a>')
        elif match.group(3) is not None:
            result.append('<strong>' + inline(match.group(3)) + '</strong>')
        else:
            raw = match.group().rstrip('.,;:!?')
            url = raw if raw.startswith('https:') else 'mailto:' + raw
            result.append(f'<a href="{html.escape(link(url), quote=True)}">{html.escape(raw)}</a>')
            result.append(html.escape(match.group()[len(raw):]))
        end = match.end()
    return ''.join(result) + html.escape(text[end:])


def blocks(markdown):
    # ponytail: supports only the headings, paragraphs and flat bullets these docs use;
    # reject other block syntax so future Markdown additions cannot silently lose meaning.
    result, paragraph = [], []
    def flush():
        if paragraph:
            result.append(('p', ' '.join(paragraph)))
            paragraph.clear()
    for raw in markdown.splitlines():
        line = raw.strip()
        if not line:
            flush()
        elif line.startswith('#'):
            flush()
            match = re.fullmatch(r'(#{1,6}) (.+)', line)
            if not match:
                raise ValueError('Unsupported heading: ' + line)
            result.append(('h' + str(len(match[1])), match[2]))
        elif line.startswith('- '):
            flush()
            result.append(('li', line[2:]))
        else:
            if line.startswith(('```', '|', '> ', '![')) or re.match(r'\d+\. ', line):
                raise ValueError('Unsupported block: ' + line)
            paragraph.append(line)
    flush()
    return result


class TextAndLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text, self.links = [], []
    def handle_data(self, data):
        self.text.append(data)
    def handle_starttag(self, tag, attrs):
        if tag in ('a', 'link'):
            values = dict(attrs)
            if 'href' in values:
                self.links.append(values['href'])


def plain(markup):
    parser = TextAndLinks()
    parser.feed(markup)
    return ' '.join(''.join(parser.text).split())


def render(markdown):
    output, listing, expected = [], False, []
    rows = blocks(markdown)
    for tag, text in rows:
        if listing and tag != 'li':
            output.append('</ul>')
            listing = False
        if tag == 'li' and not listing:
            output.append('<ul>')
            listing = True
        content = inline(text)
        # Independent visible-text expectation: strip Markdown marks, never paragraphs.
        wanted = re.sub(r'\[([^\]]+)\]\([^\s)]+\)', r'\1', text).replace('**', '')
        assert plain(content) == ' '.join(wanted.split()), text
        expected.append(plain(content))
        css = ' class="updated"' if text.startswith('Version ') else ''
        output.append(f'<{tag}{css}>{content}</{tag}>')
    if listing:
        output.append('</ul>')
    body = '\n'.join(output)
    assert plain(body) == ' '.join(expected)
    return body, len(rows)


def page(title, description, body, nested=True):
    prefix = '../' if nested else ''
    home = '<a class="home" href="../">← Kapi</a>' if nested else ''
    nav = ''.join(f'<a href="{prefix}{name}/">{label}</a>' for name, label in
                  [('privacy', 'Privacy'), ('terms', 'Terms'), ('support', 'Support')])
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} — Kapi</title>
<meta name="description" content="{html.escape(description, quote=True)}">
<link rel="stylesheet" href="{prefix}style.css">
</head>
<body>
<main>
{home}
{body}
<footer><nav class="nav" aria-label="Legal and support">{nav}</nav></footer>
</main>
</body>
</html>
'''


def check_links(path, content):
    parser = TextAndLinks()
    parser.feed(content)
    for href in parser.links:
        parsed = urlparse(href)
        if parsed.scheme:
            assert parsed.scheme in ('https', 'mailto'), href
            assert not href.endswith(('.', ',')), href
        else:
            target = (path.parent / unquote(parsed.path)).resolve()
            if href.endswith('/'):
                target /= 'index.html'
            assert target.is_relative_to(HERE) and target.exists(), str(target)
    return len(parser.links)


def demo():
    markup, count = render('# Name\n\nFirst line\nsecond line.\n\n- **One**\n- [Two](https://example.com/two)\n\nhttps://example.com/end.\n\n<script>x</script>')
    assert count == 6 and '<script>' not in markup
    assert 'href="https://example.com/end"' in markup
    assert 'First line second line.' in markup
    try:
        inline('[bad](javascript:alert)')
    except ValueError:
        pass
    else:
        raise AssertionError('Unsafe link accepted')


def main():
    demo()
    check = '--check' in sys.argv
    pages, proof = {}, {}
    for slug, title in [('privacy', 'Privacy Policy'), ('terms', 'Terms of Use'), ('support', 'Support')]:
        source = DOCS / f'{slug}.md' if slug != 'support' else HERE / 'support.md'
        raw = source.read_text()
        body, count = render(raw)
        pages[HERE / slug / 'index.html'] = page(title, f'Kapi {title.lower()}: information, rights and help.', body)
        proof[slug] = {'source': str(source.relative_to(DOCS)), 'sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'contentBlocks': count, 'textCoverage': 'every source block checked in order'}
    email = re.search(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}', (DOCS / 'privacy.md').read_text())[0]
    root_body = '<h1>Kapi</h1><p class="updated">Learn Japanese kanji from your Lock Screen. For iPhone.</p><div class="lead"><p>Legal information and support for Kapi. Learning happens on your device; subscriptions are handled by Apple and RevenueCat.</p></div><h2>Contact</h2>' + inline(f'[Email Kapi support](mailto:{email})')
    pages[HERE / 'index.html'] = page('Kapi', 'Kapi privacy, subscription terms and support.', root_body, nested=False)
    for path, content in pages.items():
        if check:
            assert path.read_text() == content, f'Stale page: {path}'
        else:
            path.parent.mkdir(exist_ok=True)
            path.write_text(content)
    for path, content in pages.items():
        links = check_links(path, content)
        if path.parent.name in proof:
            proof[path.parent.name]['linksChecked'] = links
    assert pages[HERE / 'terms/index.html'].count('Permission is hereby granted, free of charge') == 2
    assert all('PLACEHOLDER' not in value for value in pages.values())
    assert 'Version 1.1' in pages[HERE / 'privacy/index.html'] and 'Version 1.1' in pages[HERE / 'terms/index.html']
    (HERE / '.nojekyll').touch(exist_ok=True) if not check else None
    summary = json.dumps(proof, indent=2) + '\n'
    if check:
        assert (HERE / 'verification.json').read_text() == summary
    else:
        (HERE / 'verification.json').write_text(summary)
    print(f'{len(pages)} pages verified; complete paragraph coverage, safe links, local targets, two MIT notices.')


if __name__ == '__main__':
    main()
