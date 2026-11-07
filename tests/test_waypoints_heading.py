import unittest
import numpy as np

from main import WAYPOINTS, control
from experiments import run_trial


class TestWaypointAndPoseMetrics(unittest.TestCase):
    def test_waypoint_loop_has_four_free_space_targets(self):
        self.assertEqual(WAYPOINTS.shape, (4, 2))
        from main import IndoorMap
        world = IndoorMap()
        for x, y in WAYPOINTS:
            self.assertTrue(world.valid(float(x), float(y)))

    def test_controller_advances_at_waypoint(self):
        pose = np.array([WAYPOINTS[0, 0], WAYPOINTS[0, 1], np.pi / 2])
        v, omega, next_index = control(pose, waypoint_index=0)
        self.assertEqual(next_index, 1)
        self.assertTrue(np.isfinite(v))
        self.assertTrue(np.isfinite(omega))

    def test_experiment_records_heading_error(self):
        result = run_trial(
            seed=7,
            steps=12,
            particle_count=25,
            method="systematic",
            scenario="tracking",
        )
        self.assertIn("mean_heading_error_deg", result)
        self.assertIn("final_heading_error_deg", result)
        self.assertIn("p95_heading_error_deg", result)
        self.assertIn("sustained_recovery_steps", result)
        self.assertIn("heading_recovery_steps", result)
        self.assertIn("post_recovery_mean_position_error_m", result)
        self.assertIn("post_recovery_mean_heading_error_deg", result)
        self.assertGreaterEqual(result["mean_heading_error_deg"], 0.0)
        self.assertLessEqual(result["p95_heading_error_deg"], 180.0)


if __name__ == "__main__":
    unittest.main()
