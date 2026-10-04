from django import forms


def apply_widget_styles(form: forms.BaseForm) -> None:
    for field in form.fields.values():
        widget = field.widget
        if isinstance(widget, forms.CheckboxInput):
            widget.attrs["class"] = "size-5 accent-primary"
            continue
        existing = widget.attrs.get("class", "")
        widget.attrs["class"] = f"field-input {existing}".strip()
        widget.attrs.setdefault("autocomplete", "off")


class StyledModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        apply_widget_styles(self)
