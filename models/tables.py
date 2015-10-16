# Tables to be used by the server.

# Table for Wikipedia pages
db.define_table('wikipages',
                Field('pageid', unique=True),  # Page ID same as Wikipedia
                Field('title'),  # Page title from Wikipedia
                Field('lang'),  # Page language from Wikipedia
                Field('last_known_rev'),  # Last known revision of the page to the system
                format = "%(pageid)s"
                )

# Table for Wikipedia users
db.define_table('wiki_users',
                Field('username', unique=True),  # Username same as Wikipedia
                Field('userid'),  # UserID from Wikipedia
                format = "%(username)s"
                )

# Table for different analysis
db.define_table('analysis_type',
                Field('name', unique=True),  # Name of the analysis, e.g., reputation, or authorship.
                Field('author'),  # Author of analysis
                Field('description', 'text'),  # Description of analysis
                Field('reference_location'),  # Reference path for algorithm code or URL call
                )

# Table to store page-analysis entries.
db.define_table('page_analysis',
                Field('analysis_type','reference analysis_type'),  # Type of analysis, e.g., reputation, or authorship.
                Field('pageid', 'reference wikipages'),  # Unique for each type of analysis.
                Field('last_annotated', 'integer', default=0),  # Last annotated revision for the analysis-page pair
                Field('worker_id'),
                # Each worker generates a random id, used to sign these. If blank = nobody working on this.
                Field('work_start_date', 'datetime'),  # If too old, blank both this and worker id.
                Field('priority', 'double'),  # Priority of analysis.
                Field('status')  # If active, then analysis needs to be done, else no
                )


# Table to store user-contribution-analysis entries.
db.define_table('user_analysis',
                Field('analysis_type','reference analysis_type'),  # Type of analysis, e.g., reputation, or authorship.
                Field('user', 'reference wiki_users'),  # Unique for each type of analysis.
                Field('last_recorded', 'integer', default=0),  # Last recorded revision for the analysis-user pair
                Field('worker_id'),
                # Each worker generates a random id, used to sign these. If blank = nobody working on this.
                Field('work_start_date', 'datetime'),  # If too old, blank both this and worker id.
                Field('priority', 'double'),  # Priority of analysis.
                Field('status')  # If active, then analysis needs to be done, else no
                )


# For first run

# Create an entry for trust in analysis_type

#db.analysis_type.update_or_insert(name='trust',author='Luca deAlfaro')