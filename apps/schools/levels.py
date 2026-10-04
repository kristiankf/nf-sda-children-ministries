from django.db import models


class ClassLevel(models.TextChoices):
    PRESCHOOL = "PRESCHOOL", "Pre-school"
    BASIC_1 = "BASIC_1", "Basic 1"
    BASIC_2 = "BASIC_2", "Basic 2"
    BASIC_3 = "BASIC_3", "Basic 3"
    BASIC_4 = "BASIC_4", "Basic 4"
    BASIC_5 = "BASIC_5", "Basic 5"
    BASIC_6 = "BASIC_6", "Basic 6"
    JHS_1 = "JHS_1", "JHS 1"
    JHS_2 = "JHS_2", "JHS 2"
    JHS_3 = "JHS_3", "JHS 3"
    SHS_1 = "SHS_1", "SHS 1"
    SHS_2 = "SHS_2", "SHS 2"
    SHS_3 = "SHS_3", "SHS 3"


CLASS_LADDER = tuple(choice.value for choice in ClassLevel)


def next_class_level(level: str) -> str:
    """The next class, or the same class when the child is already in SHS 3."""
    if level not in CLASS_LADDER:
        return level
    index = CLASS_LADDER.index(level)
    if index == len(CLASS_LADDER) - 1:
        return level
    return CLASS_LADDER[index + 1]
