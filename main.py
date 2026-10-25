"""Monte Carlo Localization for a simulated indoor robot.

Run: python main.py --steps 120 --particles 180
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
        return np.array([local_dx+self.rng.normal(0, 0.035),
                         local_dy+self.rng.normal(0, 0.012),
                         wrap_angle(self.pose[2]-old[2])+self.rng.normal(0, 0.025)])

    def sense(self):
        ranges = self.world.raycast(self.pose[0], self.pose[1],
                                    self.pose[2]+self.beams, self.max_range)
        return np.clip(ranges+self.rng.normal(0, self.lidar_sigma, len(ranges)), 0.05, self.max_range)

class MCL:
    def __init__(self, world, n, rng, beams, max_range, initial=(0.9, 0.9, 0.10)):
        self.world, self.n, self.rng = world, n, rng
        self.beams, self.max_range = beams, max_range
        self.particles = []
        while len(self.particles) < n:
            x, y = rng.normal(initial[0], 0.28), rng.normal(initial[1], 0.28)
            t = rng.normal(initial[2], 0.22)
            if world.valid(x, y):
                self.particles.append([x, y, wrap_angle(t)])
        self.particles = np.asarray(self.particles)
        self.weights = np.full(n, 1/n)

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
        logw -= np.max(logw)
        w = np.exp(np.clip(logw, -60, 0))+1e-12
        self.weights = w/w.sum()
        x = np.sum(self.weights*self.particles[:, 0])
        y = np.sum(self.weights*self.particles[:, 1])
        s = np.sum(self.weights*np.sin(self.particles[:, 2]))
        c = np.sum(self.weights*np.cos(self.particles[:, 2]))
        estimate = np.array([x, y, np.arctan2(s, c)])
        # Systematic resampling
        positions = (self.rng.random()+np.arange(self.n))/self.n
        cumulative = np.cumsum(self.weights); cumulative[-1] = 1.0
        indices = np.searchsorted(cumulative, positions)
        self.particles = self.particles[indices].copy()
        self.weights.fill(1/self.n)
        return estimate

def control(step):
    phase = step % 42
    if phase < 30:
        return 0.48, 0.0
    if phase < 36:
        return 0.12, 0.62
    return 0.36, -0.20

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", type=int, default=120)
    parser.add_argument("--particles", type=int, default=180)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", default="outputs")
    args = parser.parse_args()
    os.makedirs(args.output, exist_ok=True)
    rng = np.random.default_rng(args.seed)
    world = IndoorMap()
    robot = Robot(world, rng)
    mcl = MCL(world, args.particles, np.random.default_rng(args.seed+1), robot.beams, robot.max_range)
    truths, estimates, particles, scans, errors = [], [], [], [], []
    for step in range(args.steps):
        v, omega = control(step)
        odom = robot.move(v, omega)
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
