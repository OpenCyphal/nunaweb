"""
Use the nunavut Python library to actually generate
the code.
"""
import uuid
import os
import tempfile
import zipfile
import logging
from typing import List
from pathlib import Path
from pydsdl import read_namespace
from pydsdl._error import InvalidDefinitionError
import nunavut
import minio
from nunavut import build_namespace_tree
from nunavut.generators import create_generators
from nunavut.lang import LanguageContext
from nunavut.jinja import DSDLCodeGenerator
from nunaserver import settings
from nunaserver.tasks import celery
from nunaserver.logging import init_logging
from nunaserver.minio_connection import storage
from nunaserver.utils.archive_utils import (
    zipdir,
    fetch_remote_namespace,
    unzip_to_directory,
)

init_logging()

# pylint: disable=too-many-locals,too-many-arguments
@celery.task(bind=True)
def generate_dsdl(
    self,
    build_uuid: str,
    urls: List[str],
    target_lang: str,
    target_endian: str,
    flags: List[str],
    doc_url: str,
):
    """
    Generate (transpile) the DSDL code.
    """

    # Create working directory
    arch_dir = Path(tempfile.mkdtemp(prefix="pyuavcan-cli-dsdl"))

    # Get uploaded files from minio and unzip
    objects = storage.list_objects(f"{build_uuid}", prefix="uploads/", recursive=True)
    for obj in objects:
        # Create temp file for zip archive
        _, file_path = tempfile.mkstemp(".zip", "dsdl")

        # Save and unzip
        data = storage.get_object(obj.bucket_name, obj.object_name.encode("utf-8"))
        with open(file_path, "wb") as file_data:
            for d in data.stream(32 * 1024):
                file_data.write(d)

        unzip_to_directory(file_path, arch_dir)

        # Delete zip file
        os.unlink(file_path)

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
            text = str(error).replace(str(arch_dir), "")
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
        generator, support_generator = create_generators(root_namespace)
        generator.generate_all()
        support_generator.generate_all()

    if target_lang == "html":
        # Upload generated files
        for file in out_dir.glob("**/*"):
            if file.is_file():
                rel_path = doc_url / file.relative_to(out_dir)
                try:
                    if storage.stat_object("docs", f"{rel_path}"):
                        raise RuntimeError("Specified doc URL is already taken")
                except minio.error.S3Error:
                    pass

                storage.fput_object(
                    "docs",
                    str(rel_path),
                    str(file.absolute()),
                    os.stat(file.absolute()).st_size,
                )
        return {
            "current": len(namespaces),
            "total": len(namespaces),
            "command": command,
            "type": "htmldoc",
            "status": "Complete!",
            "result": [
                f"{settings.MINIO_DOCS}/{doc_url}/{str(ns).split('/')[-1]}/index.html" for ns in namespaces
            ],
        }
    else:
        # Zip result
        zipfile_name = f"nunavut_out-{uuid.uuid4()}.zip"
        zipf = zipfile.ZipFile(f"/tmp/{zipfile_name}", "w", zipfile.ZIP_DEFLATED)
        zipdir(out_dir, zipf)
        zipf.close()

        # Upload result
        storage.fput_object(
            "results",
            zipfile_name,
            f"/tmp/{zipfile_name}",
            os.stat(f"/tmp/{zipfile_name}").st_size,
        )

        return {
            "current": len(namespaces),
            "total": len(namespaces),
            "command": command,
            "type": "generic",
            "status": "Complete!",
            "result": f"{settings.MINIO_RESULTS}/{zipfile_name}",
        }
