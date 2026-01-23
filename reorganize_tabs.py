#!/usr/bin/env python3
"""
Reorganize tabs in app.py:
- Tab 1: Issuer 360 (standalone)
- Tab 2: Relative Value Matrix
- Tab 3: Alpha Lab
- Tab 4: Executive Brief
"""

# Read the file
with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find key line numbers
tab_def_start = None
tab1_start = None
issuer360_start_in_tab1 = None
tab2_start = None
tab3_start = None
tab4_start = None

for i, line in enumerate(lines):
    if 'tab_issuer360, tab_matrix, tab_optimization, tab_brief = st.tabs' in line:
        tab_def_start = i
    elif line.strip() == 'with tab_issuer360:':
        tab1_start = i
    elif '# ISSUER 360 DEEP DIVE (Moved from Tab 3)' in line:
        issuer360_start_in_tab1 = i
    elif line.strip() == 'with tab2:':
        tab2_start = i
    elif line.strip() == 'with tab3:':
        tab3_start = i
    elif line.strip() == 'with tab4:':
        tab4_start = i

print(f"Tab definition: line {tab_def_start}")
print(f"Tab 1 (tab_issuer360) starts: line {tab1_start}")
print(f"Issuer 360 content in tab1 starts: line {issuer360_start_in_tab1}")
print(f"Tab 2 starts: line {tab2_start}")
print(f"Tab 3 starts: line {tab3_start}")
print(f"Tab 4 starts: line {tab4_start}")

# Extract sections
matrix_content = lines[tab1_start+1:issuer360_start_in_tab1]  # Matrix content (without Issuer 360)
issuer360_content = lines[issuer360_start_in_tab1:tab2_start]  # Issuer 360 content
alpha_lab_content = lines[tab2_start:tab3_start]  # Alpha Lab
brief_content = lines[tab4_start:]  # Executive Brief

# Build new file
new_lines = []

# Keep everything before tabs
new_lines.extend(lines[:tab1_start+1])

# Tab 1: Issuer 360 (remove the "Moved from Tab 3" part and just keep the content)
issuer360_clean = []
skip_intro = True
for line in issuer360_content:
    if skip_intro:
        if '# ISSUER SELECTION (Changed to Equity Ticker - Name format)' in line:
            skip_intro = False
            # Add proper header
            issuer360_clean.append('        st.markdown(f\'<div class="section-header">🏢 Issuer 360 / 发行人全景深度分析</div>\', unsafe_allow_html=True)\n')
            issuer360_clean.append('        st.markdown("*Quantamental Fusion: Market Pricing + Financial Fundamentals*")\n')
            issuer360_clean.append('        st.markdown("*量化与基本面融合：市场定价 + 财务基本面*")\n')
            issuer360_clean.append('\n')
            issuer360_clean.append(line)
    else:
        issuer360_clean.append(line)

new_lines.extend(issuer360_clean)

# Tab 2: Relative Value Matrix
new_lines.append('\n')
new_lines.append('    # ============================================\n')
new_lines.append('    # TAB 2: RELATIVE VALUE MATRIX\n')
new_lines.append('    # ============================================\n')
new_lines.append('    with tab_matrix:\n')
new_lines.extend(matrix_content)

# Tab 3: Alpha Lab
new_lines.append('\n')
new_lines.append('    # ============================================\n')
new_lines.append('    # TAB 3: ALPHA OPTIMIZATION LAB\n')
new_lines.append('    # ============================================\n')
new_lines.append('    with tab_optimization:\n')
new_lines.extend(alpha_lab_content[1:])  # Skip the "with tab2:" line

# Tab 4: Executive Brief
new_lines.append('\n')
new_lines.append('    # ============================================\n')
new_lines.append('    # TAB 4: EXECUTIVE BRIEF\n')
new_lines.append('    # ============================================\n')
new_lines.append('    with tab_brief:\n')
new_lines.extend(brief_content[1:])  # Skip the "with tab4:" line

# Write the new file
with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("\nFile reorganized successfully!")
print(f"Total lines: {len(new_lines)}")
