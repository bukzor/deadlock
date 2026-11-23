from .load import load_all


class DescribeLoadAll:
    def it_loads_every_experiment(self):
        experiments = load_all()
        assert list(experiments) == ["crimson_slash"]
        heals = [s.heal for s in experiments["crimson_slash"][0].scenarios]
        assert heals == [464, 467, 558, 923]
