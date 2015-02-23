from django.shortcuts import render, redirect
from models import Notebook, Hit
from django import forms
from django.http import HttpResponseRedirect, HttpResponse
from django.template import Context, Template

from utils import insert_notebook
from django.utils import timezone


# global variables
nb_per_page = 30


# forms
class NotebookForm(forms.Form):
    URL = forms.URLField(label='paste the URL of the notebook', required=True)


# Create your views here.

def index(request):
    return sort(request, 'date')


def sort(request, sort_by):
    context = {'sort_by': sort_by}
    if sort_by == 'views':
        nbs = Notebook.objects.order_by('-hits_total')[0:nb_per_page]
        context['views_active'] = 'active'
    elif sort_by == 'date':
        tmp = Notebook.objects.order_by('-accessed_date')[0:nb_per_page]
        dates = list(set(tmp.values_list('accessed_date', flat=True)))
        dates.sort()
        dates = dates[::-1]
        nbs = []
        for d in dates:
            tmp_nbs = []
            for o in tmp:
                if o.accessed_date == d:
                    tmp_nbs.append(o)
            nbs.append([d, tmp_nbs])
        context['date_active'] = 'active'
    elif sort_by == 'random':
        nbs = Notebook.objects.order_by('?')[0:nb_per_page]
        context['random_active'] = 'active'
    else:
        raise NotImplementedError
    context['nbs'] = nbs
    return render(request, 'web/index.html', context)


def page(request, sort_by, obj_id):
    i = int(obj_id) - 1
    more_pages = False
    if sort_by == 'views':
        nbs = Notebook.objects.order_by('-hits_total')[nb_per_page * i:nb_per_page * (i+1)]
        more_pages = (len(nbs) == nb_per_page)
    elif sort_by == 'date':
        tmp = Notebook.objects.order_by('-accessed_date')[nb_per_page * i:nb_per_page * (i+1)]
        dates = list(set(tmp.values_list('accessed_date', flat=True)))
        dates.sort()
        dates = dates[::-1]
        nbs = []
        for d in dates:
            tmp_nbs = []
            for o in tmp:
                if o.accessed_date == d:
                    tmp_nbs.append(o)
            nbs.append([d, tmp_nbs])
        more_pages = (len(nbs) == nb_per_page)
    elif sort_by == 'random':
        nbs = Notebook.objects.order_by('?')[nb_per_page * i:nb_per_page * (i+1)]
        more_pages = (len(nbs) == nb_per_page)
    else:
        raise NotImplementedError

    context = {'nbs': nbs, 'next_page': int(obj_id)+1, 'more_pages' : more_pages, 'sort_by': sort_by}
    return render(request, 'web/page.html', context)


def submit(request):
    if request.method == 'POST':
        print('POST')
        # create a form instance and populate it with data from the request:
        form = NotebookForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            url = form.cleaned_data['URL']
            out = insert_notebook(url)
            t = Template("""<div class="thumbcenter thumbnail">
      <a href="/redirect/{{nb.id}}" target="_blank">
        <img width="295px" src="/{{nb.thumb_img}}" alt="{{nb.title}}"/>
      </a>
      <h4>{{nb.title}}</h4>
      <p>{{nb.description}}</p>
    </div>
    """)

            if out['status'] == 'success':
                nb = Notebook.objects.get(pk=out['pk'])
                html = "<h2>It worked!</h2><p>Your notebook is now online:</p>"
                c = Context({'nb': nb})
                html += t.render(c)
                html += '<h3>New Notebooks will appear immediate in the <a href="/sort/date/">new Notebooks section</a></h3>'
            elif out['reason'] == 'duplicate document':
                html = '<h2>This document is already in the collection</h2>'
                nb = Notebook.objects.get(pk=out['pk'])
                c = Context({'nb': nb})
                html += t.render(c)
            # redirect to a new URL:
            return HttpResponse(html)

    # if a GET (or any other method) we'll create a blank form
    else:
        form = NotebookForm()

    context = {'submit_active' : 'active', 'form': form}
    return render(request, 'web/submit.html', context)

def about(request):
    context = {'about_active' : 'active'}
    return render(request, 'web/about.html', context)

def thanks(request, obj_id):
    nb = Notebook.objects.get(pk=obj_id)
    context = {'nb' : nb}
    return render(request, 'web/thanks.html', context)


def nb_redirect(request, obj_id):

    # increment the current object by 1
    nb = Notebook.objects.get(pk=obj_id) # TODO: get or 404
    nb.hits_total += 1
    nb.save()
    ip = request.META['REMOTE_ADDR']
    h = Hit(model=nb, created=timezone.now(), ip=ip)
    h.save()
    # increment one view
    import nltk
    context = {'html' : nltk.clean_html(nb.full_html), 'redirect' : nb.html_url}
    return render(request, 'web/redirect.html', context)
    #return redirect(nb.html_url)
