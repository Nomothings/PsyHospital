"""
Web package marker.

Keep this package init side-effect free so importing submodules like
``web.service_layer.session_store`` does not recursively import ``web.app``.
"""
