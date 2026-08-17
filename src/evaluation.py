import copy
import time

import matplotlib.pyplot as plt
import numpy as np
from kaggle_environments import make

import agent

# Configuration
NUM_EPISODES = 10
COPY_OBSERVATION = False


def evaluate_agents(agent1, agent2, num_episodes=10):
    env = make("kaggriculture")

    results = {
        "agent1_scores": [],
        "agent2_scores": [],
        "agent1_times": [],
        "agent2_times": [],
        "errors": [],
    }

    print(f"Starting evaluation of {num_episodes} independent episodes...")

    for i in range(num_episodes):
        # We wrap the agents to measure decision time and optionally protect the engine state
        def wrapped_agent1(obs):
            safe_obs = copy.deepcopy(obs) if COPY_OBSERVATION else obs
            t0 = time.perf_counter()
            act = agent1(safe_obs)
            results["agent1_times"].append(time.perf_counter() - t0)
            return act

        def wrapped_agent2(obs):
            safe_obs = copy.deepcopy(obs) if COPY_OBSERVATION else obs
            t0 = time.perf_counter()
            act = agent2(safe_obs)
            results["agent2_times"].append(time.perf_counter() - t0)
            return act

        # Run the episode (this independently evaluates a full game)
        steps = env.run([wrapped_agent1, wrapped_agent2])
        final_state = steps[-1]

        # Check for environment errors exposed in the final state
        if final_state[0].status == "ERROR" or final_state[1].status == "ERROR":
            results["errors"].append(
                (i, final_state[0].status, final_state[1].status)
            )

        # The score is stored in the reward field
        r1 = final_state[0].reward if final_state[0].reward is not None else 0
        r2 = final_state[1].reward if final_state[1].reward is not None else 0

        results["agent1_scores"].append(r1)
        results["agent2_scores"].append(r2)

        print(
            f"Episode {i + 1}/{num_episodes} Complete | Agent 1: {r1:.1f} | Agent 2: {r2:.1f}"
        )

    return results


def print_summary(results):
    a1_scores = np.array(results["agent1_scores"])
    a2_scores = np.array(results["agent2_scores"])

    wins = np.sum(a1_scores > a2_scores)
    losses = np.sum(a1_scores < a2_scores)
    ties = np.sum(a1_scores == a2_scores)

    n = len(a1_scores)
    a1_sem = np.std(a1_scores, ddof=1) / np.sqrt(n) if n > 1 else 0
    a2_sem = np.std(a2_scores, ddof=1) / np.sqrt(n) if n > 1 else 0

    print("=" * 40)
    print("EVALUATION SUMMARY")
    print("=" * 40)
    print(f"Total Episodes: {n}")
    print(f"Win/Loss/Tie: {wins}W - {losses}L - {ties}T")
    print(f"Win Rate: {(wins / n) * 100:.1f}%\n")

    print("Agent 1 (Challenger) Stats:")
    print(f"  Mean Score:   {np.mean(a1_scores):.2f} (± {a1_sem:.2f} SEM)")
    print(f"  Median Score: {np.median(a1_scores):.2f}")
    print(f"  Std Dev:      {np.std(a1_scores, ddof=1) if n > 1 else 0:.2f}")
    print(f"  Min/Max:      {np.min(a1_scores):.2f} / {np.max(a1_scores):.2f}")
    print(
        f"  Average Agent Decision Time: {np.mean(results['agent1_times']) * 1000:.2f} ms\n"
    )

    print("Agent 2 (Baseline) Stats:")
    print(f"  Mean Score:   {np.mean(a2_scores):.2f} (± {a2_sem:.2f} SEM)")
    print(
        f"  Average Agent Decision Time: {np.mean(results['agent2_times']) * 1000:.2f} ms\n"
    )

    if results["errors"]:
        print(
            f"WARNING: {len(results['errors'])} episodes ended in an ERROR state."
        )
    else:
        print("No errors detected during evaluation.")


def plot_scores_over_time(results):
    episodes = range(1, len(results["agent1_scores"]) + 1)

    plt.figure()
    plt.plot(
        episodes,
        results["agent1_scores"],
        marker="o",
        label="Agent 1 (Challenger)",
    )
    plt.plot(
        episodes,
        results["agent2_scores"],
        marker="o",
        label="Agent 2 (Baseline)",
    )
    plt.title("Scores per Episode")
    plt.xlabel("Episode")
    plt.ylabel("Final Score")
    plt.legend()
    plt.show()


def plot_score_distribution(results):
    plt.figure()
    plt.hist(results["agent1_scores"], alpha=0.7, bins=10, label="Agent 1")
    plt.hist(results["agent2_scores"], alpha=0.7, bins=10, label="Agent 2")
    plt.title("Score Distribution")
    plt.xlabel("Score")
    plt.ylabel("Frequency")
    plt.legend()
    plt.show()


if __name__ == "__main__":
    results = evaluate_agents(agent, agent, num_episodes=NUM_EPISODES)
    plot_scores_over_time(results)
    plot_score_distribution(results)
    print_summary(results)
