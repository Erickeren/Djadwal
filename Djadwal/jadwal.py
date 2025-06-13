### Struktur awal proyek Django
# 1. models.py
from django.db import models

class Staff(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class ShiftSchedule(models.Model):
    SHIFT_CHOICES = (
        ('Pagi', 'Pagi (08:00 - 20:00)'),
        ('Malam', 'Malam (20:00 - 08:00)'),
    )
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    date = models.DateField()
    shift = models.CharField(max_length=10, choices=SHIFT_CHOICES)

class DayOff(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    date = models.DateField()


# 2. forms.py
from django import forms
from .models import Staff

class StaffForm(forms.Form):
    names = forms.CharField(widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Masukkan 4 nama, pisahkan dengan baris'}))


# 3. views.py
import calendar
from datetime import date, timedelta
from django.shortcuts import render, redirect
from .models import Staff, ShiftSchedule, DayOff
from .forms import StaffForm


def generate_schedule(request):
    if request.method == 'POST':
        form = StaffForm(request.POST)
        if form.is_valid():
            names = form.cleaned_data['names'].split('\n')
            if len(names) != 4:
                return render(request, 'schedule_form.html', {'form': form, 'error': 'Masukkan tepat 4 nama'})

            Staff.objects.all().delete()
            ShiftSchedule.objects.all().delete()
            DayOff.objects.all().delete()

            staffs = [Staff.objects.create(name=name.strip()) for name in names]

            today = date.today().replace(day=1)
            last_day = calendar.monthrange(today.year, today.month)[1]
            day_pointer = today

            rotation = [
                (staffs[0], staffs[1]),
                (staffs[2], staffs[3]),
            ]
            shift_cycle = ['Pagi', 'Malam']
            index = 0

            while day_pointer.day <= last_day:
                working, off = rotation[index % 2], rotation[(index + 1) % 2]
                for i in range(4):
                    if day_pointer.day > last_day:
                        break
                    for shift in shift_cycle:
                        for staff in working:
                            ShiftSchedule.objects.create(staff=staff, date=day_pointer, shift=shift)
                    for staff in off:
                        DayOff.objects.create(staff=staff, date=day_pointer)
                    day_pointer += timedelta(days=1)
                index += 1

            return redirect('schedule_result')
    else:
        form = StaffForm()
    return render(request, 'schedule_form.html', {'form': form})


def schedule_result(request):
    shifts = ShiftSchedule.objects.all().order_by('date')
    days_off = DayOff.objects.all().order_by('date')
    return render(request, 'schedule_result.html', {'shifts': shifts, 'days_off': days_off})

