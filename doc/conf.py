# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'voctomix'
copyright = '2014-2026, c3voc'
author = 'fightling, MaZderMind, Florob, Kunsi, derpeter, sophieschi'
release = '2.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['sphinx_wagtail_theme']

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_wagtail_theme'
html_static_path = ['_static']

html_theme_options = {
    'project_name': 'voctomix',
    'logo': 'voctocat.svg',
    'logo_alt': 'voctomix',
    'logo_height': 59,
    'logo_width': 59,
    'github_url': 'https://github.com/voc/voctomix/blob/main/doc/',
    'footer_links': ', '.join([
        'voctomix on GitHub|https://github.com/voc/voctomix',
        'c3voc|https://c3voc.de/',
        'VOC on GitHub|https://github.com/voc',
        'c3voc config management|https://forgejo.c3voc.de/voc/cm',
    ]),
}
