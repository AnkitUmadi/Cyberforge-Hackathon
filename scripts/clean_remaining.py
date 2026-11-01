template_path = "templates/incident_report.j2"
with open(template_path, "r", encoding="utf-8") as f:
    content = f.read()

kpi_end = "    </div>\n            <div style=\"display: flex; align-items: center; gap: 8px;\">"
rankings_start = "    <!-- Executive Threat Rankings & Jump Bar -->"

if kpi_end in content and rankings_start in content:
    idx1 = content.find("            <div style=\"display: flex; align-items: center; gap: 8px;\">")
    idx2 = content.find(rankings_start)
    clean_content = content[:idx1] + "\n" + content[idx2:]
    with open(template_path, "w", encoding="utf-8") as f:
        f.write(clean_content)
    print("Cleaned up remaining audit lines completely!")
else:
    print("Could not find markers!")
