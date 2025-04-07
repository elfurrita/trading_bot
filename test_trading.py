import unittest
from unittest.mock import patch, MagicMock
from trading_bot.trading import buy_crypto, sell_crypto, get_avg_volume, calculate_position_size, macd_confirmation

class TestTrading(unittest.TestCase):

    @patch('trading_bot.trading.Client')
    def test_get_avg_volume(self, MockClient):
        mock_client = MockClient()
        mock_client.get_klines.return_value = [
            [0, 0, 0, 0, 0, 100], [0, 0, 0, 0, 0, 200], [0, 0, 0, 0, 0, 300]
        ]
        avg_volume = get_avg_volume(mock_client, 'BTCUSDT', period=3)
        self.assertEqual(avg_volume, 200)

    @patch('trading_bot.trading.Client')
    def test_calculate_position_size(self, MockClient):
        mock_client = MockClient()
        mock_client.get_klines.return_value = [
            [0, 0, 0, 0, 0, 100], [0, 0, 0, 0, 0, 200], [0, 0, 0, 0, 0, 300]
        ]
        position_size = calculate_position_size(mock_client, 'BTCUSDT', 100)
        self.assertGreater(position_size, 0)

    @patch('trading_bot.trading.Client')
    def test_macd_confirmation(self, MockClient):
        mock_client = MockClient()
        mock_client.get_klines.return_value = [
            [0, 0, 0, 0, 100], [0, 0, 0, 0, 200], [0, 0, 0, 0, 300]
        ]
        confirmation = macd_confirmation(mock_client, 'BTCUSDT')
        self.assertIsInstance(confirmation, bool)

    @patch('trading_bot.trading.Client')
    def test_buy_crypto(self, MockClient):
        mock_client = MockClient()
        mock_client.get_price.return_value = 100
        mock_client.get_volume.return_value = 1000
        mock_client.get_avg_volume.return_value = 800
        mock_client.macd_confirmation.return_value = True
        price, quantity = buy_crypto(mock_client, 'BTCUSDT', 1000)
        self.assertIsNotNone(price)
        self.assertIsNotNone(quantity)

    @patch('trading_bot.trading.Client')
    def test_sell_crypto(self, MockClient):
        mock_client = MockClient()
        mock_client.get_price.return_value = 200
        sell_crypto(mock_client, 'BTCUSDT', 100, 10, 0.05, 0.02)
        mock_client.order_limit_sell.assert_called()

if __name__ == '__main__':
    unittest.main()