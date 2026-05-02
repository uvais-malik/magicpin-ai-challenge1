import unittest

from core.composer import compose


class ComposeTests(unittest.TestCase):
    def test_compose_perf_dip_contains_contract_fields(self):
        category = {
            "slug": "dentists",
            "peer_stats": {"avg_ctr": 0.03},
            "offer_catalog": [{"title": "Dental Cleaning @ Rs 299"}],
            "voice": {"tone": "peer_clinical", "vocab_taboo": ["cure"]},
        }
        merchant = {
            "merchant_id": "m1",
            "category_slug": "dentists",
            "identity": {"name": "Dr. Test Clinic", "owner_first_name": "Test", "locality": "Delhi", "languages": ["en"]},
            "performance": {"views": 1000, "calls": 8, "ctr": 0.018, "delta_7d": {"calls_pct": -0.5}},
            "offers": [],
            "signals": ["perf_dip_severe"],
        }
        trigger = {
            "id": "t1",
            "kind": "perf_dip",
            "scope": "merchant",
            "payload": {"metric": "calls", "delta_pct": -0.5, "window": "7d", "vs_baseline": 12},
            "urgency": 4,
        }
        out = compose(category, merchant, trigger)
        self.assertEqual(set(out), {"body", "cta", "send_as", "suppression_key", "rationale"})
        self.assertEqual(out["send_as"], "vera")
        self.assertIn("50%", out["body"])
        self.assertIn("Fact:", out["body"])
        self.assertTrue(out["cta"])


if __name__ == "__main__":
    unittest.main()
