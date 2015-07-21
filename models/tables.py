# Tables to be used by the server.

db.define_table('wikipages',
                Field('pageid', unique=True),
                Field('title'),
                Field('lang'),
                Field('last_known_rev'),
                )

db.define_table('analysis',
                Field('analysis_type'),  # Type of analysis, e.g., reputation, or authorship.
                Field('pageid'),  # Unique for each type of analysis.
                Field('last_annotated'),
                Field('worker_id'),  # Each worker generates a random id, used to sign these. If blank = nobody working on this.
                Field('work_start_date', 'datetime'),  # If too old, blank both this and worker id.
                Field('priority', 'double'),
                Field('status')  # If active, then analysis needs to be done, else no
                )
