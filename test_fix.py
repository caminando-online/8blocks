from decimal import Decimal

def _clean_currency(value: str) -> str:
    if not value or not isinstance(value, str):
        if isinstance(value, (int, float, Decimal)):
            return str(value)
        return '0'
    clean = value.replace('$', '').replace('€', '').replace('%', '').strip()
    if '.' in clean and ',' in clean:
        if clean.rfind('.') < clean.rfind(','):
            clean = clean.replace('.', '').replace(',', '.')
    elif ',' in clean:
        clean = clean.replace(',', '.')
    return clean

def test_extraction_logic():
    # Simulate form data sent by the UI
    data = {
        'difficulty_method': 'backlog',
        'manual_diff_var_1': '1.5',
        'manual_diff_var_2': '2.0',
        'manual_diff_var_3': '2.5',
        'manual_diff_var_4': '3.0',
        'manual_diff_var_5': '3.5',
        'manual_diff_var_6': '4.0',
        'manual_diff_var_7': '4.5',
        'manual_diff_var_8': '5.0',
    }

    # The logic I implemented:
    manual_difficulty_variations = [Decimal(_clean_currency(data.get(f'manual_diff_var_{i}', '0'))) for i in range(1, 9)]

    print(f"Extracted variations: {manual_difficulty_variations}")
    
    expected = [Decimal('1.5'), Decimal('2.0'), Decimal('2.5'), Decimal('3.0'), 
                Decimal('3.5'), Decimal('4.0'), Decimal('4.5'), Decimal('5.0')]
    
    assert manual_difficulty_variations == expected
    print("✅ Extraction logic test passed!")

if __name__ == "__main__":
    test_extraction_logic()
