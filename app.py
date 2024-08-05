from flask import Flask, request, render_template, redirect, url_for
import re
import os
import webbrowser

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def fix_encoding_issues(text):
    replacements = {
        'â€˜': '‘',
        'â€™': '’',
        'â€¦': '…',
        'â€”': '—',
        'â€“': '–',
        'â€': '”',
        'â€œ': '“',
        'â€': '†',
        'â€™': '’',
        'â€˜': '‘'
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
            current_section = {
                'name': section_name,
                'content': []
            }
            header_block = False
            continue

        if header_block and header_pattern.match(line):
            header_block = False
            continue

        if current_section:
            current_section['content'].append(line)

    if current_section:
        sections.append(current_section)

    return sections


def remove_empty_sections(sections):
    return [section for section in sections if any(line.strip() for line in section['content'])]


def format_section_links(sections):
    links = '<ul>'
    for i, section in enumerate(sections):
        links += f'<li><a href="#section-{i}">{section["name"]}</a></li>'
    links += '</ul>'
    return links


def format_sections_to_html(sections):
    html_body = ""
    colon_pattern = re.compile(r'^(.*?):(.*)$')

    for i, section in enumerate(sections):
        html_body += f'<div class="section" id="section-{i}">'
        html_body += f'<h2>{section["name"]} <button onclick="toggleVisibility(\'section-{i}-content\')">Toggle</button></h2>'
        html_body += f'<div id="section-{i}-content">'
        line_number = 1
        for line in section['content']:
            colon_match = colon_pattern.match(line)
            if colon_match:
                bold_text = colon_match.group(1).strip()
                remaining_text = colon_match.group(2).strip()
                line_html = f'<span class="line-number">{line_number}</span><span class="code-line"><strong>{bold_text}:</strong> {remaining_text}</span><br>'
            else:
                line_html = f'<span class="line-number">{line_number}</span><span class="code-line">{line}</span><br>'
            html_body += line_html
            line_number += 1
        html_body += '</div></div>'
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
            return render_template('display.html', section_links=section_links, html_output=html_output)
    return render_template('index.html')


if __name__ == '__main__':
    webbrowser.open('http://127.0.0.1:5000/')
    app.run(debug=True)
