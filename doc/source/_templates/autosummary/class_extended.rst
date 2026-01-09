:orphan:

{{ fullname | escape | underline}}

.. container:: api-nav-links

   **from** {%- set path_parts = module.split('.') -%}
   {%- set current_path = [] -%}
   {%- for part in path_parts -%}
     {%- set _ = current_path.append(part) -%}
     :mod:`{{ part }} <{{ current_path | join('.') }}>`
     {%- if not loop.last %}.\ {% endif -%}
   {%- endfor %}
   **import** {{ objname }}

.. include:: ../api_inc/classes/{{fullname}}_{{class_inc}}.rst.inc
    :parser: rst

.. container:: custom-api-style api-class

      {% set inherited = False %}
      {% set classtoc = False %}

   .. currentmodule:: {{ module }}

   .. autoclass:: {{ objname }}
      {%- if (class_show_inheritance == True 
         or class_show_inheritance and objname is in(class_show_inheritance))
         and not (excl_class_show_inheritance and objname is in(excl_class_show_inheritance)) %}
      {%- set inherited = True %}
      :show-inheritance:
      :inherited-members:
      {%- endif %}
      {%- if inherited and (autoclass_toc == True 
         or autoclass_toc and objname is in(autoclass_toc)) %}
      {%- set classtoc = True %}
      :members:

      .. autoclasstoc::
      {%- endif %}


   {%- if not classtoc %}

      {% block methods %}

      {% if methods %}
      .. rubric:: {{ _('Methods') }}

      .. autosummary::
      {% for item in methods %}
         {%- if classtoc %}
         ~{{ name }}.{{ item }}
         {%- else%}
         ~{{ name }}.{{ item }}
         {%- endif%}
      {%- endfor %}
      {% endif %}
      {% endblock methods %}

      {% block attributes %}
      {% if attributes %}
      .. rubric:: {{ _('Attributes') }}

      .. autosummary::
      {% for item in attributes %}
         ~{{ name }}.{{ item }}
      {%- endfor %}
      {% endif %}
      {% endblock attributes %}

   {% endif %}

   