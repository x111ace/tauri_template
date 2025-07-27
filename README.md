# Tauri GUI

## How to use

Use the `__mgr__.py` script to manage the project.

Run the following commands in the terminal:
```bash
# If something freezes, 'Ctrl+C' and try again. It will work.
cd tauri-gui
# init project
python __mgr__.py -i
# print file tree
python __mgr__.py -t
# clean build artifacts
python __mgr__.py -c
# clean dependencies
python __mgr__.py -f
# start dev server
python __mgr__.py -d
```

## File tree

```
{
    "folders": 21,
    "files": {
        "total": 58,
        "by_type": {
            "TypeScript": {
                "files": 2,
                "lines": 106
            },
            "CSS": {
                "files": 3,
                "lines": 68
            },
            "Svelte": {
                "files": 5,
                "lines": 134
            },
            "HTML": {
                "files": 1,
                "lines": 14
            },
            "Rust": {
                "files": 2,
                "lines": 19
            },
            "Python": {
                "files": 1,
                "lines": 588
            },
            "JavaScript": {
                "files": 2,
                "lines": 35
            }
        }
    }
}
tauri-gui/
├── config/                                 # TypeScript compiler configurations
│   ├── tsconfig.base.json                  # Base TSConfig for shared settings
│   └── tsconfig.main.json                  # Specific TSConfig for the main process
├── icons/                                  # Application icons for different platforms
│   ├── favicon_io/                         # Raw icon assets downloaded from favicon.io
│   │   ├── android-chrome-192x192.png      # Icon for Android Chrome
│   │   ├── android-chrome-512x512.png      # Larger icon for Android Chrome
│   │   ├── apple-touch-icon.png            # Icon for iOS devices
│   │   ├── favicon-16x16.png               # 16x16 pixel favicon
│   │   ├── favicon-32x32.png               # 32x32 pixel favicon
│   │   ├── favicon.ico                     # Standard favicon file for older browsers
│   │   └── site.webmanifest                # Web app manifest for PWA capabilities
│   ├── #.#ICONS.md                         # Documentation for application icons
│   ├── favicon.ico                         # Primary favicon for the application
│   └── icon.png                            # The main application icon used by Tauri for the executable
├── renderer/                               # SvelteKit frontend source code
│   ├── lib/                                # SvelteKit library directory for reusable code/components
│   │   ├── #.#COMPS.md                     # Documentation for Svelte components
│   │   ├── api.ts :: 37 lines              # Frontend API to communicate with the Rust backend
│   │   └── mouseEffects.ts :: 69 lines     # UI mouse effects library
│   ├── routes/                             # SvelteKit file-based routing directory
│   │   ├── entry/                          # Route for the application's entry page
│   │   │   ├── styles/
│   │   │   │   └── entry-page.css :: 34 lines      # Styles specific to the entry page
│   │   │   └── +page.svelte :: 22 lines            # Svelte component for the entry page
│   │   ├── game/                                   # Route for the main game/interactive page
│   │   │   ├── styles/
│   │   │   │   └── game-page.css :: 15 lines       # Styles specific to the game page
│   │   │   ├── +page.svelte :: 32 lines            # Svelte component for the game page
│   │   │   └── Draggable.svelte :: 58 lines        # A reusable draggable component
│   │   ├── #.#ROUTES.md                    # Documentation for application routes
│   │   ├── +layout.svelte :: 9 lines       # The root layout for all pages
│   │   └── +page.svelte :: 13 lines        # The root/home page svelte component
│   ├── static/                             # Static assets that are copied as-is
│   │   ├── fonts/                          # Directory for custom fonts
│   │   │   └── aattackgraffiti/
│   │   │       └── placeholder.txt         # Placeholder for a font file
│   │   ├── styles/
│   │   │   └── main.css :: 19 lines        # Global CSS styles
│   │   ├── #.#STATIC.md                    # Documentation for static assets
│   │   └── favicon.png                     # Favicon for the web view
│   ├── utils/                              # Utility functions for the frontend
│   │   └── #.#UTILS.md                     # Documentation for utility functions
│   ├── #.#RENDERER.md                      # High-level documentation for the frontend
│   └── app.html :: 14 lines                # The main HTML shell for the SvelteKit app
├── shared/                                 # Code/types shared between frontend and backend
│   └── #.#SHARED.md                        # Documentation for shared code
├── src/                                    # Rust source code for the Tauri backend
│   ├── #.#BACKEND.md                       # High-level documentation for the backend
│   └── main.rs :: 16 lines                 # The main entry point for the Rust application
├── .gitignore                              # Specifies files for Git to ignore
├── __mgr__.py :: 588 lines                 # The all-powerful project management script
├── build.rs :: 3 lines                     # Rust build script, for compile-time tasks
├── Cargo.toml                              # Rust's package manager manifest file
├── package.json                            # Node.js package manager manifest file
├── python                                  # Python interpreter or script reference
├── README.md                               # This file, explaining the project
├── svelte.config.js :: 29 lines            # SvelteKit configuration file
├── tauri.conf.json                         # Tauri's main configuration file
├── tsconfig.json                           # Root TypeScript configuration for the project
└── vite.config.js :: 6 lines               # Vite (the frontend build tool) configuration
```