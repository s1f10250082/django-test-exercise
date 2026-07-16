from django.shortcuts import render, redirect
from django.http import Http404
from django.utils.timezone import make_aware
from django.utils.dateparse import parse_datetime
from todo.models import Task
# Create your views here.
def index(request):
    if request.method == 'POST':
        due_at_value = request.POST.get('due_at')
        task = Task(
            title=request.POST['title'],
            detail=request.POST.get('detail', ''),
            due_at=make_aware(parse_datetime(due_at_value)) if due_at_value else None,
        )
        task.save()
    if request.GET.get('order') == 'due':
        tasks = Task.objects.order_by('due_at')
    else:
        tasks = Task.objects.order_by('-posted_at')
    context = {
        'tasks': tasks
    }
    return render(request, 'todo/index.html', context)
def detail(request, task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        raise Http404("Task does not exist")
    context = {
        'task': task,
    }
    return render(request, 'todo/detail.html', context)
def edit(request, task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        raise Http404("Task does not exist")
    if request.method == 'POST':
        task.title = request.POST['title']
        task.detail = request.POST.get('detail', '')
        due_at = request.POST.get('due_at')
        task.due_at = make_aware(parse_datetime(due_at)) if due_at else None
        task.completed = 'completed' in request.POST
        task.save()
        return redirect('detail', task_id=task.id)
    context = {
        'task': task,
    }
    return render(request, 'todo/edit.html', context)
def delete(request, task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        raise Http404("Task does not exist")
    task.delete()
    return redirect(index)