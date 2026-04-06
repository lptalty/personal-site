#!/usr/bin/env python3
"""
Convert Substack HTML export to markdown files for the personal site.

Usage:
    python3 convert_substack.py <export_dir> <output_dir>

Example:
    python3 convert_substack.py ~/Downloads/OXEfgS4EQqu2_TABw6j0_w converted_posts
"""

import csv
import os
import re
import sys
from html.parser import HTMLParser
from datetime import datetime


class MarkdownConverter(HTMLParser):
    def __init__(self):
        super().__init__()
        self.md = []
        self._list_type = []
        self._link_stack = []  # stack of hrefs for open <a> tags
        self._skip_depth = 0   # >0 means we're inside a skipped subtree

        # Tags whose entire subtree should be dropped (must have closing tags)
        self._skip_tags = {"script", "style", "svg"}
        # Void elements to silently ignore (no closing tag, so can't use depth counter)
        self._skip_void = {"source"}
        # CSS class substrings that trigger a skip of the whole element
        self._skip_classes = {
            "button-wrapper", "captioned-button-wrap", "image-link-expand",
        }

    def _should_skip_start(self, tag, attrs):
        if tag in self._skip_void:
            return None  # void: ignore silently, no depth change
        if tag in self._skip_tags:
            return True
        cls = attrs.get("class", "")
        if any(sc in cls for sc in self._skip_classes):
            return True
        # Substack subscribe/share <a class="button ...">
        if tag == "a" and "button" in cls:
            return True
        return False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        skip = self._should_skip_start(tag, attrs)
        if self._skip_depth > 0 or skip is True:
            self._skip_depth += 1
            return
        if skip is None:
            return  # void skip element — ignore without depth change

        if tag in ("h1", "h2", "h3", "h4"):
            level = int(tag[1])
            self.md.append("\n" + "#" * level + " ")
        elif tag == "p":
            self.md.append("\n\n")
        elif tag == "br":
            self.md.append("  \n")
        elif tag in ("strong", "b"):
            self.md.append("**")
        elif tag in ("em", "i"):
            self.md.append("*")
        elif tag == "a":
            href = attrs.get("href", "")
            self._link_stack.append(href)
            self.md.append("[")
        elif tag == "img":
            src = attrs.get("src", "")
            alt = attrs.get("alt", "")
            self.md.append(f"\n\n![{alt}]({src})\n\n")
        elif tag == "ul":
            self._list_type.append("ul")
            self.md.append("\n")
        elif tag == "ol":
            self._list_type.append("ol")
            self.md.append("\n")
        elif tag == "li":
            marker = "\n1. " if self._list_type and self._list_type[-1] == "ol" else "\n- "
            self.md.append(marker)
        elif tag == "blockquote":
            self.md.append("\n\n> ")
        elif tag == "hr":
            self.md.append("\n\n---\n\n")
        elif tag == "figcaption":
            self.md.append("\n*")

    def handle_endtag(self, tag):
        if self._skip_depth > 0:
            self._skip_depth -= 1
            return

        if tag == "a" and self._link_stack:
            href = self._link_stack.pop()
            self.md.append(f"]({href})")
        elif tag in ("strong", "b"):
            self.md.append("**")
        elif tag in ("em", "i"):
            self.md.append("*")
        elif tag in ("h1", "h2", "h3", "h4"):
            self.md.append("\n")
        elif tag in ("ul", "ol"):
            if self._list_type:
                self._list_type.pop()
            self.md.append("\n")
        elif tag == "figcaption":
            self.md.append("*\n")

    def handle_data(self, data):
        if self._skip_depth > 0:
            return
        self.md.append(data)

    def get_markdown(self):
        text = "".join(self.md)
        # Strip link wrappers around images: [\n\n![alt](img)\n\n](href) -> ![alt](img)
        text = re.sub(r'\[\s*(\!\[.*?\]\(.*?\))\s*\]\([^)]*\)', r'\1', text)
        # collapse 3+ blank lines to 2
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


def html_to_markdown(html_content):
    converter = MarkdownConverter()
    converter.feed(html_content)
    return converter.get_markdown()


def slugify(title):
    slug = title.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = slug.strip("-")
    return slug


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    export_dir = os.path.expanduser(sys.argv[1])
    output_dir = sys.argv[2]
    posts_dir = os.path.join(export_dir, "posts")
    csv_path = os.path.join(export_dir, "posts.csv")

    os.makedirs(output_dir, exist_ok=True)

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        posts = list(reader)

    converted = 0
    skipped = 0

    for post in posts:
        post_id = post["post_id"]
        title = post["title"].strip()
        date_str = post["post_date"]
        is_published = post["is_published"] == "true"

        if not is_published or not title or not date_str:
            skipped += 1
            continue

        html_path = os.path.join(posts_dir, f"{post_id}.html")
        if not os.path.exists(html_path):
            print(f"  MISSING: {html_path}")
            skipped += 1
            continue

        date = datetime.fromisoformat(date_str.replace("Z", "+00:00")).date()

        with open(html_path, encoding="utf-8") as f:
            html_content = f.read()

        markdown_body = html_to_markdown(html_content)

        slug = slugify(title)
        output_path = os.path.join(output_dir, f"{slug}.md")

        frontmatter = f'---\ntitle: "{title}"\ndate: {date}\n---\n\n'

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(frontmatter + markdown_body + "\n")

        print(f"  OK: {slug}.md  ({date})")
        converted += 1

    print(f"\nDone: {converted} converted, {skipped} skipped.")
    print(f"Output in: {output_dir}/")


if __name__ == "__main__":
    main()
