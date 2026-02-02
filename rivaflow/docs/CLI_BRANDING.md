# CLI Branding and Visual Identity

## ASCII Art Logo

RivaFlow includes ASCII art branding to create a memorable and professional CLI experience.

### Available Logo Sizes

The `rivaflow/cli/utils/logo.py` module provides three logo sizes:

#### Default Logo (Recommended for welcome screens)
```
    ____  _            ______
   / __ \(_)   ______ / ____/___ _      __
  / /_/ / / | / / __ `/ /_  / __ \ | /| / /
 / _, _/ /| |/ / /_/ / __/ / /_/ / |/ |/ /
/_/ |_/_/ |___/\__,_/_/    \____/|__/|__/
```

#### Small Logo (For constrained screens)
```
   ___  _           _____ _
  / _ \(_)  _____ _/ ___// /__ _    __
 / , _/ / |/ / _ `/ /_  / / _ \ |/|/ /
/_/|_/_/|___/\_,_/\__/ /_/\___/__,__/
```

#### Mini Logo (For inline display)
```
 ╔═╗┬┬  ┬┌─┐╔═╗┬  ┌─┐┬ ┬
 ╠╦╝│└┐┌┘├─┤╠╣ │  │ ││││
 ╩╚═┴ └┘ ┴ ┴╚  ┴─┘└─┘└┴┘
```

### Tagline

**Official tagline:** "Train Smarter. Track Progress. Flow Forward."

This tagline emphasizes:
- **Train Smarter** - Intelligent tracking and insights
- **Track Progress** - Data-driven improvement
- **Flow Forward** - Continuous progress in the journey

### Usage in Code

```python
from rivaflow.cli.utils.logo import LOGO, TAGLINE, print_logo, get_logo

# Print logo with tagline
print_logo(size="default", tagline=True)

# Print small logo without tagline
print_logo(size="small", tagline=False)

# Get logo as string
logo_str = get_logo(size="mini")
```

### Where Logos Appear

1. **First-Run Welcome** (`first_run.py`)
   - Full logo with tagline
   - First impression for new users
   - Clear brand identity

2. **About Command** (`rivaflow about`)
   - Full logo with version info
   - Showcases branding
   - Provides project links

3. **Version Command** (`rivaflow --version`)
   - Mini logo (if space permits)
   - Quick version check

### Design Philosophy

The ASCII art follows these principles:

1. **Professional** - Clean, readable fonts that work in any terminal
2. **Recognizable** - Consistent branding across all sizes
3. **Accessible** - Uses standard ASCII characters for maximum compatibility
4. **Memorable** - Distinctive visual identity

### Terminal Compatibility

All logos use standard ASCII characters and are tested to work in:
- macOS Terminal
- iTerm2
- Windows Terminal
- Linux terminal emulators
- VS Code integrated terminal

The mini logo uses Unicode box-drawing characters for visual flair while maintaining readability.

### Color Scheme

When displayed with Rich:
- **Logo text**: Bold cyan (`[bold cyan]`)
- **Tagline**: Dim white (`[dim]`)
- **Accent borders**: Cyan (`border_style="cyan"`)

This creates a cohesive visual identity throughout the CLI.

### Future Enhancements

Potential improvements for future versions:
- Animated logo reveal on first run
- Seasonal variations (holiday themes)
- Achievement-based logo variations (e.g., belt promotions)
- Custom color themes based on user preferences

---

**Last Updated:** 2026-02-02
**Related:** Task #32 from BETA_READINESS_REPORT.md
