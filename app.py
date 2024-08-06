from flask import Flask, request, render_template, redirect, url_for
import re
import os
import webbrowser

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


class Section:
    def __init__(self, name):
        self.name = name
        self.content = []

    def add_line(self, line):
        self.content.append(line)

    def is_empty(self):
        return not any(line.strip() for line in self.content)

    def to_html(self, index):
        colon_pattern = re.compile(r'^(.*?):(.*)$')
        html_body = f'<div class="section" id="section-{index}">'
        html_body += f'<h2 onclick="toggleVisibility(\'section-{index}-content\')" style="cursor:pointer;">{self.name}</h2>'
        html_body += f'<div id="section-{index}-content" style="display:none;">'

        started = False

        for line_number, line in enumerate(self.content, 1):

            line_style = 'display:none;' if line.startswith('$') or line.startswith('[1]') else ''

            if line == '':
                if not started:
                    continue
                line_style = 'display:none;'
            else:
                started = True

            colon_match = colon_pattern.match(line)
            if colon_match:
                bold_text = colon_match.group(1).strip()
                remaining_text = colon_match.group(2).strip()
                line_html = f'<span class="line-number" style="{line_style}">{line_number}</span><span class="code-line" style="{line_style}"><strong>{bold_text}:</strong> {remaining_text}</span><br>'
            else:
                line_html = f'<span class="line-number" style="{line_style}">{line_number}</span><span class="code-line" style="{line_style}">{line}</span><br>'
            html_body += line_html
        html_body += '</div></div>'
        return html_body


def fix_encoding_issues(text):
    replacements = {
        'â€˜': '‘', 'â€™': '’', 'â€¦': '…', 'â€”': '—',
        'â€“': '–', 'â€': '”', 'â€œ': '“', 'â€': '†',
        'â€™': '’', 'â€˜': '‘'
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def parse_sections(r_output):
    r_output = fix_encoding_issues(r_output)
    lines = r_output.split('\n')
    sections = []
    current_section = None
    header_block = False
    header_pattern = re.compile(r'^\s*#+\s*$')
    section_header_pattern = re.compile(r'^\s*##\s*(.*?)\s*##\s*$')

    for line in lines:
        if header_pattern.match(line):
            header_block = True
            continue
        if header_block and section_header_pattern.match(line):
            if current_section:
                sections.append(current_section)
            section_name = section_header_pattern.match(line).group(1).strip()
            current_section = Section(section_name)
            header_block = False
            continue
        if header_block and header_pattern.match(line):
            header_block = False
            continue
        if current_section:
            current_section.add_line(line)
    if current_section:
        sections.append(current_section)
    return sections


def remove_empty_sections(sections):
    return [section for section in sections if not section.is_empty()]


def format_section_links(sections):
    links = '<ul id="section-links">'
    for i, section in enumerate(sections):
        links += f'<li><a href="#section-{i}" onclick="highlightSection(\'section-{i}\')">{section.name}</a></li>'
    links += '</ul>'
    return links


def format_sections_to_html(sections):
    html_body = ""
    for i, section in enumerate(sections):
        html_body += section.to_html(i)
    return html_body


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if file:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)
            with open(file_path, 'r') as f:
                r_output = f.read()
            sections = parse_sections(r_output)
            sections = remove_empty_sections(sections)
            section_links = format_section_links(sections)
            html_output = format_sections_to_html(sections)
            return render_template('display.html', filename=file.filename, section_links=section_links,
                                   html_output=html_output)
    return render_template('index.html')


@app.route('/load')
def load_file():
    return redirect(url_for('upload_file'))


if __name__ == '__main__':
    webbrowser.open('http://127.0.0.1:5000/')
    app.run(debug=True)
