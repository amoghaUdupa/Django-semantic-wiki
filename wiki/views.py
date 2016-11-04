from django.shortcuts import render
from django.http import Http404
from wiki.models import Page, PageOutlinks
from wikimarkup import parse
import mwparserfromhell
import string
import re

LINK_FROMAT = u'<a href="{path}">{linktext}</a>'
OUTLINK_TITLES = []

_re_linktext = re.compile(r'\[\[([a-zA-Z0-9 ()-.]+)\]\]')
_re_altlink = re.compile(r'\[\[([a-zA-Z0-9 ()-.]+)\|([a-zA-Z0-9 ()-.]+)\]\]')
_re_media = re.compile(r'\[\[([a-zA-Z0-9 -,.:<>=""/_|]+)\]\]')
_re_annotate = re.compile(r'\{\{([\'a-zA-Z0-9 -,.:<>=""/_|]+)\}\}')

def processlink(m):
    if "|" in m.group(0):
        linktext = m.group(2)
    else:
        linktext = m.group(1)
    matchtext = m.group(1)
    matchtext = matchtext.replace(" ","_")
    if matchtext not in OUTLINK_TITLES:
        return linktext
    path = "/wiki/" + matchtext
    return LINK_FROMAT.format(path = path,linktext = linktext)

def processmedia(text):
    mwcode = mwparserfromhell.parse(text)
    templates = mwcode.filter_templates()
    for template in templates:
        try:
            mwcode.remove(template)
        except ValueError as e:
            print "Unrenderable template"
    return mwcode

def getOutlinks(id):
    outlinks = PageOutlinks.objects.filter(id=id)
    for outLink in outlinks:
        OUTLINK_TITLES.append(Page.objects.get(id=outLink.outlinks).name)

def addlinks(id,text):
    getOutlinks(id)
    text = _re_linktext.sub(processlink, text) # direct links
    text = _re_altlink.sub(processlink, text) # links with
    # text = _re_media.sub(processmedia, text) # for File Wikitory and other wikimedia
    # text = processmedia(text) # infobox and related info
    OUTLINK_TITLES = []

    return text

# Create your views here.
def article(request, page_name):
    try:
        page = Page.objects.get(name=page_name)
    except Page.DoesNotExist as e:
        raise Http404("No such page exists")
    text = processmedia(page.text)
    text = addlinks(page.id, parse(text))
    context = {
    'name' : page.name.replace("_"," "),
    'text' : text,
    }
    return render(request,'wiki/article.html',context)

def home(request):
    context = {'title':"Home"}
    return render(request,'wiki/home.html',context)
