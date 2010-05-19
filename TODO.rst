Todo
----

+ enable the version control repository
  + register user's details
  + register one (or more) github repos
  + method to read the whole document tree
  + method to invalidate / refresh when git updates

* provide a document assembly UI
  + list the units
  => simple drag and drop and reorder
  => save the unit paths in order in a list attr on document
  => n.b.: atm get_data displays raw image data...

* handle commits
  => test the post handler fo real
  => in ``handle_commit`` (either via update hook, or against a commit list) we find all Blobs where ``latest commit`` matches a ``commit parent id``, set the ``latest commit`` to be the latest commit and clear the ``data``
  => when we handle a commit via the post hook, we store it against the repo
  => then, when we do the check, trigged by ..., we check these against the full commits list, fetching any we missed since we last sanity checked
  => github upate hook & merging: ***check the docs again*** - i.e.: what do you get in data after a merge?  how do you handle branches dissapearing?

* provide templates
  => no doubt wrap the markdown with unobtrusive classes
  => some sort of css UI (or just type for now?)

* generate
  => html
  => pdf


Issues
------

http://code.google.com/p/gevent/issues/detail?id=25

``Currently we are limiting API calls to 60 per minute. This may change in the future, or possibly per user at some point, but if you try to access the API more than 60 times in a minute, it will start giving you "access denied" errors.``