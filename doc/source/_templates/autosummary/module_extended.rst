:orphan:

{{ fullname | escape | underline}}

.. include:: ../api_inc/modules/{{fullname}}_{{module_inc}}.rst.inc
    :parser: rst

.. container:: custom-api-style api-module

    .. module:: {{ fullname }}

    {%- block classes %}
    {%- if classes %}
    .. rubric:: {{ _('Classes') }}

    .. autosummary::
        :toctree:
        :recursive:
        :template: class_extended.rst

        {% for item in classes %}
        {{ item }}
        {%- endfor %}
        {% endif %}
        {%- endblock %}

    {%- block functions %}
    {%- if functions %}
    .. rubric:: {{ _('Functions') }}

    .. autosummary::

        {% for item in functions %}
            {{ item }}
        {%- endfor %}
    {% for item in functions %}

    .. include:: ../api_inc/functions/{{fullname}}.{{item}}_{{function_inc}}.rst.inc
        :parser: rst

    .. autofunction:: {{ item }}

    {%- endfor %}
    {% endif %}
    {%- endblock %}

    {% block attributes %}
    {%- if attributes %}
    .. rubric:: {{ _('Module Attributes') }}

    .. autosummary::
    {% for item in attributes %}
        {{ item }}
    {%- endfor %}

    {% for item in attributes %}

    .. include:: ../api_inc/attributes/{{fullname}}.{{item}}_{{attributes_inc}}.rst.inc
        :parser: rst

    .. autoattribute:: {{ item }}
    {%- endfor %}

    {% endif %}
    {%- endblock %}

    {%- block exceptions %}
    {%- if exceptions %}
    .. rubric:: {{ _('Exceptions') }}

    .. autosummary::
    {% for item in exceptions %}
        {{ item }}
    {%- endfor %}
    {% for item in exceptions %}
    .. include:: ../api_inc/exceptions/{{fullname}}.{{item}}_{{exception_inc}}.rst.inc

    .. autoexception:: {{ item }}
        :show-inheritance:
    {%- endfor %}

    {% endif %}
    {%- endblock %}
