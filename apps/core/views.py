from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views.generic import TemplateView

from apps.attendance.calendar import upcoming_sabbath
from apps.attendance.stats import sabbath_stats
from apps.attendance.streaks import missing_church
from apps.children.birthdays import upcoming_birthdays
from apps.children.groups import class_summary
from apps.core import dates
from apps.schools.models import AcademicYear


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "core/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = dates.local_today()
        sabbath = upcoming_sabbath(today)
        class_counts, ready, oldest = class_summary(today)
        context.update(
            {
                "today": today,
                "greeting": dates.greeting_for(dates.local_now()),
                "sabbath": sabbath,
                "stats": sabbath_stats(sabbath),
                "class_counts": class_counts,
                "ready_count": len(ready),
                "graduation_slug": oldest.slug if oldest else "",
                "missing": missing_church(today, minimum=2)[:5],
                "birthdays": upcoming_birthdays(today, within_days=30, limit=5),
                "academic_year": AcademicYear.objects.filter(is_current=True).first(),
            }
        )
        return context


class MoreView(LoginRequiredMixin, TemplateView):
    template_name = "core/more.html"


class ReportIndexView(LoginRequiredMixin, TemplateView):
    template_name = "reports/index.html"


def error_403(request, exception):
    return render(request, "403.html", status=403)


def error_404(request, exception):
    return render(request, "404.html", status=404)


def error_500(request):
    return render(request, "500.html", status=500)
