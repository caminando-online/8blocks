import subprocess
import os

repo_dir = r"d:\dev\BP-8Blocks"
cmd = ['git', 'log', '-p', '--all']
try:
    result = subprocess.run(cmd, cwd=repo_dir, capture_output=True, text=True, encoding='utf-8')
    lines = result.stdout.split('\n')
    found_lines = []
    for i, line in enumerate(lines):
        ll = line.lower()
        if 'setup_fee_per_unit' in ll or 'amortization' in ll or 'taxes' in ll:
            if '<input' in ll or 'card-header' in ll or 'class="card' in ll:
                found_lines.append(f"Line {i}: {line.strip()}")
                # grab context
                start = max(0, i-5)
                end = min(len(lines), i+6)
                found_lines.append("CONTEXT:")
                found_lines.extend(lines[start:end])
                found_lines.append("-" * 40)
    
    with open(r'd:\dev\BP-8Blocks\search_git_results.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(found_lines))
    print(f"Found {len(found_lines)} references.")
except Exception as e:
    print(str(e))
