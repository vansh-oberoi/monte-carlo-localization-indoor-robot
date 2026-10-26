"""Monte Carlo Localization for a simulated indoor robot.

Run: python main.py --steps 120 --particles 180
Options: --resampler {systematic,multinomial,stratified} --ess-ratio 0.5
         --augmented --kidnap-step 50
"""
import argparse
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


def wrap_angle(a):
    return (a + np.pi) % (2 * np.pi) - np.pi


class IndoorMap:
    def __init__(self, width=10.0, height=10.0):
        self.width, self.height = width, height
        self.obstacles = [(2.0, 1.2, 2.6, 6.2), (4.0, 3.8, 7.8, 4.4),
                          (6.8, 6.0, 7.4, 9.0), (1.0, 7.4, 4.4, 8.0),
                          (8.3, 1.2, 9.0, 3.8)]

    def occupied(self, x, y):
        x, y = np.asarray(x), np.asarray(y)
        hit = (x <= 0) | (x >= self.width) | (y <= 0) | (y >= self.height)
        for x1, y1, x2, y2 in self.obstacles:
            hit |= (x >= x1) & (x <= x2) & (y >= y1) & (y <= y2)
        return hit

    def valid(self, x, y, margin=0.12):
        if x <= margin or x >= self.width-margin or y <= margin or y >= self.height-margin:
            return False
        for x1, y1, x2, y2 in self.obstacles:
            if x1-margin <= x <= x2+margin and y1-margin <= y <= y2+margin:
                return False
        return True

    def raycast(self, x, y, angles, max_range=5.0, step=0.10):
        angles = np.asarray(angles).reshape(-1)
        distances = np.arange(step, max_range + step, step)
        px = x + distances[:, None] * np.cos(angles)[None, :]
        py = y + distances[:, None] * np.sin(angles)[None, :]
        hits = self.occupied(px, py)
        any_hit = hits.any(axis=0)
        idx = np.argmax(hits, axis=0)
        ranges = np.full(len(angles), max_range, dtype=float)
        ranges[any_hit] = distances[idx[any_hit]]
        return ranges

    def draw(self, ax):
        from matplotlib.patches import Rectangle
        ax.set(xlim=(0, self.width), ylim=(0, self.height), xlabel="x (m)", ylabel="y (m)")
        ax.set_aspect("equal")
        ax.add_patch(Rectangle((0, 0), self.width, self.height, fill=False, linewidth=2))
        for x1, y1, x2, y2 in self.obstacles:
            ax.add_patch(Rectangle((x1, y1), x2-x1, y2-y1, color="dimgray"))
        ax.grid(alpha=0.15)


class Robot:
    def __init__(self, world, rng):
        self.world, self.rng = world, rng
        self.pose = np.array([0.9, 0.9, 0.10], dtype=float)
        self.beams = np.linspace(-np.pi, np.pi, 16, endpoint=False)
        self.max_range = 5.0
        self.lidar_sigma = 0.035
        self.odom_noise_scale = 1.0  # multiplies true odometry noise (noise sweeps)

    def move(self, v, omega, dt=0.18):
        old = self.pose.copy()
        mid = old[2] + 0.5*omega*dt
        candidate = old.copy()
        candidate[0] += v*dt*np.cos(mid)
        candidate[1] += v*dt*np.sin(mid)
        candidate[2] = wrap_angle(old[2] + omega*dt)
        if self.world.valid(candidate[0], candidate[1], 0.15):
            self.pose = candidate
        dx, dy = self.pose[0]-old[0], self.pose[1]-old[1]
        local_dx = dx*np.cos(old[2]) + dy*np.sin(old[2])
        local_dy = -dx*np.sin(old[2]) + dy*np.cos(old[2])
        s = self.odom_noise_scale
        return np.array([local_dx+self.rng.normal(0, 0.035*s),
                         local_dy+self.rng.normal(0, 0.012*s),
                         wrap_angle(self.pose[2]-old[2])+self.rng.normal(0, 0.025*s)])

    def sense(self):
        ranges = self.world.raycast(self.pose[0], self.pose[1],
                                    self.pose[2]+self.beams, self.max_range)
        return np.clip(ranges+self.rng.normal(0, self.lidar_sigma, len(ranges)), 0.05, self.max_range)

    def kidnap(self):
        """Teleport the robot to a random free pose (kidnapped-robot test)."""
        while True:
            x = self.rng.uniform(0, self.world.width)
            y = self.rng.uniform(0, self.world.height)
            if self.world.valid(x, y, 0.3):
                self.pose = np.array([x, y, self.rng.uniform(-np.pi, np.pi)])
                return


class MCL:
    def __init__(self, world, n, rng, beams, max_range, initial=(0.9, 0.9, 0.10),
                 resampler="systematic", ess_ratio=None, augmented=False,
                 alpha_slow=0.05, alpha_fast=0.5, max_inject=0.5, global_init=False):
        if resampler not in ("systematic", "multinomial", "stratified"):
            raise ValueError(f"unknown resampler: {resampler}")
        self.world, self.n, self.rng = world, n, rng
        self.beams, self.max_range = beams, max_range
        self.resampler, self.ess_ratio = resampler, ess_ratio
        self.augmented = augmented
        self.alpha_slow, self.alpha_fast, self.max_inject = alpha_slow, alpha_fast, max_inject
        self.w_slow = self.w_fast = 0.0
        self.avg_likelihood, self.n_eff, self.injected = 0.0, float(n), 0
        if global_init:
            self.particles = np.array([self._random_pose() for _ in range(n)])
        else:
            self.particles = []
            while len(self.particles) < n:
                x, y = rng.normal(initial[0], 0.28), rng.normal(initial[1], 0.28)
                t = rng.normal(initial[2], 0.22)
                if world.valid(x, y):
                    self.particles.append([x, y, wrap_angle(t)])
            self.particles = np.asarray(self.particles)
        self.weights = np.full(n, 1/n)

    def _random_pose(self):
        while True:
            x = self.rng.uniform(0, self.world.width)
            y = self.rng.uniform(0, self.world.height)
            if self.world.valid(x, y, 0.08):
                return [x, y, self.rng.uniform(-np.pi, np.pi)]

    def _resample(self):
        n = self.n
        if self.resampler == "multinomial":
            positions = self.rng.random(n)
        elif self.resampler == "stratified":
            positions = (self.rng.random(n)+np.arange(n))/n
        else:  # systematic
            positions = (self.rng.random()+np.arange(n))/n
        cumulative = np.cumsum(self.weights)
        cumulative[-1] = 1.0
        self.particles = self.particles[np.searchsorted(cumulative, positions)].copy()
        self.weights.fill(1/n)

    def _update_averages(self):
        """Augmented MCL (Thrun et al., Probabilistic Robotics): returns injection probability."""
        w = self.avg_likelihood
        if self.w_slow == 0.0:
            self.w_slow = self.w_fast = w
        self.w_slow += self.alpha_slow*(w-self.w_slow)
        self.w_fast += self.alpha_fast*(w-self.w_fast)
        return min(self.max_inject, max(0.0, 1.0-self.w_fast/max(self.w_slow, 1e-12)))

    def _inject_random(self, p_random):
        mask = self.rng.random(self.n) < p_random
        for i in np.flatnonzero(mask):
            self.particles[i] = self._random_pose()
        self.injected = int(mask.sum())

    def step(self, odom, observed):
        dx, dy, dt = odom
        # Propose noisy odometry updates from each particle's previous valid pose.
        # Reject invalid proposals instead of teleporting particles to random map locations.
        for i in range(self.n):
            previous = self.particles[i].copy()
            theta = previous[2]
            accepted = False
            for _ in range(10):
                dx_sample = dx + self.rng.normal(0, 0.045)
                dy_sample = dy + self.rng.normal(0, 0.045)
                dt_sample = dt + self.rng.normal(0, 0.035)
                candidate_x = previous[0] + dx_sample*np.cos(theta) - dy_sample*np.sin(theta)
                candidate_y = previous[1] + dx_sample*np.sin(theta) + dy_sample*np.cos(theta)
                candidate_theta = wrap_angle(theta + dt_sample)
                if self.world.valid(candidate_x, candidate_y, 0.08):
                    self.particles[i] = [candidate_x, candidate_y, candidate_theta]
                    accepted = True
                    break
            if not accepted:
                # Keep the previous valid pose if all motion proposals are invalid.
                self.particles[i] = previous
        logw = np.empty(self.n)
        for i, p in enumerate(self.particles):
            predicted = self.world.raycast(p[0], p[1], p[2]+self.beams, self.max_range)
            residual = np.clip(observed-predicted, -2.5, 2.5)
            logw[i] = -0.5*np.mean((residual/0.32)**2)
        self.avg_likelihood = float(np.exp(logw).mean())  # raw likelihood, before normalising
        logw -= np.max(logw)
        # Multiply by prior weights (equal to 1/n right after any resampling step).
        w = self.weights*np.exp(np.clip(logw, -60, 0)) + 1e-12
        self.weights = w/w.sum()
        x = np.sum(self.weights*self.particles[:, 0])
        y = np.sum(self.weights*self.particles[:, 1])
        s = np.sum(self.weights*np.sin(self.particles[:, 2]))
        c = np.sum(self.weights*np.cos(self.particles[:, 2]))
        estimate = np.array([x, y, np.arctan2(s, c)])
        self.n_eff = float(1.0/np.sum(self.weights**2))
        p_random = self._update_averages() if self.augmented else 0.0
        self.injected = 0
        if self.ess_ratio is None or self.n_eff < self.ess_ratio*self.n:
            self._resample()
            if p_random > 0:
                self._inject_random(p_random)
        return estimate


def control(step, scan=None, beams=None):
    # Reactive obstacle avoidance using the current LiDAR scan.
    if scan is None or beams is None:
        return 0.25, 0.0

    front_angles = np.abs(np.arctan2(np.sin(beams), np.cos(beams)))
    front = scan[front_angles < np.deg2rad(35)]

    if len(front) and np.min(front) < 0.65:
        # Turn in place when an obstacle is too close ahead.
        left = scan[(beams > 0) & (beams < np.pi)]
        right = scan[(beams < 0) & (beams > -np.pi)]

        left_clearance = np.mean(left) if len(left) else 0.0
        right_clearance = np.mean(right) if len(right) else 0.0

        return 0.0, 0.65 if left_clearance >= right_clearance else -0.65

    return 0.30, 0.0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", type=int, default=120)
    parser.add_argument("--particles", type=int, default=180)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", default="outputs")
    parser.add_argument("--resampler", choices=["systematic", "multinomial", "stratified"],
                        default="systematic")
    parser.add_argument("--ess-ratio", type=float, default=None,
                        help="resample only when N_eff < ratio * N (e.g. 0.5)")
    parser.add_argument("--augmented", action="store_true",
                        help="augmented MCL: inject random particles when likelihood drops")
    parser.add_argument("--kidnap-step", type=int, default=None,
                        help="teleport the robot at this step to test recovery")
    args = parser.parse_args()
    os.makedirs(args.output, exist_ok=True)
    rng = np.random.default_rng(args.seed)
    world = IndoorMap()
    robot = Robot(world, rng)
    mcl = MCL(world, args.particles, np.random.default_rng(args.seed+1), robot.beams, robot.max_range,
              resampler=args.resampler, ess_ratio=args.ess_ratio, augmented=args.augmented)
    truths, estimates, particles, scans, errors = [], [], [], [], []
    for step in range(args.steps):
        initial_scan = robot.sense()
        v, omega = control(step, initial_scan, robot.beams)
        odom = robot.move(v, omega)
        if args.kidnap_step is not None and step == args.kidnap_step:
            robot.kidnap()
        scan = robot.sense()
        estimate = mcl.step(odom, scan)
        truths.append(robot.pose.copy()); estimates.append(estimate.copy())
        particles.append(mcl.particles.copy()); scans.append(scan.copy())
        errors.append(float(np.linalg.norm(estimate[:2]-robot.pose[:2])))
    truths, estimates, particles, scans, errors = map(np.asarray, (truths, estimates, particles, scans, errors))
    print(f"Steps: {args.steps}; particles: {args.particles}")
    print(f"Mean position error: {errors.mean():.4f} m")
    print(f"Final position error: {errors[-1]:.4f} m")
    np.savetxt(os.path.join(args.output, "position_errors.csv"),
               np.c_[np.arange(1, args.steps+1), errors], delimiter=",",
               header="step,position_error_m", comments="")
    fig, (ax, err_ax) = plt.subplots(1, 2, figsize=(13, 6))
    world.draw(ax)
    ax.set_title("Monte Carlo Localization")
    pts = ax.scatter([], [], s=8, alpha=0.35, label="Particles")
    true_line, = ax.plot([], [], "b-", label="Ground truth")
    est_line, = ax.plot([], [], "r--", label="Estimate")
    true_dot, = ax.plot([], [], "bo", label="True robot")
    est_dot, = ax.plot([], [], "rx", markersize=9, label="Estimated pose")
    rays = [ax.plot([], [], color="green", alpha=0.25, linewidth=0.8)[0] for _ in robot.beams]
    err_ax.plot(np.arange(1, args.steps+1), errors)
    if args.kidnap_step is not None:
        err_ax.axvline(args.kidnap_step+1, color="r", linestyle=":", label="kidnap")
        err_ax.legend(fontsize=8)
    err_ax.set(xlabel="Step", ylabel="Position error (m)", title="Localization error")
    err_ax.grid(alpha=0.3)
    ax.legend(fontsize=8, loc="upper left")

    def update(k):
        pts.set_offsets(particles[k][:, :2])
        true_line.set_data(truths[:k+1, 0], truths[:k+1, 1])
        est_line.set_data(estimates[:k+1, 0], estimates[:k+1, 1])
        true_dot.set_data([truths[k, 0]], [truths[k, 1]])
        est_dot.set_data([estimates[k, 0]], [estimates[k, 1]])
        for j, line in enumerate(rays):
            a = truths[k, 2]+robot.beams[j]
            line.set_data([truths[k, 0], truths[k, 0]+scans[k, j]*np.cos(a)],
                          [truths[k, 1], truths[k, 1]+scans[k, j]*np.sin(a)])
        return [pts, true_line, est_line, true_dot, est_dot, *rays]

    animation = FuncAnimation(fig, update, frames=args.steps, interval=65, blit=False, repeat=False)
    fig.tight_layout()
    fig.savefig(os.path.join(args.output, "localization_snapshot.png"), dpi=150)
    plt.show()


if __name__ == "__main__":
    main()