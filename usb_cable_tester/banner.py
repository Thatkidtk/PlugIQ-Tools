from __future__ import annotations


FULL = r"""
PPPPPP  LL        UU   UU   GGGGG    IIIII    QQQQQ
PP   PP LL        UU   UU  GG          II    QQ   QQ
PPPPPP  LL        UU   UU  GG  GGG     II    QQ   QQ
PP      LL        UU   UU  GG   GG     II    QQ  QQQ
PP      LLLLLL     UUUUU    GGGGGG    IIIII   QQQQQQ
""".strip("\n")


COMPACT = r"""
PLUGIQ • Cable Tester
""".strip("\n")


BLOCK = (
    """
▄▖▜     ▄▖▄▖  
▙▌▐ ▌▌▛▌▐ ▌▌  
▌ ▐▖▙▌▙▌▟▖█▌  
      ▄▌   ▘
"""
    .strip("\n")
)


def get_banner(style: str = "full") -> str:
    style = (style or "full").lower()
    if style == "compact":
        return COMPACT
    if style == "block":
        return BLOCK
    return FULL
