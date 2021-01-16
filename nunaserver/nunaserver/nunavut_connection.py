"""
Use the nunavut Python library to actually generate
the code.
"""
from pydsdl import read_namespace
from nunavut import build_namespace_tree
from nunavut.lang import LanguageContext
from nunavut.jinja import DSDLCodeGenerator
from typing import L

def generate_dsdl(namespaces: List, lang_context)
