import unittest
import numpy as np

from experiments import recovery_steps


class TestRecoverySteps(unittest.TestCase):
    def test_immediate_recovery(self):
        errors = np.array([2.0, 0.2, 0.3, 0.1, 0.4, 0.2])
        self.assertEqual(recovery_steps(errors, ref=1, hold=5), 0.0)

    def test_recovery_after_several_steps(self):
        errors = np.array([2.0, 1.0, 0.8, 0.4, 0.3, 0.2, 0.1, 0.4])
        self.assertEqual(recovery_steps(errors, ref=1, hold=5), 2.0)

    def test_no_recovery_returns_nan(self):
        errors = np.array([2.0, 0.2, 0.3, 0.4, 0.1, 0.8])
        self.assertTrue(np.isnan(recovery_steps(errors, ref=1, hold=5)))

    def test_error_equal_to_threshold_does_not_count(self):
        errors = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.1, 0.2, 0.3, 0.4])
        self.assertTrue(np.isnan(recovery_steps(errors, ref=0, hold=5)))

    def test_insufficient_remaining_steps_returns_nan(self):
        errors = np.array([2.0, 0.1, 0.2, 0.3])
        self.assertTrue(np.isnan(recovery_steps(errors, ref=1, hold=5)))


    def test_negative_reference_raises_value_error(self):
        with self.assertRaises(ValueError):
            recovery_steps(np.array([0.1, 0.2]), ref=-1, hold=2)

    def test_zero_hold_raises_value_error(self):
        with self.assertRaises(ValueError):
            recovery_steps(np.array([0.1, 0.2]), ref=0, hold=0)

    def test_empty_errors_returns_nan(self):
        self.assertTrue(np.isnan(recovery_steps(np.array([]), ref=0, hold=1)))

    def test_reference_beyond_array_returns_nan(self):
        self.assertTrue(np.isnan(recovery_steps(np.array([0.1, 0.2]), ref=5, hold=1)))


if __name__ == "__main__":
    unittest.main()
