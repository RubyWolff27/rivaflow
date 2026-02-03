"""ASCII art logo and branding for RivaFlow CLI."""

LOGO = r"""
    ____  _            ______
   / __ \(_)   ______ / ____/___ _      __
  / /_/ / / | / / __ `/ /_  / __ \ | /| / /
 / _, _/ /| |/ / /_/ / __/ / /_/ / |/ |/ /
/_/ |_/_/ |___/\__,_/_/    \____/|__/|__/
"""

LOGO_SMALL = r"""
   ___  _           _____ _
  / _ \(_)  _____ _/ ___// /__ _    __
 / , _/ / |/ / _ `/ /_  / / _ \ |/|/ /
/_/|_/_/|___/\_,_/\__/ /_/\___/__,__/
"""

LOGO_MINI = r"""
 ╔═╗┬┬  ┬┌─┐╔═╗┬  ┌─┐┬ ┬
 ╠╦╝│└┐┌┘├─┤╠╣ │  │ ││││
 ╩╚═┴ └┘ ┴ ┴╚  ┴─┘└─┘└┴┘
"""

TAGLINE = "Train Smarter. Track Progress. Flow Forward."

WELCOME_MESSAGE = f"""
{LOGO}
{TAGLINE}

Brazilian Jiu-Jitsu Training Journal
"""

WELCOME_MESSAGE_SMALL = f"""
{LOGO_SMALL}
{TAGLINE}
"""


def print_logo(size: str = "default", tagline: bool = True):
    """
    Print the RivaFlow ASCII logo.

    Args:
        size: Logo size - "default", "small", or "mini"
        tagline: Whether to include the tagline
    """
    if size == "mini":
        print(LOGO_MINI)
    elif size == "small":
        print(LOGO_SMALL)
    else:
        print(LOGO)

    if tagline:
        print(TAGLINE)


def get_logo(size: str = "default") -> str:
    """Get the logo as a string without printing."""
    if size == "mini":
        return LOGO_MINI
    elif size == "small":
        return LOGO_SMALL
    else:
        return LOGO
