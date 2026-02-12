import unittest
from decimal import Decimal
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.domain.value_objects import FinancialMetrics

class TestFinancialMetrics(unittest.TestCase):
    def test_calculate_roi(self):
        # Profit 50, Investment 100 -> 50%
        roi = FinancialMetrics.calculate_roi(Decimal('50'), Decimal('100'))
        self.assertEqual(roi, Decimal('50'))
        
        # Zero investment
        roi = FinancialMetrics.calculate_roi(Decimal('50'), Decimal('0'))
        self.assertEqual(roi, Decimal('0'))

    def test_calculate_cagr(self):
        # BV 100, EV 144, Years 2 -> sqrt(1.44) - 1 = 1.2 - 1 = 0.2 -> 20%
        cagr = FinancialMetrics.calculate_cagr(Decimal('100'), Decimal('144'), 2)
        self.assertAlmostEqual(float(cagr), 20.0, places=5)
        
        # Zero or negative years
        cagr = FinancialMetrics.calculate_cagr(Decimal('100'), Decimal('144'), 0)
        self.assertEqual(cagr, Decimal('0'))

    def test_calculate_break_even_month(self):
        investment = Decimal('100')
        monthly_flows = [Decimal('20'), Decimal('30'), Decimal('50'), Decimal('10')]
        
        # Cumulative: 20, 50, 100 -> Month 3
        be_month = FinancialMetrics.calculate_break_even_month(investment, monthly_flows)
        self.assertEqual(be_month, 3)
        
        # Never reaches investment
        be_month = FinancialMetrics.calculate_break_even_month(Decimal('200'), monthly_flows)
        self.assertIsNone(be_month)

if __name__ == '__main__':
    unittest.main()
