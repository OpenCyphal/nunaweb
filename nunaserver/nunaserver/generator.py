"""
Use the nunavut Python library to actually generate
the code.
"""
from pydsdl import read_namespace
from nunavut import build_namespace_tree
from nunavut.lang import LanguageContext
from nunavut.jinja import DSDLCodeGenerator
from nunaserver import settings
from nunaserver.tasks import celery
from nunaserver.utils.archive_utils import zipdir
import uuid
import zipfile
import tempfile
import logging
import time
import sys
from typing import List
from pathlib import Path

@celery.task(bind=True)
def generate_dsdl(self,
                  namespaces: List[str],
                  lang_target: str,
                  out_dir: str):
    """
    Generate (transpile) the DSDL code.
    """

    # Parse DSDL
    for c, namespace in enumerate(namespaces):
        namespace = str(namespace)
        self.update_state(state="PROGRESS",
                          meta={
                              "current": c+1,
                              "total": len(namespaces),
                              "status": "Generating " + namespace.split("/")[-1]
                          })

        extra_includes = namespaces
        extra_includes = list(map(str, extra_includes))

        compound_types = read_namespace(namespace,
                                        extra_includes,
                                        allow_unregulated_fixed_port_id=False)

        # Select target language
        lang_context = LanguageContext(lang_target)

        # Build namespace tree
        root_namespace = build_namespace_tree(compound_types,
                                              namespace,
                                              out_dir,
                                              lang_context)

        # Generate code
        generator = DSDLCodeGenerator(root_namespace)
        generator.generate_all()

    # Zip result
    # TODO: Is uuid4 secure enough? Might switch to something more secure
    # Technically should be secure (uses urandom) but ehhhhhh
    zipfile_name = f"nunavut_out-{uuid.uuid4()}.zip"
    zipf = zipfile.ZipFile(Path(settings.OUT_FILE_FOLDER) / zipfile_name,
                           "w", zipfile.ZIP_DEFLATED)
    zipdir(out_dir, zipf)
    zipf.close()

    return {
        "current": len(namespaces),
        "total": len(namespaces),
        "status": "Complete!",
        "result": f"{settings.OUT_SERVER_URL}/{zipfile_name}"
    }
