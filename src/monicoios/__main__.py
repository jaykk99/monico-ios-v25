"""iOS entry point.

The Briefcase iOS bootstrap runs the app's main module as ``__main__``
(runpy ``_run_module_as_main``), so this module starts the Toga app.
"""
from monicoios.app import main

if __name__ == "__main__":
    app = main()
    if app is not None:
        app.main_loop()
    # app is None in headless dev mode (no Toga GUI backend): main() has
    # already started the web server in the foreground.
