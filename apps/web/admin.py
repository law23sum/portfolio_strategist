from django.contrib import admin

from .models import Equation, EquationCategory, EquationVariable


@admin.register(EquationCategory)
class EquationCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "order", "is_premium", "equation_count"]
    list_filter = ["is_premium"]
    search_fields = ["name", "description"]
    prepopulated_fields = {"slug": ("name",)}

    def equation_count(self, obj):
        return obj.equations.count()

    equation_count.short_description = "Equations"


@admin.register(Equation)
class EquationAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "slug", "is_featured", "is_premium", "supports_graph"]
    list_filter = ["category", "is_featured", "is_premium", "supports_graph", "implementation_type"]
    search_fields = ["name", "description", "formula_text"]
    prepopulated_fields = {"slug": ("name",)}
    filter_horizontal = []
    readonly_fields = ["created_at", "updated_at"]


@admin.register(EquationVariable)
class EquationVariableAdmin(admin.ModelAdmin):
    list_display = ["name", "symbol", "equation", "variable_type", "is_required", "order"]
    list_filter = ["variable_type", "is_required", "equation__category"]
    search_fields = ["name", "symbol", "description", "equation__name"]
    ordering = ["equation", "order", "name"]
