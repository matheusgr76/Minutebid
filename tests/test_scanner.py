import sys
import os
import unittest

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import scanner

class TestScannerMatching(unittest.TestCase):
    def test_calculate_similarity(self):
        # Should be high similarity
        score1 = scanner._calculate_similarity("Everton", "Everton FC")
        score2 = scanner._calculate_similarity("Liverpool", "Liverpool FC")
        self.assertGreater(score1, 0.7)
        self.assertGreater(score2, 0.7)
        
        # Should be low similarity
        score3 = scanner._calculate_similarity("Arsenal", "Chelsea")
        self.assertLess(score3, 0.3)

    def test_lookup_reference_prob_basic(self):
        event = {"title": "Liverpool vs Everton"}
        ref_prices = {
            "Liverpool FC v Everton FC": {
                "liverpool": 0.8,
                "everton": 0.1,
                "draw": 0.1
            }
        }
        
        # Match outcome "Liverpool"
        prob = scanner._lookup_reference_prob(event, "Liverpool", ref_prices)
        self.assertEqual(prob, 0.8)
        
        # Match outcome "Everton"
        prob = scanner._lookup_reference_prob(event, "Everton", ref_prices)
        self.assertEqual(prob, 0.1)

    def test_lookup_reference_prob_containment(self):
        # "Will Liverpool win?" market question
        event = {"title": "Liverpool vs Everton"}
        ref_prices = {
            "Liverpool v Everton": {
                "liverpool": 0.85,
                "everton": 0.05,
                "draw": 0.1
            }
        }
        
        prob = scanner._lookup_reference_prob(event, "Will Liverpool win?", ref_prices)
        self.assertEqual(prob, 0.85)

    def test_filter_opportunities_no_match(self):
        events = [{"id": "1", "title": "A vs B", "markets": [{"conditionId": "c1", "question": "A"}]}]
        prices = {"c1": 0.9}
        # In range but no period = second half default
        game_states = {"1": {"minute": 80, "period": "2H", "home_score": 1, "away_score": 0}}
        ref_prices = {} # No reference prices
        
        opps = scanner.filter_opportunities(events, prices, game_states, ref_prices)
        self.assertEqual(len(opps), 1)
        self.assertEqual(opps[0]["poly_prob"], 0.9)
        self.assertIsNone(opps[0]["reference_prob"])

if __name__ == '__main__':
    unittest.main()
