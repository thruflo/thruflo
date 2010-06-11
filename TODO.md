
* in order to develop, hardcode a testing user & account
* lose github and introduce local repos with dulwich wrapper
  * `git commit` is atomic across multiple files
  * `git push` is atomic per ref (i.e.: it's atomic)
  * it *seems* that [Dulwich][] provides the same atomicity as the git command line tools, as they all work by writing blob and tree by id and then writing commit referencing those (i.e.: there's no harm in writing objects and trees and then aborting)
  * clone a tmp repo per user (or session?)
  * commit to a user's clone and push to `--bare` master repo
  * n.b.: need to handle rejected pushes (i.e: can't merge)
* expose git daemon, git hooks
* what do we need to store / index / cache to support the UI / sectioning?
* how do we handle rebuilding from git in the event of server failure?
* document editing UI, bespin, section re-use handling
* template management
* views / selecting & publishing through stylesheets
* refactor user / access / subscription / pricing:
  * sign up and create an account
  * automatically subscribed to 30 day free trial for the account
  * pricing plan for an account, with points based on users, repos & data
  * admin users and general users
  * admin users can create new repos
  * admins can invite users to repos & manage who has access
  * when only one repo in an account, default to select it (encourage to minimise no. of repos -- most accounts should by fine with one)

[Dulwich]: http://github.com/jelmer/dulwich/blob/master/docs/tutorial/2-change-file.txt