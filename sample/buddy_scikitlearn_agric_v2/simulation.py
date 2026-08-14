from kaggle_environments import make


class Simulator:

    def __init__(self, debug=False):

        self.debug = debug

    # --------------------------------------------------------

    def run(

        self,

        agent1,

        agent2="random",

        render=False,

    ):

        env = make(
            "kaggriculture",
            debug=self.debug,
        )

        env.run([agent1, agent2])

        if render:
            try:
                env.render(
                    mode="ipython",
                    width=900,
                    height=700,
                )
            except:
                pass

        return env

    # --------------------------------------------------------

    def result(self, env):

        final = env.steps[-1]

        results = []

        for i, s in enumerate(final):

            results.append(
                {
                    "player": i,
                    "reward": s.reward,
                    "status": s.status,
                }
            )

        return results

    # --------------------------------------------------------

    def winner(self, env):

        result = self.result(env)

        if len(result) < 2:
            return None

        if result[0]["reward"] > result[1]["reward"]:
            return 0

        if result[1]["reward"] > result[0]["reward"]:
            return 1

        return -1

    # --------------------------------------------------------

    def evaluate(

        self,

        agent,

        opponent="random",

        episodes=20,

    ):

        wins = 0
        losses = 0
        draws = 0

        rewards = []

        for _ in range(episodes):

            env = self.run(
                agent,
                opponent,
            )

            r = self.result(env)

            rewards.append(r[0]["reward"])

            w = self.winner(env)

            if w == 0:
                wins += 1

            elif w == 1:
                losses += 1

            else:
                draws += 1

        return {

            "episodes": episodes,

            "wins": wins,

            "losses": losses,

            "draws": draws,

            "win_rate": wins / episodes,

            "avg_reward": sum(rewards) / len(rewards),

            "max_reward": max(rewards),

            "min_reward": min(rewards),

        }

    # --------------------------------------------------------

    def compare(

        self,

        agent_a,

        agent_b,

        episodes=20,

    ):

        a = self.evaluate(
            agent_a,
            opponent=agent_b,
            episodes=episodes,
        )

        b = self.evaluate(
            agent_b,
            opponent=agent_a,
            episodes=episodes,
        )

        return {

            "agent_a": a,

            "agent_b": b,

        }
