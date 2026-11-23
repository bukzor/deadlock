"""Model of one Crimson Slash cast: damage dealt and self-heal.

Constants come from the game data (`data/gamedata.json/scripts/abilities.json`),
for a fully upgraded Crimson Slash with Mystic Reverb and Tankbuster imbued.
Damage values are unrounded; the game rounds each damage number randomly.

Run `python crimson_slash_model.py` to compare the model with
`crimson_slash_test_data.py`.
"""

from dataclasses import dataclass
from typing import final

from crimson_slash_test_data import SETUPS, ExperimentalSetup, Scenario


@final
class CrimsonSlash:  # citadel_ability_healing_slash
    @final
    class Damage:
        BASE = 55
        SPIRIT_SCALE = 0.37
        SPIRIT_SCALE_T3 = 0.6  # third upgrade

    @final
    class Heal:
        BASE = 55  # HealFixedHealth
        SPIRIT_SCALE = 1.035871
        SPIRIT_SCALE_T3 = 0.4  # third upgrade
        MAX_HEALTH_T2 = 0.06  # second upgrade: HealMaxHealth, a percentage


@final
class Tankbuster:  # upgrade_magic_shock; ignores spirit resist
    DAMAGE = 40
    CURRENT_HEALTH_DAMAGE = 0.075


@final
class MysticReverb:  # upgrade_mystic_reverb
    ECHO_DAMAGE = 0.5  # TechDamagePercent
    IMBUE_LIFESTEAL = 0.22
    HERO_LIFESTEAL = 0.08


@dataclass(frozen=True, kw_only=True)
class Prediction:
    hit_damage: float  # slash plus Tankbuster, shown as one number
    echo_damage: float | None  # only with Mystic Reverb
    hit_heal: float
    echo_heal: float | None  # only with Mystic Reverb


def resisted(damage: float, spirit_resist: float) -> float:
    return damage * (1 - spirit_resist)


def slash_damage_raw(spirit: float) -> float:
    """Slash damage before the target's spirit resist."""
    d = CrimsonSlash.Damage
    from_spirit = (d.SPIRIT_SCALE + d.SPIRIT_SCALE_T3) * spirit
    return d.BASE + from_spirit


def tankbuster_damage(*, dummy_health: float, slash_damage: float) -> float:
    """Tankbuster's proc, computed on the health the slash left behind."""
    health_left = dummy_health - slash_damage
    from_health = Tankbuster.CURRENT_HEALTH_DAMAGE * health_left
    return Tankbuster.DAMAGE + from_health


def echo_damage(*, slash_raw: float, tankbuster: float, spirit_resist: float) -> float:
    """Reverb repeats the hit's pre-resist damage; the echo itself is resisted."""
    echoed = MysticReverb.ECHO_DAMAGE * (slash_raw + tankbuster)
    return resisted(echoed, spirit_resist)


def slash_heal(*, spirit: float, hero_max_health: float) -> float:
    h = CrimsonSlash.Heal
    from_spirit = (h.SPIRIT_SCALE + h.SPIRIT_SCALE_T3) * spirit
    from_max_health = h.MAX_HEALTH_T2 * hero_max_health
    return h.BASE + from_spirit + from_max_health


def reverb_lifesteal(damage: float) -> float:
    rate = MysticReverb.IMBUE_LIFESTEAL + MysticReverb.HERO_LIFESTEAL
    return rate * damage


def predict(
    *,
    spirit: float,
    hero_max_health: float,
    dummy_health: float,
    spirit_resist: float,
    tankbuster: bool,
    reverb: bool,
) -> Prediction:
    slash_raw = slash_damage_raw(spirit)
    slash = resisted(slash_raw, spirit_resist)
    if tankbuster:
        proc = tankbuster_damage(dummy_health=dummy_health, slash_damage=slash)
    else:
        proc = 0.0
    hit_damage = slash + proc
    heal = slash_heal(spirit=spirit, hero_max_health=hero_max_health)
    if reverb:
        echo = echo_damage(
            slash_raw=slash_raw, tankbuster=proc, spirit_resist=spirit_resist
        )
        return Prediction(
            hit_damage=hit_damage,
            echo_damage=echo,
            hit_heal=heal + reverb_lifesteal(hit_damage),
            echo_heal=reverb_lifesteal(echo),
        )
    else:
        return Prediction(
            hit_damage=hit_damage, echo_damage=None, hit_heal=heal, echo_heal=None
        )


def predict_scenario(setup: ExperimentalSetup, s: Scenario) -> Prediction:
    items = setup.items + s.items
    return predict(
        spirit=setup.spirit,
        hero_max_health=s.health.max,
        dummy_health=setup.dummy.max_health,
        spirit_resist=setup.dummy.spirit_resist,
        tankbuster="Tankbuster" in items,
        reverb="Mystic Reverb" in items,
    )


def format_pair(observed: int | None, predicted: float | None) -> str:
    if observed is None or predicted is None:
        assert observed is None and predicted is None, (observed, predicted)
        return f"{'':>14}"
    else:
        return f"{observed:>6} {predicted:>7.1f}"


def format_row(setup: ExperimentalSetup, s: Scenario) -> str:
    p = predict_scenario(setup, s)
    h = s.health
    match s.damage:
        case (hit,):
            echo = None
        case (hit, echo):
            pass
        case _:
            raise AssertionError(s.damage)
    return (
        f"{s.name:<18}{setup.spirit:>4}{setup.dummy.max_health:>6} "
        + format_pair(hit, p.hit_damage)
        + format_pair(echo, p.echo_damage)
        + format_pair(h.hit - h.start, p.hit_heal)
        + format_pair(s.echo_heal, p.echo_heal)
    )


def main():
    print(
        f"{'scenario':<18}{'spi':>4}{'tgt':>6} "
        + "".join(
            f"{col:>14}" for col in ("hit dmg", "echo dmg", "hit heal", "echo heal")
        )
    )
    print(f"{'':<29}" + f"{'seen  model':>14}" * 4)
    for setup in SETUPS:
        for s in setup.scenarios:
            print(format_row(setup, s))


if __name__ == "__main__":
    main()
