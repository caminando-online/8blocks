import os

def search_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        with open(filepath, 'r', encoding='utf-16') as f:
            lines = f.readlines()
            
    for i, line in enumerate(lines):
        ll = line.lower()
        if 'setup_fee_per_unit' in ll or 'amortizaci' in ll or 'taxes' in ll or 'other income' in ll:
            print(f"Line {i}: {line.strip()}")
            # print surrounding 5 lines
            for j in range(max(0, i-5), min(len(lines), i+6)):
                print(f"  {j}: {lines[j].strip()}")
            print("-" * 40)

search_file(r'd:\dev\BP-8Blocks\templates\index_backup.html')
