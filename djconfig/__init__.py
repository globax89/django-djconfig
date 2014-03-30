#-*- coding: utf-8 -*-

from django.core.cache import get_cache
from django.db import connection
from django.conf import settings

from djconfig.forms import ConfigForm
from djconfig.settings import DJC_BACKEND
from djconfig.config import Config
from djconfig.models import Config as ConfigModel

__all__ = ['config', 'register']

BACKEND = getattr(settings, 'DJC_BACKEND', DJC_BACKEND)

config = Config()
_registered_forms = set()


def register(form_class):
    """
    Register config forms

    :param form_class: The form to be registered.
    :type form_class: ConfigForm.
    """
    global _registered_forms

    assert issubclass(form_class, ConfigForm), \
        "The form does not inherit from ConfigForm"

    _registered_forms.add(form_class)


def load():
    """
    Loads every registered form into the cache.
    If a field name is found in the db, it will load it from there.
    Otherwise, the initial value from the field form is used.
    """
    global _registered_forms

    cache_values = {}
    data = dict(ConfigModel.objects.all().values_list('key', 'value'))

    for form_class in _registered_forms:
        form = form_class(data=data)
        form.full_clean()

        initial = {field_name: field.initial
                   for field_name, field in form.fields.iteritems()}
        cache_values.update(initial)

        cleaned_data = {field_name: value
                        for field_name, value in form.cleaned_data.iteritems()
                        if field_name in data}
        cache_values.update(cleaned_data)

    cache = get_cache(BACKEND)
    cache.set_many(cache_values)


def _load():
    """
    Avoids loading if the Config table does not exists.
    ie: when running syncdb for the first time.
    """
    if not ConfigModel._meta.db_table in connection.introspection.table_names():
        return

    load()

_load()