# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.apps import apps
from django.conf import settings

from . import registry
from .settings import DJCONFIG_CONFIG_MODEL

CONFIG_MODEL = getattr(settings, 'DJCONFIG_CONFIG_MODEL', DJCONFIG_CONFIG_MODEL)


class Config(object):

    def __init__(self):
        self._cache = {}
        self._is_loaded = False

    def __getattr__(self, key):
        self._lazy_load()

        try:
            return self._cache[key]
        except KeyError:
            raise AttributeError('Attribute "%s" not found in config.' % key)

    def _set(self, key, value):
        self._cache[key] = value

    def _set_many(self, items):
        self._cache.update({
            key: value
            for key, value in items.items()
        })

    def _reload(self):
        """
        Gets every registered form's field value.
        If a field name is found in the db, it will load it from there.
        Otherwise, the initial value from the field form is used.
        """
        ConfigModel = apps.get_model(CONFIG_MODEL)
        cache_items = {}
        data = dict(ConfigModel.objects
                    .all()
                    .values_list('key', 'value'))

        for form_class in registry._registered_forms:
            form = form_class(data=data, pre_load_config=False)
            form.is_valid()

            initial = {
                field_name: field.initial
                for field_name, field in form.fields.items()
            }
            cache_items.update(initial)

            cleaned_data = {
                field_name: value
                for field_name, value in form.cleaned_data.items()
                if field_name in data
            }
            cache_items.update(cleaned_data)

        cache_items['_updated_at'] = data.get('_updated_at')
        self._set_many(cache_items)

    def _reset(self):
        self._is_loaded = False

    def _lazy_load(self):
        if self._is_loaded:
            return

        self._reload()
        self._is_loaded = True


config = Config()
