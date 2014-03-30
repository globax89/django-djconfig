#-*- coding: utf-8 -*-

from django import forms

import djconfig
from djconfig.models import Config


class ConfigForm(forms.Form):
    """
    Base class for every registered config form.

    :param initial: This parameter will be ignored. The cache is used to populate it.
    :type initial: dict.
    """
    def __init__(self, *args, **kwargs):
        super(ConfigForm, self).__init__(*args, **kwargs)

        self.initial = {field_name: getattr(djconfig.config, field_name)
                        for field_name in self.fields}

    def save(self):
        for field_name, value in self.cleaned_data.iteritems():
            count = Config.objects.filter(key=field_name).update(value=value)

            if not count:
                Config.objects.create(key=field_name, value=value)

        djconfig.load()