"""
Use the nunavut Python library to actually generate
the code.
"""
import uuid
import os
import tempfile
import zipfile
import minio
import typing
from typing import List
from pathlib import Path
from pydsdl import read_namespace
from pydsdl._error import InvalidDefinitionError
from nunavut import build_namespace_tree
from nunavut import DSDLCodeGenerator, SupportGenerator, AbstractGenerator, Namespace
from nunaserver import settings
from nunaserver.tasks import celery
from nunaserver.logging import init_logging
from nunaserver.minio_connection import storage
from nunaserver.utils.archive_utils import (
    zipdir,
    fetch_remote_namespace,
    unzip_to_directory,
)
from nunavut.lang import (
    Language,
    LanguageContextBuilder,
)

init_logging()

def create_default_generators(ns: Namespace, **kwargs: typing.Any) -> tuple[AbstractGenerator, AbstractGenerator]:
    return DSDLCodeGenerator(ns, **kwargs), SupportGenerator(ns, **kwargs)

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
        subnss = [d for d in path.iterdir() if d.is_dir() and not d.name.startswith(".")]
        if len(subnss) > 0:
            namespaces.extend([d for d in path.iterdir() if d.is_dir() and not d.name.startswith(".")])
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
                command += f" --lookup dsdl_src{str(lookup_dir).replace(str(arch_dir), '')}"

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
            compound_types = read_namespace(namespace, extra_includes, allow_unregulated_fixed_port_id=False)
        except InvalidDefinitionError as error:
            text = str(error).replace(str(arch_dir), "")
            raise RuntimeError(f"{text}") from error

        # Select target language and configure context
        language_options = {
            "target_endianness": target_endian,
            "omit_float_serialization_support": ("--omit-float-serialization-support" in flags),
            "enable_serialization_asserts": ("--enable-serialization-asserts" in flags),
            "enable_override_variable_array_capacity": ("--enable-override-variable-array-capacity" in flags),
        }

        language_context = (
            LanguageContextBuilder(include_experimental_languages=True)
            .set_target_language(target_lang)
            .set_target_language_configuration_override(Language.WKCV_LANGUAGE_OPTIONS, language_options)
            .create()
        )

        root_namespace = build_namespace_tree(compound_types, namespace, str(out_dir), language_context)

        # Generate code
        generator, support_generator = create_default_generators(root_namespace)
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
                    content_type="text/html",
                )
        return {
            "current": len(namespaces),
            "total": len(namespaces),
            "command": command,
            "type": "htmldoc",
            "status": "Complete!",
            "result": [f"{settings.MINIO_DOCS}/{doc_url}/{str(ns).split('/')[-1]}/index.html" for ns in namespaces],
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
        )

        return {
            "current": len(namespaces),
            "total": len(namespaces),
            "command": command,
            "type": "generic",
            "status": "Complete!",
            "result": f"{settings.MINIO_RESULTS}/{zipfile_name}",
        }
