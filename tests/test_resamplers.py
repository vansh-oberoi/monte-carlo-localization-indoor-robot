import unittest
import numpy as np
from main import IndoorMap, Robot, MCL


def make(resampler="systematic", **kw):
    rng = np.random.default_rng(0)
    world = IndoorMap()
    robot = Robot(world, rng)
    return world, robot, MCL(world, 50, np.random.default_rng(1),
                             robot.beams, robot.max_range, resampler=resampler, **kw)


class TestResamplers(unittest.TestCase):
    def test_all_resamplers_keep_particle_count(self):
        for name in ("systematic", "multinomial", "stratified"):
            world, robot, mcl = make(name)
            mcl.weights = np.random.default_rng(2).random(50)
            mcl.weights /= mcl.weights.sum()
            mcl._resample()
            self.assertEqual(mcl.particles.shape, (50, 3))
            self.assertAlmostEqual(mcl.weights.sum(), 1.0)

    def test_unknown_resampler_rejected(self):
        with self.assertRaises(ValueError):
            make("bogus")

    def test_step_returns_finite_estimate(self):
        world, robot, mcl = make(augmented=True)
        est = mcl.step(robot.move(0.3, 0.0), robot.sense())
        self.assertTrue(np.all(np.isfinite(est)))

    def test_augmented_mcl_injects_valid_particles_after_likelihood_drop(self):
        world, robot, mcl = make(augmented=True)

        mcl.w_slow = 1.0
        mcl.w_fast = 1.0
        mcl.avg_likelihood = 0.01

        p_random = mcl._update_averages()

        self.assertGreater(p_random, 0.0)
        self.assertLessEqual(p_random, mcl.max_inject)

        mcl._inject_random(p_random)

        self.assertGreater(mcl.injected, 0)
        self.assertEqual(mcl.particles.shape, (mcl.n, 3))
        self.assertTrue(all(world.valid(p[0], p[1], 0.08) for p in mcl.particles))
        self.assertAlmostEqual(mcl.weights.sum(), 1.0)

    def test_ess_resampling_keeps_weights_normalised(self):
        world, robot, mcl = make(ess_ratio=0.5)
        for _ in range(3):
            mcl.step(robot.move(0.3, 0.0), robot.sense())
        self.assertAlmostEqual(mcl.weights.sum(), 1.0)

    def test_kidnap_lands_on_free_space(self):
        world, robot, _ = make()
        robot.kidnap()
        self.assertTrue(world.valid(robot.pose[0], robot.pose[1]))

    def test_global_init_particles_are_valid(self):
        world, robot, mcl = make(global_init=True)
        self.assertTrue(all(world.valid(p[0], p[1]) for p in mcl.particles))


if __name__ == "__main__":
    unittest.main()