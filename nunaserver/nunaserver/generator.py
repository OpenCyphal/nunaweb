"""
Use the nunavut Python library to actually generate
the code.
"""
import uuid
import tempfile
import zipfile
import logging
from typing import List
from pathlib import Path
from pydsdl import read_namespace
from pydsdl._error import InvalidDefinitionError
from nunavut import build_namespace_tree
from nunavut.lang import LanguageContext
from nunavut.jinja import DSDLCodeGenerator
from nunaserver import settings
from nunaserver.tasks import celery
from nunaserver.logging import init_logging
from nunaserver.utils.archive_utils import zipdir, fetch_remote_namespace

init_logging()

# pylint: disable=too-many-locals,too-many-arguments
@celery.task(bind=True)
def generate_dsdl(
    self,
    urls: List[str],
    arch_dir: str,
    target_lang: str,
    target_endian: str,
    flags: List[str],
):
    """
    Generate (transpile) the DSDL code.
    """

    # pylint: disable=invalid-name
    for c, url in enumerate(urls):
        self.update_state(
            state="PROGRESS",
            meta={
                "current": c + 1,
                "total": len(urls),
                "status": f"Fetching remote namespace {url}",
            },
        )
        fetch_remote_namespace(url, arch_dir)

    # Gather all the namespace directories
    inner = [d for d in Path(arch_dir).iterdir() if d.is_dir()]
    namespaces = []
    for path in inner:
        subnss = [
            d for d in path.iterdir() if d.is_dir() and not d.name.startswith(".")
        ]
        if len(subnss) > 0:
            namespaces.extend(
                [d for d in path.iterdir() if d.is_dir() and not d.name.startswith(".")]
            )
        else:
            namespaces.append(path)

    out_dir = Path(tempfile.mkdtemp(prefix="nunavut-out"))

    # Generate nnvg command
    # pylint: disable=invalid-name
    command = ""
    for c, ns_dir in enumerate(namespaces):
        if c > 0:
            command += "\n"
        command += "nnvg "
        command += f"--target-language {target_lang} "
        if target_endian != "any":
            command += f"--target-endianness {target_endian} "
        command += f"{' '.join(flags)}"
        command += f" dsdl_src{str(ns_dir).replace(str(arch_dir), '')}"
        for lookup_dir in namespaces:
            if lookup_dir != ns_dir:
                command += (
                    f" --lookup dsdl_src{str(lookup_dir).replace(str(arch_dir), '')}"
                )

    self.update_state(
        state="PROGRESS",
        meta={
            "current": 0,
            "total": len(namespaces),
            "status": "Preparing to generate namespaces",
            "command": command,
        },
    )

    # Parse DSDL
    # pylint: disable=invalid-name
    for c, namespace in enumerate(namespaces):
        namespace = str(namespace)
        self.update_state(
            state="PROGRESS",
            meta={
                "current": c + 1,
                "total": len(namespaces),
                "status": "Generating namespace: " + namespace.split("/")[-1],
                "command": command,
            },
        )

        extra_includes = namespaces
        extra_includes = list(map(str, extra_includes))

        try:
            compound_types = read_namespace(
                namespace, extra_includes, allow_unregulated_fixed_port_id=False
            )
        except InvalidDefinitionError as error:
            text = str(error).replace(arch_dir, "")
            raise RuntimeError(f"{text}") from error

        # Select target language and configure context
        language_options = {}
        language_options["target_endianness"] = target_endian
        language_options["omit_float_serialization_support"] = (
            "--omit-float-serialization-support" in flags
        )
        language_options["enable_serialization_asserts"] = (
            "--enable-serialization-asserts" in flags
        )
        lang_context = LanguageContext(
            target_lang,
            omit_serialization_support_for_target="--omit-serialization-support"
            in flags,
            language_options=language_options,
        )

        # Build namespace tree
        root_namespace = build_namespace_tree(
            compound_types, namespace, out_dir, lang_context
        )

        # Generate code
        generator = DSDLCodeGenerator(root_namespace)
        generator.generate_all()

    # Zip result
    zipfile_name = f"nunavut_out-{uuid.uuid4()}.zip"
    zipf = zipfile.ZipFile(
        Path(settings.OUT_FILE_FOLDER) / zipfile_name, "w", zipfile.ZIP_DEFLATED
    )
    zipdir(out_dir, zipf)
    zipf.close()

    return {
        "current": len(namespaces),
        "total": len(namespaces),
        "command": command,
        "status": "Complete!",
        "result": f"{settings.OUT_SERVER_URL}/{zipfile_name}",
    }
