from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User

    # 1. Dashboard Columns
    list_display = ("username", "colored_role", "status_indicator", "is_staff")
    list_filter = ("role", "is_active")
    search_fields = ("username",)
    ordering = ("username",)

    # 2. Modern UI Logic (Badges)
    def colored_role(self, obj):
        colors = {
            'Admin': '#dc2626',
            'Teacher': '#2563eb',
            'Student': '#16a34a',
        }
        bg_color = colors.get(obj.role, '#6b7280')
        return format_html(
            '<span style="background:{}; color:white; padding:4px 12px; border-radius:50px; font-size:10px; font-weight:bold; text-transform:uppercase;">{}</span>',
            bg_color, obj.role
        )
    colored_role.short_description = "User Role"

    def status_indicator(self, obj):
        color = "#10b981" if obj.is_active else "#ef4444"
        return format_html(
            '<span style="display:inline-block; width:8px; height:8px; background:{}; border-radius:50%; margin-right:5px;"></span> {}',
            color, "Active" if obj.is_active else "Inactive"
        )
    status_indicator.short_description = "Status"

    # 3. Modern Styling (Combined CSS)
    # This injects CSS directly without needing a separate .css file
    class Media:
        js = []
        css = {
            'all': [
                "data:text/css, " + 
                ".module { border-radius: 12px !important; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1) !important; border: none !important; }" +
                "thead th { background: #f8fafc !important; color: #64748b !important; text-transform: uppercase !important; font-size: 11px !important; }" +
                "input[type=submit], .button { background: #2563eb !important; border-radius: 8px !important; padding: 10px 20px !important; border: none !important; }" +
                "input, select, textarea { border-radius: 8px !important; border: 1px solid #e2e8f0 !important; padding: 5px !important; }"
            ]
        }

    # 4. Organizing Fields
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Identity", {"fields": ("role",)}),
        ("Permissions", {
            "classes": ("collapse",), 
            "fields": ("is_active", "is_staff", "is_superuser")
        }),
        ("Important Dates", {"fields": ("last_login",)}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "password1", "password2", "role", "is_active", "is_staff"),
        }),
    )