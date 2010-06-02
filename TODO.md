First Pass
----------

* live updates
  a. against repo
    => handle add and remove data in the commit [we only live update against post recieve hook posts and they contain the paths that have been added or removed]
  b. against each blob
    => when a blob invalidates its content, broadcast the fact & trigger a /blobs/get_blobs?keys=[...] call

^^^ atm the impl relies on too much convention.  if we're going to clear a list of commits when a repo is requested, then we should have a `handle_get_repo` event handler that's triggered no matter how a user clients there way through.

equally, can we not usefully keep a record of when a user logs in?


* document assembly UI
  => handle images & media
  => n.b.: atm get_data displays raw image data...

* generate
  => markdown validation
  => html
  => pdf

* style
  => no doubt wrap the markdown with unobtrusive classes
  => select .css files in document UI


Second Pass
-----------

* caching
  * cache session user in redis
  => trigger the repo sanity check properly

* dissapearing
  * handle branches dissapearing
  * handle repos dissapearing:
    
    > Edge case to resolve later: repos can be renamed; now, presumably this is discoverable using, e.g.: a matching list of commit ids.  so, e.g.: say a repo dissapears, ``handle_repo_gone()`` might re-get the repos for user from github, interrogate the description / commit history / blobs listing and either auto switch if a match is found or query the user.  
    > In the immediate term, we could just freeze renamed repos.

* document assembly UI
  => delete
  => reorder / drop in right place
  => preview
