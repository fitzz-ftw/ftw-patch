:orphan:

{{ fullname | escape | underline}}

.. include-if-exists:: ../api_inc/modules/{{fullname}}_{{module_inc}}.rst.inc
    :parser: rst

{% if inheritence_diagram(fullname) %}

.. container:: class-tree-diagram
   
   .. autoclasstree:: {{fullname}}
      :name: {{ objname }}
      :strict:
      :title: {{ objname }}
      :caption: Inheritage diagramm for {{ objname }} 
      :align: center
      :config: {"width": "300px", "height": "300px"}

{% endif %}

.. automodule:: {{ fullname }}
   :no-members:
   :no-undoc-members:

.. container:: custom-api-style api-module

    .. currentmodule:: {{ fullname }}

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

    .. include-if-exists:: ../api_inc/functions/{{fullname}}.{{item}}_{{function_inc}}.rst.inc
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

    .. include-if-exists:: ../api_inc/attributes/{{fullname}}.{{item}}_{{attributes_inc}}.rst.inc
        :parser: rst

    .. autodata:: {{ item }}
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
    .. include-if-exists:: ../api_inc/exceptions/{{fullname}}.{{item}}_{{exception_inc}}.rst.inc

    .. autoexception:: {{ item }}
        :show-inheritance:
    {%- endfor %}

    {% endif %}
    {%- endblock %}
