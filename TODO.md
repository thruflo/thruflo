
Simplify
--------

* refactoring:
  * go through and simplify the existing views
  * revise `_design`

* here's the flow (without any caching):
  f)  render dashboard => updates repos listing saved as `model.User.repos`
  g)  render repo => updates `model.Repo` inc. blobs listing for each branch
  h)  click through doc => checks commits and updates `model.Blob`s
* 'live' notifications go: 'get users for repo' w. stack cleared on page load


First Pass
----------

* handle commits
  + test the post handler fo real
  => live updates using redis / long polling to push to the page
    => there are two things:
      a. refreshing the blobs tree, *preserving current expand state*
      b. updating the content displayed for a blob
      
      so, when a page loads, it needs to register for updates
      a. against repo
        => handle add and remove data in the commit [we only live update against post recieve hook posts and they contain the paths that have been added or removed]
      b. against each blob
        => when a blob invalidates it's content, broadcast the fact & trigger a /blobs/get_blobs?keys=[...] call
    
    => with long polling, we need clients to connect, get any messages in a queue
       or wait for updates
       
       this can be done with bpop but it raises the qu: do you write to all these
       channels, e.g.: for all blobs?  or, presumably, can we push all messages
       down a single queue per session (account + session id)?
       

* document assembly UI
  => handle images & media
  => n.b.: atm get_data displays raw image data...

* generate
  => markdown validation
  => html
  => pdf

* provide templates
  => no doubt wrap the markdown with unobtrusive classes
  => paste in CSS


Second Pass
-----------

Edge case to resolve later: repos can be renamed; now, presumably this is discoverable using, e.g.: a matching list of commit ids.  so, e.g.: say a repo dissapears, ``handle_repo_gone()`` might re-get the repos for user from github, interrogate the description / commit history / blobs listing and either auto switch if a match is found or query the user.  

In the immediate term, we could just freeze renamed repos.

* users / accounts / repos
  * github oauth
  * cache session user in redis
  * handle repos dissapearing

* handle commits  
  => trigger the repo sanity check properly
  => handle branches dissapearing

* document assembly UI
  => handle blobs being removed
  => manage / reorder / drop in right place

* templates
  => some sort of css UI


Issues
------

http://code.google.com/p/gevent/issues/detail?id=25

``Currently we are limiting API calls to 60 per minute. This may change in the future, or possibly per user at some point, but if you try to access the API more than 60 times in a minute, it will start giving you "access denied" errors.``