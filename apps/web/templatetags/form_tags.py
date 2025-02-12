from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def render_form_fields(form):
    rendered_values = [render_field(form[field]) for field in form.fields]
    return mark_safe("".join(rendered_values))


@register.simple_tag
def render_field(form_field, **attrs):
    render_function = {
        "select": render_select_input,
        "checkbox": render_checkbox_input,
    }.get(form_field.widget_type, render_text_input)
    return render_function(form_field, **attrs)


@register.simple_tag
def render_text_input(form_field, **attrs):
    TEXT_INPUT_TEMPLATE = """<div class="field" {% include "django/forms/attrs.html" %}>
      <label class="label">{{ form_field.label }}</label>
      <div class="control">
        {{ form_field }}
      </div>
      <div class="help">{{ form_field.help_text|safe }}</div>
      {{ form_field.errors }}
    </div>
    """
    return _render_field(TEXT_INPUT_TEMPLATE, form_field, **attrs)


@register.simple_tag
def render_select_input(form_field, **attrs):
    SELECT_INPUT_TEMPLATE = """<div class="field" {% include "django/forms/attrs.html" %}>
      <label class="label">{{ form_field.label }}</label>
      <div class="control">
        <div class="select">
          {{ form_field }}
        </div>
      </div>
      <div class="help">{{ form_field.help_text|safe }}</div>
      {{ form_field.errors }}
    </div>
    """
    return _render_field(SELECT_INPUT_TEMPLATE, form_field, **attrs)


@register.simple_tag
def render_checkbox_input(form_field, **attrs):
    CHECKBOX_INPUT_TEMPLATE = """<div class="field" {% include "django/forms/attrs.html" %}>
      <div class="control">
        <label class="checkbox">
          {{ form_field }}
          {{ form_field.label }}
        </label>
      </div>
      <div class="help">{{ form_field.help_text|safe }}</div>
      {{ form_field.errors }}
    </div>
    """
    return _render_field(CHECKBOX_INPUT_TEMPLATE, form_field, **attrs)


def _render_field(template_text, form_field, **attrs):
    if not form_field.is_hidden:
        template_object = template.Template(template_text)
    else:
        template_object = template.Template("{{ form_field }}")
    attrs = _transform_x_attrs(attrs)
    context = template.Context({"form_field": form_field, "attrs": attrs})
    return template_object.render(context)


def _transform_x_attrs(attrs):
    """Assumes that attributes which start with 'x' are AlpineJS attributes
    and converts them by adding a dash after the x: `xbind` -> `x-bind`.

    It will also convert a double underscore into a colon: `xbind__placeholder` -> `x-bind:placeholder`.

    There is no support for '.' modifiers.
    """

    def _make_x_attr(key):
        if key.startswith("x"):
            key = key[1:].replace("__", ":")
            return f"x-{key}"
        return key

    return {_make_x_attr(key): value for key, value in attrs.items()}
