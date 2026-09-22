import api.app

app = api.app.create_app()
paths = set()
for r in app.routes:
    if hasattr(r, "path"):
        paths.add(r.path)
    elif r.__class__.__name__ == "_IncludedRouter":
        prefix = getattr(r.include_context, "prefix", "")
        # wait, include_context or just original_router.routes?
        for rr in getattr(r.original_router, "routes", []):
            paths.add(prefix + getattr(rr, "path", ""))
print(paths)
