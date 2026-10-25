import unittest
import numpy as np
from main import IndoorMap, Robot, MCL

class TestSimulationSmoke(unittest.TestCase):
    def test_map_validity(self):
        world = IndoorMap()
        self.assertTrue(world.valid(0.9, 0.9))
        self.assertFalse(world.valid(2.2, 2.0))

    def test_lidar_and_filter_step(self):
        rng = np.random.default_rng(7)
        world = IndoorMap()
        robot = Robot(world, rng)
        scan = robot.sense()
        self.assertEqual(scan.shape, (len(robot.beams),))
        self.assertTrue(np.all(scan > 0))
        mcl = MCL(world, 25, np.random.default_rng(8), robot.beams, robot.max_range)
        odom = robot.move(0.2, 0.0)
        estimate = mcl.step(odom, robot.sense())
        self.assertEqual(estimate.shape, (3,))
        self.assertTrue(np.all(np.isfinite(estimate)))

if __name__ == "__main__":
    unittest.main()
