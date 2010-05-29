First Pass
----------

* handle commits
  => test the post handler fo real
  => live updates using redis / long polling to push to the page

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