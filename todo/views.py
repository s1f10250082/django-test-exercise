from django.shortcuts import render, redirect
from django.http import Http404
from django.utils.timezone import make_aware
from django.utils.dateparse import parse_datetime
from todo.models import Task
# Create your views here.
def index(request):
    if request.method == 'POST':
        due_at = request.POST.get('due_at')
        task = Task(
            title=request.POST['title'],
            completed='completed' in request.POST,
            favorite='favorite' in request.POST,
            due_at=make_aware(parse_datetime(due_at)) if due_at else None,
            photo=request.FILES.get('photo'),
        )
        task.save()
    order = request.GET.get('order')
    if order == 'favorite':
        tasks = Task.objects.filter(favorite=True).order_by('-posted_at')
    elif order == 'due':
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
        due_at = request.POST.get('due_at')
        task.due_at = make_aware(parse_datetime(due_at)) if due_at else None
        task.completed = 'completed' in request.POST
        task.favorite = 'favorite' in request.POST
        photo = request.FILES.get('photo')
        if photo:
            if task.photo:
                task.photo.delete(save=False)
            task.photo = photo
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
    if task.photo:
        task.photo.delete(save=False)
    task.delete()
    return redirect(index)