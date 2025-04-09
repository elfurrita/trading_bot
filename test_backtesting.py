import unittest
from unittest.mock import patch, MagicMock
from ..trading_bot.backtesting import backtest, optimize_parameters  # Importación relativa

class TestBacktesting(unittest.TestCase):

    @patch('..trading_bot.backtesting.Client')
    def test_backtest(self, MockClient):
        mock_client = MockClient()
        mock_client.get_klines.return_value = [
            [0, 0, 0, 0, 100], [0, 0, 0, 0, 200], [0, 0, 0, 0, 300]
        ]
        result = backtest(mock_client, 'BTCUSDT', 0.05, 0.02)
        self.assertIn('total_profit', result)
        self.assertIn('max_drawdown', result)
        self.assertIn('sharpe_ratio', result)

    @patch('..trading_bot.backtesting.Client')
    def test_optimize_parameters(self, MockClient):
        mock_client = MockClient()
        mock_client.get_klines.return_value = [
            [0, 0, 0, 0, 100], [0, 0, 0, 0, 200], [0, 0, 0, 0, 300]
        ]
        best_params = optimize_parameters(mock_client, 'BTCUSDT')
        self.assertIn('profit_threshold', best_params)
        self.assertIn('trailing_stop', best_params)

if __name__ == '__main__':
    unittest.main()
