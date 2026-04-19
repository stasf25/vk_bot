#!/usr/bin/env python3
"""
Simple HTML to Markdown converter for scraping web pages.
"""

import re
from html.parser import HTMLParser


class HTMLToMarkdown(HTMLParser):
    """Convert HTML content to markdown format."""

    def __init__(self):
        super().__init__()
        self.markdown = []
        self.skip_tags = {'script', 'style', 'noscript'}
        self.current_skip = None
        self.heading_level = 0
        self.in_link = False
        self.link_text = []
        self.link_href = ''
        self.in_list = False
        self.list_indent = 0

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag in self.skip_tags:
            self.current_skip = tag
            return
        if tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            self.heading_level = int(tag[1])
            self.markdown.append('\n')
        elif tag == 'a':
            self.in_link = True
            self.link_text = []
            self.link_href = attrs_dict.get('href', '')
        elif tag in ('strong', 'b'):
            self.markdown.append('**')
        elif tag in ('em', 'i'):
            self.markdown.append('*')
        elif tag == 'br':
            self.markdown.append('\n')
        elif tag == 'hr':
            self.markdown.append('\n---\n')
        elif tag in ('ul', 'ol'):
            self.in_list = True
            self.list_indent = len(self.markdown)
        elif tag == 'li':
            self.markdown.append('\n')

    def handle_endtag(self, tag):
        if tag == self.current_skip:
            self.current_skip = None
            return
        if tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            self.heading_level = 0
        elif tag == 'a':
            if self.link_href and self.link_text:
                link_content = ''.join(self.link_text).strip()
                self.markdown.append(f'[{link_content}]({self.link_href})')
            self.in_link = False
            self.link_text = []
            self.link_href = ''
        elif tag in ('strong', 'b'):
            self.markdown.append('**')
        elif tag in ('em', 'i'):
            self.markdown.append('*')
        elif tag in ('ul', 'ol'):
            self.in_list = False
        elif tag == 'li':
            pass

    def handle_data(self, data):
        if self.current_skip:
            return
        text = data.strip()
        if not text:
            return
        if self.in_link:
            self.link_text.append(text)
        else:
            prefix = ''
            if self.heading_level > 0:
                prefix = '#' * self.heading_level + ' '
            elif self.in_list:
                prefix = '- '
            self.markdown.append(prefix + text)

    def get_markdown(self):
        """Return the generated markdown content."""
        result = ' '.join(self.markdown)
        result = re.sub(r'\s+', ' ', result)
        result = re.sub(r'\n\s*\n', '\n\n', result)
        return result.strip()


def html_to_markdown(html_content: str) -> str:
    """Convert HTML content to markdown."""
    parser = HTMLToMarkdown()
    parser.feed(html_content)
    return parser.get_markdown()


if __name__ == '__main__':
    # Read the HTML file with error handling for encoding
    with open('/tmp/google.html', 'r', encoding='utf-8', errors='ignore') as f:
        html_content = f.read()

    # Convert to markdown
    markdown_content = html_to_markdown(html_content)

    # Write to output file
    output_path = '/home/ubuntu/vk_bot/google.md'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('# Google.com Scraping Result\n\n')
        f.write('**Source URL:** https://google.com\n\n')
        f.write('**Scraped with:** curl + HTML parser\n\n')
        f.write('---\n\n')
        f.write(markdown_content)

    print(f'Markdown saved to: {output_path}')