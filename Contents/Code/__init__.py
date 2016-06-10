# -*- coding: utf-8 -*-

# Copyright (c) 2014, KOL
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the <organization> nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTLICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from updater import Updater
Common = SharedCodeService.common


def Start():
    HTTP.CacheTime = CACHE_1HOUR


###############################################################################
# Video
###############################################################################

@handler(
    Common.PREFIX,
    L(Common.TITLE),
    None,
    R(Common.ICON)
)
def MainMenu():

    oc = ObjectContainer(
        title2=L(Common.TITLE),
        no_cache=True,
        content=ContainerContent.Genres
    )

    Updater(Common.PREFIX+'/update', oc)

    oc.add(DirectoryObject(
        key=Callback(Category, key='/popular/', title=L('Popular')),
        title=u'%s' % L('Popular'),
    ))
    oc.add(DirectoryObject(
        key=Callback(Category, key='/popular/hot/', title=L('Hot')),
        title=u'%s' % L('Hot'),
    ))
    oc.add(DirectoryObject(
        key=Callback(Category, key='/new/', title=L('New')),
        title=u'%s' % L('New'),
    ))

    if Prefs['username']:
        AddUser(oc, '/%s/' % Prefs['username'])
        oc.add(DirectoryObject(
            key=Callback(Discover, fmt='music', title=L('Discover Music Shows')),
            title=u'%s' % L('Discover Music Shows'),
        ))
    else:
        AddCategories(oc, 'music')

    oc.add(DirectoryObject(
        key=Callback(Discover, fmt='talk', title=L('Discover Talk Shows')),
        title=u'%s' % L('Discover Talk Shows'),
    ))

    oc.add(DirectoryObject(
        key=Callback(Discover, fmt=None, title=L('Users'), connection='users'),
        title=u'%s' % L('Users'),
    ))

    oc.add(InputDirectoryObject(
        key=Callback(
            Search
        ),
        title=u'%s' % L('Search'), prompt=u'%s' % L('Search cloudcasts'),
    ))

    return oc


@route(Common.PREFIX + '/category')
def Category(key, title, paging=False, **kwargs):

    params = None if paging else 'limit=%s' % Prefs['items_per_page']
    items = Common.ApiRequest(key, params)

    if not items:
        return ContentNotFound()

    oc = ObjectContainer(
        title2=u'%s' % title,
        replace_parent=paging,
        art=Common.GetArtBySlug(kwargs['slug']) if 'slug' in kwargs else None
    )

    for item in items['data']:
        oc.add(Common.GetTrackObject(item))

    return Pagination(oc, Category, items, title, **kwargs)


@route(Common.PREFIX + '/user')
def User(key):
    oc = AddUser(ObjectContainer(), key)
    return oc if len(oc) else ContentNotFound()


@route(Common.PREFIX + '/playlist')
def Playlist(key, title):
    return Category('%scloudcasts/' % key, title)


@route(Common.PREFIX + '/feed')
def Feed(key, title, paging=False):

    params = None if paging else 'limit=%s' % Prefs['items_per_page']
    items = Common.ApiRequest(key)

    if not items:
        return ContentNotFound()

    oc = ObjectContainer(
        title2=u'%s' % title,
        replace_parent=paging,
    )
    for item in items['data']:
        if 'cloudcasts' in item and len(item['cloudcasts']):
            for cloudcast in item['cloudcasts']:
                oc.add(Common.GetTrackObject(cloudcast))

    return Pagination(oc, Feed, items, title)


@route(Common.PREFIX + '/playlists')
def Playlists(key, title, paging=False):

    params = None if paging else 'limit=%s' % Prefs['items_per_page']
    items = Common.ApiRequest(key, params)

    if not items:
        return ContentNotFound()

    oc = ObjectContainer(
        title2=u'%s' % title,
        replace_parent=paging,
    )
    for item in items['data']:
        oc.add(DirectoryObject(
            key=Callback(Playlist, key=item['key'], title=item['name']),
            title=u'%s' % item['name'],
        ))

    return Pagination(oc, Playlists, items, title)


@route(Common.PREFIX + '/discover')
def Discover(title, fmt, connection='cloudcasts'):
    oc = ObjectContainer(title2=u'%s' % title)
    if connection == 'users':
        oc.add(InputDirectoryObject(
            key=Callback(
                Search,
                s_type='user',
                title=u'%s' % L('Search users')
            ),
            title=u'%s' % L('Search'), prompt=u'%s' % L('Search users'),
        ))

    AddCategories(oc, fmt, connection)
    return oc if len(oc) else ContentNotFound()


@route(Common.PREFIX + '/users')
def Users(key, title, paging=False):

    params = None if paging else 'limit=%s' % Prefs['items_per_page']
    items = Common.ApiRequest(key, params)

    if not items:
        return ContentNotFound()

    oc = ObjectContainer(
        title2=u'%s' % title,
        replace_parent=paging,
    )
    for item in items['data']:
        oc.add(GetUserObject(item))

    return Pagination(oc, Users, items, title)


def Search(query=None, title=L('Search'), s_type='cloudcast', **kwargs):

    if not query and not kwargs:
        return NoContents()

    if 'key' in kwargs:
        key = kwargs['key']
        params = None
        replace_parent=True
    else:
        key = '/search/'
        params = 'limit=%s&type=%s&q=%s' % (
            Prefs['items_per_page'],
            s_type,
            String.Quote(query, True)
        )
        replace_parent=False

    items = Common.ApiRequest(key, params)

    if not items:
        return ContentNotFound()

    oc = ObjectContainer(
        title2=u'%s' % title,
        replace_parent=replace_parent,
    )

    pcallback = GetUserObject if s_type == 'user' else Common.GetTrackObject

    for item in items['data']:
        oc.add(pcallback(item))

    return Pagination(oc, Search, items, title)


###############################################################################
# Common
###############################################################################

MC_CALLBACKS = {
    'users': Users,
    'cloudcasts': Category,
    'followers': Users,
    'favorites': Category,
    'following': Users,
    'cloudcasts': Category,
    'listens': Category,
    'feed': Feed,
    'playlists': Playlists,
}


def ContentNotFound():
    return MessageContainer(
        L('Error'),
        L('No entries found')
    )


def AddCategories(oc, fmt=None, connection='cloudcasts'):

    items = Common.ApiRequest('/categories/')

    if items and len(items['data']):
        for item in items['data']:
            if fmt is not None and item['format'] != fmt:
                continue

            oc.add(DirectoryObject(
                key=Callback(
                    MC_CALLBACKS[connection],
                    key='%s%s/' % (item['key'], connection),
                    title=item['name']
                ),
                title=u'%s' % item['name'],
            ))

    return oc


def AddUser(oc, key):
    user = Common.ApiRequest(key, 'metadata=1')

    if not user:
        return oc

    if not oc.title2:
        oc.title2=u'%s' % user['username']

    if 'cover_pictures' in user and 'large' in user['cover_pictures']:
        oc.art=user['cover_pictures']['large']

    for connection, key in user['metadata']['connections'].items():
        if connection in MC_CALLBACKS:
            title = L(connection)
            oc.add(DirectoryObject(
                key=Callback(MC_CALLBACKS[connection], key=key, title=title),
                title=u'%s' % title
            ))

    return oc


def GetUserObject(item):
    return DirectoryObject(
        key=Callback(User, key=item['key']),
        title=u'%s' % item['username'],
        thumb=item['pictures']['640wx640h']
    )


def Pagination(oc, pcallback, items, title, **kwargs):
    if 'paging' in items and 'next' in items['paging']:
        oc.add(NextPageObject(
                key=Callback(
                    pcallback,
                    key=items['paging']['next'],
                    title=title,
                    paging=True,
                    **kwargs
                ),
                title=u'%s' % L('More')
            ))

    return oc if len(oc) else ContentNotFound()
