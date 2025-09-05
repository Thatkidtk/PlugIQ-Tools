from __future__ import annotations


FULL = r"""
PPPPPP  LL        UU   UU   GGGGG    IIIII    QQQQQ
PP   PP LL        UU   UU  GG          II    QQ   QQ
PPPPPP  LL        UU   UU  GG  GGG     II    QQ   QQ
PP      LL        UU   UU  GG   GG     II    QQ  QQQ
PP      LLLLLL     UUUUU    GGGGGG    IIIII   QQQQQQ
""".strip("\n")


SUBTITLE = "PlugIQ Cable Tester"


COMPACT = r"""
PLUGIQ • Cable Tester
""".strip("\n")


def get_banner(compact: bool = False) -> str:
    return (COMPACT if compact else FULL)

