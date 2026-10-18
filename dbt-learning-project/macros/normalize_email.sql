{% macro normalize_email(expression) %}
    lower(trim({{ expression }}))
{% endmacro %}
