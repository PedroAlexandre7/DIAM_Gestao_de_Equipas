from datetime import datetime, timedelta
from calendar import HTMLCalendar

from django.template import Template, Context
from django.urls import reverse

from .models import Evento


class Calendar(HTMLCalendar):
    def __init__(self, year=None, month=None):
        self.year = year
        self.month = month
        super(Calendar, self).__init__()

    # formats a day as a td
    # filter events by day
    def formatday(self, day, events):
        events_per_day = events.filter(data_evento__day=day)
        d = ''
        for event in events_per_day:
            event_url = reverse('gestaoequipas:modificarevento', args=[event.id])
            d += f'<li><a href="{event_url}">{event.tipo_evento}</a></li>'

        if day != 0:
            return f"<td><span class='date'>{day}</span><ul> {d} </ul></td>"
        return '<td></td>'

    # formats a week as a tr
    def formatweek(self, theweek, events):
        week = ''
        for d, weekday in theweek:
            week += self.formatday(d, events)
        return f'<tr> {week} </tr>'

    def get_previous_month(self):
        previous_month = self.month - 1
        previous_year = self.year
        if previous_month == 0:
            previous_month = 12
            previous_year -= 1
        return previous_year, previous_month

    def get_next_month(self):
        next_month = self.month + 1
        next_year = self.year
        if next_month == 13:
            next_month = 1
            next_year += 1
        return next_year, next_month

    # formats a month as a table
    # filter events by year and month
    def formatmonth(self, withyear=True):
        events = Evento.objects.filter(data_evento__year=self.year, data_evento__month=self.month)

        cal = f'<table border="0" cellpadding="0" cellspacing="0" class="calendar">\n'
        cal += f'{self.formatmonthname(self.year, self.month, withyear=withyear)}\n'
        cal += f'{self.formatweekheader()}\n'
        for week in self.monthdays2calendar(self.year, self.month):
            cal += f'{self.formatweek(week, events)}\n'
        cal += '</table>\n'
        return cal