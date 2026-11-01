import re

template_path = "templates/incident_report.j2"
with open(template_path, "r", encoding="utf-8") as f:
    content = f.read()

# Pattern matching the audit block from comment to closing tag
pattern = r"\n\s*<!-- Hackathon PRD Evaluation Rubric & Mathematical Audit Panel -->[\s\S]*?</div>\s*</div>\s*</div>\n"

new_content = re.sub(pattern, "\n", content)

if new_content != content:
    with open(template_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Successfully removed PRD Audit Panel from templates/incident_report.j2!")
else:
    print("Pattern did not match. Trying exact substring removal...")
    start_marker = "    <!-- Hackathon PRD Evaluation Rubric & Mathematical Audit Panel -->"
    end_marker = "    <!-- Executive Threat Rankings & Jump Bar -->"
    if start_marker in content and end_marker in content:
        start_idx = content.find(start_marker)
        end_idx = content.find(end_marker)
        content = content[:start_idx] + end_marker + content[end_idx + len(end_marker):]
        with open(template_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("Successfully removed PRD Audit Panel using substring indices!")
    else:
        print("Markers not found!")
