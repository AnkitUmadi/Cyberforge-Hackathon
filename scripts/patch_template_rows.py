template_path = "templates/incident_report.j2"
with open(template_path, "r", encoding="utf-8") as f:
    content = f.read()

target = """                        <tr style="border-bottom: 1px solid #111827;">
                            <td style="padding: 8px; font-weight: 600; color: #f1f5f9;">False Alarms</td>
                            <td style="padding: 8px; color: #94a3b8;">Under 10%</td>
                            <td style="padding: 8px; font-weight: 700; color: #10b981;">{{ metrics.false_alarm_rate }}%</td>
                            <td style="padding: 8px; text-align: right;"><span style="background: #064e3b; color: #34d399; padding: 2px 6px; border-radius: 3px; font-weight: 700; font-size: 0.7rem;">GREAT</span></td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; font-weight: 600; color: #f1f5f9;">Investigation Speed</td>"""

replacement = """                        <tr style="border-bottom: 1px solid #111827;">
                            <td style="padding: 8px; font-weight: 600; color: #f1f5f9;">False Alarms</td>
                            <td style="padding: 8px; color: #94a3b8;">Under 10%</td>
                            <td style="padding: 8px; font-weight: 700; color: #10b981;">{{ metrics.false_alarm_rate }}%</td>
                            <td style="padding: 8px; text-align: right;"><span style="background: #064e3b; color: #34d399; padding: 2px 6px; border-radius: 3px; font-weight: 700; font-size: 0.7rem;">GREAT</span></td>
                        </tr>
                        <tr style="border-bottom: 1px solid #111827;">
                            <td style="padding: 8px; font-weight: 600; color: #f1f5f9;">Processing Time</td>
                            <td style="padding: 8px; color: #94a3b8;">Under 1 hour</td>
                            <td style="padding: 8px; font-weight: 700; color: #10b981;">{{ metrics.processing_time_s }}s ({{ "{:,}".format(metrics.throughput_eps) }} ev/s)</td>
                            <td style="padding: 8px; text-align: right;"><span style="background: #064e3b; color: #34d399; padding: 2px 6px; border-radius: 3px; font-weight: 700; font-size: 0.7rem;">GREAT</span></td>
                        </tr>
                        <tr style="border-bottom: 1px solid #111827;">
                            <td style="padding: 8px; font-weight: 600; color: #f1f5f9;">Peak Memory</td>
                            <td style="padding: 8px; color: #94a3b8;">Under 8 GB</td>
                            <td style="padding: 8px; font-weight: 700; color: #10b981;">{{ metrics.peak_mem_mb }} MB (Out-of-Core)</td>
                            <td style="padding: 8px; text-align: right;"><span style="background: #064e3b; color: #34d399; padding: 2px 6px; border-radius: 3px; font-weight: 700; font-size: 0.7rem;">GREAT</span></td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; font-weight: 600; color: #f1f5f9;">Investigation Speed</td>"""

if target in content:
    content = content.replace(target, replacement)
    with open(template_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Successfully patched incident_report.j2 with Processing Time and Peak Memory rows!")
else:
    print("Target string not found in template!")
