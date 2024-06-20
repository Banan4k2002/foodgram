from django.utils.translation import gettext_lazy


def shortlink_patch():
    """Заменяет импорт устаревшей функции."""
    import django

    if django.VERSION >= (4, 0):
        import django.utils.translation

        django.utils.translation.ugettext_lazy = gettext_lazy
