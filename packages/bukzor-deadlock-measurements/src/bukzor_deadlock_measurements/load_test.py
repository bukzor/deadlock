from .load import load_all


class DescribeLoadAll:
    def it_loads_every_experiment(self):
        (crimson,) = load_all()
        assert crimson.name == "crimson-slash"
        heals = [s.heal for s in crimson.dummies[0].scenarios]
        assert heals == [463, 467, 557, 923]
