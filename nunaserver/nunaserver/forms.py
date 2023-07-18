"""
Flask-WTF Forms for API form validation.
Used to parse and validate request data on API endpoints (e.g. /upload).
"""
import uuid


# pylint: disable=too-few-public-methods
class ValidationError(Exception):
    """
    Raised when form fails to validate.
    """

    def __init__(self, errors, *args, **kwargs):
        super().__init__(self, *args, **kwargs)
        self.errors = errors


class UploadForm:
    """
    Upload form for parsing namespace uploads.
    """

    def __init__(self, form, files):
        errors = {}

        self.archive_files = list(files.getlist("archive_files"))
        self.archive_urls = list(set(form.getlist("archive_urls")))

        if self.archive_files == [] and self.archive_urls == []:
            errors["archive_files"] = "No archive files or URLs for conversion."
            errors["archive_urls"] = "No archive files or URLs for conversion."

        if len(self.archive_urls) > 5:
            errors["archive_urls"] = "Too many archive URLs."

        try:
            self.target_lang = form["target_lang"]
        except KeyError:
            errors["target_lang"] = "target_lang attribute not found."

        try:
            self.target_endian = form["target_endian"]
        except KeyError:
            errors["target_endian"] = "target_endian attribute not found."

        try:
            self.doc_url = form["doc_url"]
        except KeyError:
            self.doc_url = f"nunavut-docs-{uuid.uuid4()}"

        self.flags = form.getlist("flags")

        if len(errors) > 0:
            raise ValidationError(errors)
