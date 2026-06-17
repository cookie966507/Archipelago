from dataclasses import dataclass
from Options import DefaultOnToggle, Toggle, DeathLink, PerGameCommonOptions

class Code1Sanity(Toggle):
    display_name = "Code 1 Sanity"

class Code2Sanity(Toggle):
    display_name = "Code 2 Sanity"

@dataclass
class MousewardOptions(PerGameCommonOptions):
    code_1_sanity: Code1Sanity
    code_2_sanity: Code2Sanity
    death_link: DeathLink