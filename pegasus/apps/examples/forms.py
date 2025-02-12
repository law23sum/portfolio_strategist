from django import forms
from django.forms import DateInput
from django.utils.translation import gettext


class ExampleForm(forms.Form):
    COLORS = (
        ("red", "Red"),
        ("blue", "Blue"),
        ("green", "Green"),
        ("yellow", "Yellow"),
    )
    name = forms.CharField(help_text="This is a character field. It is required.")
    email = forms.EmailField(help_text="This is an email field. It is required.")
    placeholder = forms.CharField(
        help_text="This is a character field with some placeholder text.",
        widget=forms.TextInput(attrs={"placeholder": "This is the placeholder text."}),
    )
    date = forms.DateField(help_text="This is a date field. It is required.", widget=DateInput(attrs={"type": "date"}))

    invisible = forms.CharField(
        help_text="This is an Invisible field.", widget=forms.HiddenInput(), initial="something"
    )
    website = forms.URLField(help_text="This is a URL field. It is required.", assume_scheme="https")
    checkbox = forms.BooleanField(help_text="This is a checkbox / boolean field", required=False)
    favorite_color = forms.ChoiceField(help_text="This is a choice field", choices=COLORS)
    comments = forms.CharField(
        help_text="This is a longer character field. It is optional", required=False, widget=forms.Textarea()
    )
    centered_input = forms.CharField(
        help_text="This is an optional input centered text.",
        required=False,
        widget=forms.TextInput(
            attrs={"class": "pg-text-centered"},
        ),
    )
    centered_text = forms.CharField(
        help_text="This is an optional text area with centered text.",
        required=False,
        widget=forms.Textarea(
            attrs={"class": "pg-text-centered"},
        ),
    )


class ExampleFormAlpine(forms.Form):
    YES_NO_OTHER = (
        ("yes", gettext("Yes")),
        ("no", gettext("No")),
        ("other", gettext("Other")),
    )
    STYLES = (
        ("regular", gettext("Normal")),
        ("success", gettext("Success")),
        ("danger", gettext("Danger")),
    )
    like_django = forms.ChoiceField(
        label=gettext("Do you like Django?"),
        help_text=gettext("Try choosing 'other' to see unhiding a form field based on a value."),
        choices=YES_NO_OTHER,
        widget=forms.Select(attrs={"x-model": "likeDjango"}),
    )
    like_django_other = forms.CharField(label=gettext("Please specify more details about your answer."))
    styled_options = forms.ChoiceField(
        label=gettext("Styled Options"),
        help_text=gettext("Try picking an option to see how you can style a component based on its value."),
        choices=STYLES,
        widget=forms.Select(attrs={"x-model": "styleValue"}),
    )
