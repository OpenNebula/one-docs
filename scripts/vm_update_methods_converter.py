import csv
import os

def csv_to_html(csv_path):
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
        return ""

    with open(csv_path, mode='r', encoding='utf-8') as f:
        # csv.reader automatically handles quotes and commas inside cells
        reader = csv.reader(f)
        rows = list(reader)

    if not rows:
        return ""

    # Extract headers (Row 1)
    headers = rows[0]
    # Data rows start from index 1
    data_rows = rows[1:]

    html = ['<table id="data-spreadsheet" class="display" style="width:100%">']
    html.append('  <thead>')
    html.append('    <tr class="dt-layout-row">')
    html.append('      <th>SectionTracker</th>')
    
    # Process headers with the same width distributions
    for col_idx, header_val in enumerate(headers, start=1):
        final_header = header_val.strip() if header_val.strip() else f"Column {col_idx}"
        
        # --- Static widths on the master definition row ---
        width_style = ""
        if col_idx == 1:     # Method Column
            width_style = ' style="width: 22%;"'
        elif col_idx == 2:   # Attribute Column
            width_style = ' style="width: 13%;"'
        elif col_idx == 3:   # Description Column
            width_style = ' style="width: 12%;"'
        elif col_idx == 4:   # Updating in Running state Column
            width_style = ' style="width: 12%;"'
        elif col_idx == 5:   # Updating in POWEROFF state Column
            width_style = ' style="width: 12%;"'
        elif col_idx == 6:   # API Column
            width_style = ' style="width: 5%;"'
        elif col_idx == 7:   # CLI Column
            width_style = ' style="width: 5%;"'
        elif col_idx == 8:   # API Column
            width_style = ' style="width: 5%;"'
        elif col_idx == 9:   # API Column
            width_style = ' style="width: 20%;"'
            
        html.append(f'      <th{width_style}>{final_header}</th>')
        
    html.append('    </tr>')
    html.append('  </thead>\n  <tbody>')
    
    current_section = "General"
    max_cols = len(headers)

    for row in data_rows:
        # Strip whitespace from cells for accurate checking
        clean_row = [cell.strip() for cell in row]
        
        # Pad row with empty strings if it has fewer columns than the header
        if len(clean_row) < max_cols:
            clean_row.extend([""] * (max_cols - len(clean_row)))

        # Check if it's a section heading: Col 1 has text, all other columns are empty
        first_cell = clean_row[0]
        other_cells_empty = all(cell == "" for cell in clean_row[1:])
        
        if first_cell and other_cells_empty:
            current_section = first_cell
            continue  # Skip generating a <tr> for the section tracker row itself

        html.append('    <tr>')
        html.append(f'      <td>{current_section}</td>')
        
        # Populate the actual row data
        for col_idx, val in enumerate(clean_row[:max_cols], start=1):
            if col_idx == 2 and val:
                html.append(f'      <td class="truncated-attribute"><span class="cell-content">{val}</span></td>')
            else:
                html.append(f'      <td>{val}</td>')
            
        html.append('    </tr>')
        
    html.append('  </tbody>\n</table>')
    return '\n'.join(html)


def inject_table_into_markdown(md_file_path, csv_path, marker):
    # 1. Generate the HTML table block
    html_table = csv_to_html(csv_path)
    if not html_table:
        print("Aborting injection: Generated HTML is empty.")
        return
        
    shortcode_payload = f"{{{{< vm-methods-table >}}}}\n{html_table}\n{{{{< /vm-methods-table >}}}}"
    
    # 2. Read the current markdown contents
    try:
        with open(md_file_path, 'r', encoding='utf-8') as file:
            md_content = file.read()
    except FileNotFoundError:
        print(f"Error: Could not find {md_file_path}.")
        return

    # Clean out old table runs if they exist
    if f"{marker}\n{{{{< vm-methods-table >}}}}" in md_content:
        parts = md_content.split(f"{marker}\n{{{{< vm-methods-table >}}}}")
        header_part = parts[0]
        footer_part = parts[1].split(f"{{{{< /vm-methods-table >}}}}")[-1]
        md_content = f"{header_part}{marker}{footer_part}"

    # 3. Inject our fresh payload
    if marker in md_content:
        updated_content = md_content.replace(marker, f"{marker}\n{shortcode_payload}")
        
        # 4. Save it back to the file
        with open(md_file_path, 'w', encoding='utf-8') as file:
            file.write(updated_content)
        print("Success: Table successfully injected into the Markdown placeholder!")
    else:
        print(f"Warning: Marker '{marker}' was not found inside the markdown file.")


# --- execution paths updated for CSV ---
MD_FILE = "content/product/operation_references/configuration_references/vm_update_methods.md"
CSV_PATH = "assets/tables/vm_update_methods.csv" # Changed path extension
inject_table_into_markdown(MD_FILE, CSV_PATH, "<!-- VM METHODS TABLE -->")