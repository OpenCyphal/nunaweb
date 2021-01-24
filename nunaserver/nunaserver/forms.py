"""
Flask-WTF Forms for API form validation.
Used to parse and validate request data on API endpoints (e.g. /upload).
"""

class ValidationError(Exception):
    def __init__(self, errors, *args, **kwargs):
        super().__init__(self, *args, **kwargs)
        self.errors = errors

class UploadForm:
    def __init__(self, form):
        errors = {}

        self.archive_files = list(form.getlist("archive_files"))
        self.archive_urls = list(set(form.getlist("archive_urls")))

        if self.archive_files == [] and self.archive_urls == []:
            errors["archive_files"] = "No archive files or URLs for conversion."
            errors["archive_urls"] = "No archive files or URLs for conversion."

        try:
            self.target_lang = form["target_lang"]
        except KeyError:
            errors["target_lang"] = "target_lang attribute not found."

        try:
            self.target_endian = form["target_endian"]
        except KeyError:
            errors["target_endian"] = "target_endian attribute not found."

        self.flags = form.getlist("flags")

        if len(errors) > 0:
            raise ValidationError(errors)
